import json

from dopemux.system_data.tools import (
    ToolRunner,
    parse_duf_json,
    parse_dust_json,
    parse_gdu_text,
    parse_procs_json,
)


def test_required_tool_preflight_reports_missing(monkeypatch):
    monkeypatch.setattr("dopemux.system_data.tools.shutil.which", lambda name: None)

    report = ToolRunner().check_required_tools()

    assert not report.ok
    assert set(report.missing) == {"dust", "duf", "btop", "procs", "gdu", "dua", "ncdu"}
    assert "brew install dust duf btop procs gdu dua-cli ncdu" in report.install_command


def test_parse_duf_json_volumes():
    volumes = parse_duf_json(
        json.dumps(
            [
                {
                    "mount_point": "/",
                    "device": "/dev/disk1",
                    "fs_type": "apfs",
                    "device_type": "local",
                    "total": 100,
                    "used": 80,
                    "free": 20,
                }
            ]
        )
    )

    assert volumes[0].mount_point == "/"
    assert volumes[0].free_bytes == 20


def test_parse_dust_json_tree():
    records = parse_dust_json(
        '{"size":"4.0K","name":"/tmp/root","children":[{"size":"2.0K","name":"/tmp/root/a","children":[]}]}'
    )

    by_path = {record.path: record.data["size_bytes"] for record in records}
    assert by_path["/tmp/root"] == 4096
    assert by_path["/tmp/root/a"] == 2048


def test_parse_gdu_text_bytes():
    records = parse_gdu_text("1024\t/tmp/a\n2048 /tmp/b\n")

    assert [record.path for record in records] == ["/tmp/a", "/tmp/b"]
    assert records[1].data["size_bytes"] == 2048


def test_parse_procs_json():
    rows = parse_procs_json('[{"PID": 123, "Command": "Docker"}]')

    assert rows == ({"PID": 123, "Command": "Docker"},)
