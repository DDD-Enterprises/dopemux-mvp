# Command log

run_id=20260710T041715Z
live=False

## dopmux_git_status

```
$ git status --short --branch
exit_code=0
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## dnh_git_status

```
$ git status --short --branch
exit_code=0
cwd=/Users/hue/code/dNh_CRM
```

## docker_ps_before

```
$ docker ps --format {{.Names}}	{{.Ports}}	{{.Labels}}
exit_code=0
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## mcp_commands_list

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -c from dopemux.commands.mcp_commands import mcp; print(sorted(mcp.commands.keys()))
exit_code=0
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## doctor_before

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m dopemux.cli mcp doctor --repo /Users/hue/code/dNh_CRM --json
exit_code=1
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## repair_dry_run

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m dopemux.cli mcp repair-config --repo /Users/hue/code/dNh_CRM --dry-run --json
exit_code=0
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## start_dry_run

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m dopemux.cli mcp start --repo /Users/hue/code/dNh_CRM --dry-run --json
exit_code=1
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## status_after

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m dopemux.cli mcp status --repo /Users/hue/code/dNh_CRM --json
exit_code=0
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## doctor_after

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m dopemux.cli mcp doctor --repo /Users/hue/code/dNh_CRM --json
exit_code=1
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## docker_ps_after

```
$ docker ps --format {{.Names}}	{{.Ports}}	{{.Labels}}
exit_code=0
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```

## fleet_doctor

```
$ /Users/hue/.local/share/mise/installs/python/3.12.13/bin/python -m dopemux.cli mcp fleet doctor --repo /Users/hue/code/dNh_CRM --worktrees /Users/hue/code/dNh_CRM --json
exit_code=1
cwd=/Users/hue/code/dopemux-mcp-runtime-006r
```
