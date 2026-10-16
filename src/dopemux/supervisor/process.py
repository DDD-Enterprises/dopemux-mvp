"""Bounded real argv execution for trusted local commands, not an OS sandbox."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import signal
import time
from pathlib import Path

from .kernel import Result
from .mandates import safe_relative
from .transport import directory, exclusive


def snapshot(root):
    """Bounded monitored project view; hidden/cache/vendor paths are excluded."""
    result, total = {}, 0
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d not in {"node_modules", "venv", "env", "__pycache__"}
        ]
        for filename in files:
            if filename.startswith("."):
                continue
            path = Path(current) / filename
            if path.is_symlink() or path.stat().st_nlink != 1:
                raise ValueError("Unqualified linked project file")
            total += path.stat().st_size
            if len(result) >= 50000 or total > 268435456:
                raise ValueError("Project inspection ceiling exceeded")
            result[str(path.relative_to(root))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return result


class LocalProcessRunner:
    def __init__(self, plans, evidence_root, verify_snapshot=None, save_snapshot=None):
        self.plans = plans
        self.evidence_root = directory(evidence_root)
        self.verify_snapshot = verify_snapshot
        self.save_snapshot = save_snapshot

    async def __call__(self, dispatch):
        mandate_id, step_id = dispatch.work.work_id.split(":", 1)
        plan = self.plans[mandate_id]
        step = next(s for s in plan["steps"] if s["step_id"] == step_id)
        root = Path(plan["project_root"])
        for path in step["write_paths"]:
            safe_relative(root, path)
        before = snapshot(root)
        if self.verify_snapshot is not None:
            self.verify_snapshot(mandate_id, before)
        run_root = directory(self.evidence_root / dispatch.attempt_id)
        home = directory(run_root / "home")
        tmp = directory(run_root / "tmp")
        stdout, stderr = run_root / "stdout.log", run_root / "stderr.log"
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(home),
            "TMPDIR": str(tmp),
            "XDG_CACHE_HOME": str(directory(run_root / "cache")),
            "XDG_CONFIG_HOME": str(home),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHON_DOTENV_DISABLED": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "LANG": "C",
            "LC_ALL": "C",
            "TZ": "UTC",
            "TERM": "dumb",
            "NO_COLOR": "1",
        }
        proc, reason, complete, pumps = None, None, True, []
        counts = {"stdout": 0, "stderr": 0}
        cap = step.get("capture_bytes", 131072)
        t0 = time.monotonic()
        handles = {}

        async def pump(label, stream):
            nonlocal reason, complete
            while True:
                chunk = await stream.read(8192)
                if not chunk:
                    return
                left = max(0, cap - sum(counts.values()))
                counts[label] += len(chunk)
                handles[label].write(chunk[:left])
                if len(chunk) > left:
                    complete = False
                    reason = "CAPTURE_CAP"
                    return

        async def cleanup():
            if proc is None:
                return
            for sig, wait in (
                (signal.SIGTERM, max(0.01, dispatch.timeout_seconds * 0.04)),
                (signal.SIGKILL, max(0.01, dispatch.timeout_seconds * 0.04)),
            ):
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    await asyncio.wait_for(proc.wait(), wait)
                    # Leader exit alone does not prove descendants are gone.
                    try:
                        os.killpg(proc.pid, 0)
                    except ProcessLookupError:
                        break
                except asyncio.TimeoutError:
                    pass

        try:
            handles = {k: (run_root / (k + ".log")).open("xb") for k in counts}
            proc = await asyncio.create_subprocess_exec(
                *step["argv"],
                cwd=root,
                env=env,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            exclusive(
                run_root / "START_ACK.json",
                {"pid": proc.pid, "pgid": proc.pid, "attempt_id": dispatch.attempt_id},
            )
            pumps = [
                asyncio.create_task(pump("stdout", proc.stdout)),
                asyncio.create_task(pump("stderr", proc.stderr)),
            ]
            # Keep native cleanup inside the kernel's enclosing active/wall reservation.
            deadline = t0 + max(0.01, dispatch.timeout_seconds * 0.8)
            while proc.returncode is None:
                if time.monotonic() >= deadline:
                    reason = "TIMEOUT"
                if reason:
                    await cleanup()
                    break
                await asyncio.sleep(min(0.01, max(0.001, deadline - time.monotonic())))
            try:
                await asyncio.wait_for(
                    asyncio.gather(*pumps), max(0.05, dispatch.timeout_seconds * 0.1)
                )
            except asyncio.TimeoutError:
                reason, complete = "CAPTURE_DRAIN_UNCONFIRMED", False
                await cleanup()
                for task in pumps:
                    task.cancel()
                await asyncio.gather(*pumps, return_exceptions=True)
        except asyncio.CancelledError:
            reason = "COORDINATOR_CANCELLED"
            await cleanup()
        except Exception as exc:
            reason = "RUNNER_" + type(exc).__name__
            await cleanup()
        finally:
            for task in pumps:
                if not task.done():
                    task.cancel()
            if pumps:
                await asyncio.gather(*pumps, return_exceptions=True)
            for handle in handles.values():
                handle.flush()
                os.fsync(handle.fileno())
                handle.close()
        closed = proc is None
        if proc:
            try:
                os.killpg(proc.pid, 0)
                closed = False
            except ProcessLookupError:
                closed = True
            if not closed:
                reason = reason or "PROCESS_GROUP_UNCLOSED"
        try:
            after = snapshot(root)
            changed = sorted(
                k for k in set(before) | set(after) if before.get(k) != after.get(k)
            )
            if set(changed) - set(step["write_paths"]):
                reason = reason or "WRITE_SCOPE_DRIFT"
        except Exception:
            changed = []
            reason = reason or "WRITE_SCOPE_UNCONFIRMED"
        record = dict(
            attempt_id=dispatch.attempt_id,
            work_id=dispatch.work.work_id,
            native_exit=proc.returncode if proc else None,
            owned_group_absent=closed,
            capture_complete=complete,
            capture_bytes=counts,
            elapsed_seconds=time.monotonic() - t0,
            changed_paths=changed,
            stop_reason=reason,
            before_fingerprint=hashlib.sha256(
                json.dumps(before, sort_keys=True).encode()
            ).hexdigest(),
            after_fingerprint=(
                hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest()
                if "after" in locals()
                else None
            ),
            containment="TRUSTED_LOCAL_COMMAND; project writes monitored, not OS-enforced",
            model_calls=0,
        )
        native = run_root / "PROCESS_RESULT.json"
        exclusive(native, record)
        status = (
            "EFFECT_UNKNOWN"
            if reason or not closed
            else ("SUCCEEDED" if proc and proc.returncode == 0 else "FAILED")
        )
        if status != "EFFECT_UNKNOWN" and self.save_snapshot is not None:
            self.save_snapshot(mandate_id, after)
        return Result(
            status,
            (str(stdout), str(stderr), str(native)),
            0 if proc is None or closed else None,
        )
