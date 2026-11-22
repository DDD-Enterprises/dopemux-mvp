"""Private local delivery records; neither native acceptance nor Master ACK."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid

from .mandates import canonical


class ReturnConflict(ValueError):
    """An immutable event or local delivery record changed identity."""


def directory(path):
    path = Path(path).absolute()
    for p in (path, *path.parents):
        if p.is_symlink():
            raise ValueError("Transport/state symlink ancestry is forbidden")
    if not path.exists():
        if not path.parent.exists():
            directory(path.parent)
        path.mkdir(mode=0o700, exist_ok=True)
    st = path.stat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ValueError("Transport/state directory must be private current-user custody")
    return path


@contextmanager
def publication_lock(parent, *, writing=False):
    path = parent / ".publication.lock"
    flags = os.O_RDWR | os.O_NOFOLLOW
    if writing:
        flags |= os.O_CREAT
    try:
        fd = os.open(path, flags, 0o600)
    except FileNotFoundError:
        if writing:
            raise
        yield
        return
    try:
        st = os.fstat(fd)
        if (
            not stat.S_ISREG(st.st_mode)
            or st.st_nlink != 1
            or st.st_uid != os.getuid()
            or st.st_mode & 0o077
        ):
            raise ValueError("Invalid private publication lock")
        fcntl.flock(fd, fcntl.LOCK_EX if writing else fcntl.LOCK_SH)
        yield
    finally:
        os.close(fd)


def _read_bytes(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size > limit:
            raise ValueError("Expected bounded ordinary JSON file")
        chunks, size = [], 0
        while size <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
            size += len(chunk)
        raise ValueError("JSON file grew beyond limit")
    finally:
        os.close(fd)


def read_json(path, limit=32768):
    path = Path(path)
    with publication_lock(path.parent):
        raw = _read_bytes(path, limit)

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("Nonfinite JSON value")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def immutable_bytes(path, limit):
    try:
        return _read_bytes(path, limit)
    except ValueError as exc:
        raise ReturnConflict("Invalid immutable local publication inode/size") from exc


def exclusive(path, payload):
    path = Path(path)
    directory(path.parent)
    data = canonical(payload)
    with publication_lock(path.parent, writing=True):
        if path.exists() or path.is_symlink():
            if immutable_bytes(path, max(len(data), 32768)) != data:
                raise ReturnConflict("Immutable local return/delivery record conflict")
            return False
        temporary = path.parent / (".pending-" + uuid.uuid4().hex)
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError:
                if immutable_bytes(path, max(len(data), 32768)) != data:
                    raise ReturnConflict("Concurrent immutable local return conflict")
                return False
        finally:
            temporary.unlink(missing_ok=True)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return True


def name(key):
    return hashlib.sha256(key.encode()).hexdigest() + ".json"


def validate_event(event):
    if not isinstance(event, dict) or set(event) != {"key", "digest", "payload"}:
        raise ReturnConflict("Invalid return envelope")
    if (
        not isinstance(event["key"], str)
        or not isinstance(event["payload"], dict)
        or event["payload"].get("key") != event["key"]
        or event["digest"] != hashlib.sha256(canonical(event["payload"])).hexdigest()
    ):
        raise ReturnConflict("Return identity/digest mismatch")


def local_record(event, receiver_ref):
    return dict(
        kind="LOCAL_DELIVERY_RECORD",
        key=event["key"],
        digest=event["digest"],
        receiver_ref=receiver_ref,
        recorded_by_uid=os.getuid(),
        native_acceptance="NOT_ASSERTED",
        master_ack="NOT_ASSERTED",
    )


class ReturnPublisher:
    def __init__(self, root, receiver_ref):
        self.root = directory(root)
        self.events = directory(self.root / "events")
        self.records = directory(self.root / "records")
        self.receiver_ref = receiver_ref

    async def __call__(self, event):
        validate_event(event)
        filename = name(event["key"])
        exclusive(self.events / filename, event)
        path = self.records / filename
        if not path.exists():
            return None
        try:
            record = read_json(path)
        except ValueError as exc:
            raise ReturnConflict("Malformed local delivery record") from exc
        if record != local_record(event, self.receiver_ref):
            raise ReturnConflict("Local delivery record differs from event/current UID")
        return event["digest"]


class LocalDeliveryRecorder:
    """Current local UID records receipt; same-account code remains inside trust boundary."""

    def __init__(self, root, receiver_ref):
        self.root = directory(root)
        self.events = directory(self.root / "events")
        self.records = directory(self.root / "records")
        self.receiver_ref = receiver_ref

    def receive(self, limit=100):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Bounded receive batch required")
        count = 0
        paths = sorted(self.events.glob("*.json"))
        if len(paths) > 10000:
            raise ValueError("Local return queue capacity exceeded")
        for path in paths:
            event = read_json(path)
            validate_event(event)
            if path.name != name(event["key"]):
                raise ReturnConflict("Return filename/identity mismatch")
            count += exclusive(self.records / path.name, local_record(event, self.receiver_ref))
            if count >= limit:
                break
        return count


# Compatibility spelling only: this class has local delivery semantics.
ReturnReceiver = LocalDeliveryRecorder
