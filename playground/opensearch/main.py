# cli/main.py
from __future__ import annotations

import argparse
import pprint
from pathlib import Path
from typing import Any
import tomllib


def _load_liquyd_toml(base_directory: Path | None = None) -> dict[str, Any]:
    root_directory = base_directory or Path.cwd()
    config_path = root_directory / "liquyd.toml"

    if not config_path.exists():
        raise FileNotFoundError(f"liquyd.toml was not found at '{config_path}'.")

    with config_path.open("rb") as file:
        return tomllib.load(file)


def _get_migration_settings(config: dict[str, Any]) -> dict[str, Any]:
    migration_settings = config.get("migration")
    if not isinstance(migration_settings, dict):
        raise ValueError("Section [migration] is required in liquyd.toml.")

    return migration_settings


def _run_makemigrations() -> int:
    config = _load_liquyd_toml()
    migration_settings = _get_migration_settings(config)

    migrations_dir = migration_settings.get("migrations_dir")
    if not migrations_dir:
        raise ValueError("Key 'migration.migrations_dir' is required in liquyd.toml.")

    migrations_path = Path(migrations_dir)
    if not migrations_path.is_absolute():
        migrations_path = Path.cwd() / migrations_path

    migrations_path.mkdir(parents=True, exist_ok=True)

    print("Liquyd config:")
    pprint.pprint(config)
    print("")
    print(f"Migrations directory ready: {migrations_path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="liquyd")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("makemigrations")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "makemigrations":
        return _run_makemigrations()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
