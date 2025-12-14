"""Renee CLI.

Designed for both humans and AI agents:
- `--json` on commands where structured output is useful
- predictable exit codes (0 success, 1 error)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from renee import __version__
from renee.assets import AssetRegistry
from renee.errors import ReneeError
from renee.examples.grid_walk import run_client, run_local, run_server
from renee.impact import analyze_schema_impact
from renee.repl import run_repl
from renee.schema import SchemaRegistry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="renee")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output where applicable")
    parser.add_argument("--version", action="store_true", help="Print version and exit")

    sub = parser.add_subparsers(dest="cmd")

    schemas_p = sub.add_parser("schemas", help="Schema introspection")
    schemas_sub = schemas_p.add_subparsers(dest="schemas_cmd", required=True)
    schemas_list = schemas_sub.add_parser("list", help="List schemas in a file")
    schemas_list.add_argument("--path", required=True, help="Schema file (.yaml/.json/.toml)")
    schemas_list.add_argument("--kind", choices=["component", "event", "action"], help="Filter by kind")

    schemas_show = schemas_sub.add_parser("show", help="Show a schema")
    schemas_show.add_argument("--path", required=True, help="Schema file (.yaml/.json/.toml)")
    schemas_show.add_argument("--kind", required=True, choices=["component", "event", "action"])
    schemas_show.add_argument("--name", required=True, help="Schema name")

    assets_p = sub.add_parser("assets", help="Asset management")
    assets_sub = assets_p.add_subparsers(dest="assets_cmd", required=True)
    assets_scan = assets_sub.add_parser("scan", help="Scan assets directory")
    assets_scan.add_argument("--root", required=True, help="Assets root directory")
    assets_scan.add_argument("--manifest", default="assets/manifest.json", help="Output manifest path")
    assets_scan.add_argument("--constants", default="assets/constants.py", help="Output constants module path")

    demo_p = sub.add_parser("demo", help="Run the built-in grid-walk demo")
    demo_sub = demo_p.add_subparsers(dest="demo_cmd", required=True)
    demo_local = demo_sub.add_parser("local", help="Run demo locally")
    demo_local.add_argument("--renderer", choices=["terminal", "pygame", "headless"], default="terminal")

    demo_server = demo_sub.add_parser("server", help="Run demo server")
    demo_server.add_argument("--host", default="127.0.0.1")
    demo_server.add_argument("--port", type=int, default=8765)

    demo_client = demo_sub.add_parser("client", help="Run demo client")
    demo_client.add_argument("--host", default="127.0.0.1")
    demo_client.add_argument("--port", type=int, default=8765)
    demo_client.add_argument("--renderer", choices=["terminal", "pygame"], default="terminal")

    impact_p = sub.add_parser("impact", help="Impact analysis utilities")
    impact_sub = impact_p.add_subparsers(dest="impact_cmd", required=True)
    impact_schema = impact_sub.add_parser("schema", help="Analyze schema references")
    impact_schema.add_argument("--path", required=True, help="Schema file (.yaml/.json/.toml)")
    impact_schema.add_argument("--kind", required=True, choices=["component", "event", "action"])
    impact_schema.add_argument("--name", required=True, help="Schema name")

    repl_p = sub.add_parser("repl", help="Interactive REPL")
    repl_sub = repl_p.add_subparsers(dest="repl_cmd", required=True)
    repl_demo = repl_sub.add_parser("demo", help="REPL for the built-in demo")

    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    try:
        if args.cmd == "schemas":
            return _cmd_schemas(args, json_mode=bool(args.json))
        if args.cmd == "assets":
            return _cmd_assets(args, json_mode=bool(args.json))
        if args.cmd == "demo":
            return _cmd_demo(args)
        if args.cmd == "impact":
            return _cmd_impact(args, json_mode=bool(args.json))
        if args.cmd == "repl":
            return _cmd_repl(args, json_mode=bool(args.json))
    except ReneeError as e:
        if args.json:
            print(json.dumps({"ok": False, "error": e.to_dict()}, indent=2, sort_keys=True))
        else:
            print(f"Error: {e.payload.message}", file=sys.stderr)
            if e.payload.hint:
                print(f"Hint: {e.payload.hint}", file=sys.stderr)
        return 1

    parser.print_help()
    return 0


def _cmd_schemas(args: Any, *, json_mode: bool) -> int:
    reg = SchemaRegistry()
    reg.load_from_path(args.path)
    if args.schemas_cmd == "list":
        kind = args.kind
        data = {
            "ok": True,
            "schemas": reg.list(kind=kind) if kind else reg.list(),
        }
        _emit(data, json_mode=json_mode)
        return 0
    if args.schemas_cmd == "show":
        data = {"ok": True, "schema": reg.as_json(args.name, kind=args.kind)}
        _emit(data, json_mode=json_mode)
        return 0
    return 1


def _cmd_assets(args: Any, *, json_mode: bool) -> int:
    if args.assets_cmd != "scan":
        return 1
    reg = AssetRegistry.scan(args.root)
    reg.write_manifest(args.manifest)
    reg.generate_constants(args.constants)
    _emit(
        {
            "ok": True,
            "manifest": str(args.manifest),
            "constants": str(args.constants),
            "counts": {k: len(v) for k, v in reg.manifest.items()},
        },
        json_mode=json_mode,
    )
    return 0


def _cmd_demo(args: Any) -> int:
    if args.demo_cmd == "local":
        run_local(renderer=args.renderer)
        return 0
    if args.demo_cmd == "server":
        run_server(host=args.host, port=args.port)
        return 0
    if args.demo_cmd == "client":
        run_client(host=args.host, port=args.port, renderer=args.renderer)
        return 0
    return 1


def _cmd_impact(args: Any, *, json_mode: bool) -> int:
    if args.impact_cmd != "schema":
        return 1
    reg = SchemaRegistry()
    reg.load_from_path(args.path)
    report = analyze_schema_impact(reg, kind=args.kind, name=args.name)
    _emit(
        {
            "ok": True,
            "impact": {
                "kind": report.kind,
                "name": report.name,
                "referenced_by": report.referenced_by,
            },
        },
        json_mode=json_mode,
    )
    return 0


def _cmd_repl(args: Any, *, json_mode: bool) -> int:
    if args.repl_cmd != "demo":
        return 1
    from renee.examples.grid_walk import build_demo

    pipeline, _schemas = build_demo()
    run_repl(pipeline=pipeline, json_mode=json_mode)
    return 0


def _emit(data: dict[str, Any], *, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    # Human-readable fallback.
    if "schema" in data:
        print(json.dumps(data["schema"], indent=2, sort_keys=True))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
