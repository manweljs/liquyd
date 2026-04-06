# main.py
from __future__ import annotations

import argparse
import importlib.util
import pprint
import tomllib
from pathlib import Path
from typing import Any


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


def _load_python_file_module(module_file_path: Path):
    if not module_file_path.exists():
        raise FileNotFoundError(
            f"Python config file was not found at '{module_file_path}'."
        )

    module_name = f"_liquyd_config_{module_file_path.stem}"
    module_spec = importlib.util.spec_from_file_location(module_name, module_file_path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError(f"Could not create a module spec for '{module_file_path}'.")

    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def _load_liquyd_config_object(config_reference: str) -> Any:
    module_path_text, separator, attribute_name = config_reference.rpartition(".")
    if separator == "":
        raise ValueError(
            "Key 'migration.liquyd_config' must be in the format "
            "'relative_file.py.ATTRIBUTE'."
        )

    module_file_path = Path.cwd() / module_path_text.replace(".", "/")
    if module_file_path.suffix != ".py":
        module_file_path = module_file_path.with_suffix(".py")

    module = _load_python_file_module(module_file_path)

    try:
        return getattr(module, attribute_name)
    except AttributeError as error:
        raise AttributeError(
            f"Attribute '{attribute_name}' was not found in file "
            f"'{module_file_path}'."
        ) from error


def _run_makemigrations() -> int:
    config = _load_liquyd_toml()
    migration_settings = _get_migration_settings(config)

    migrations_dir = migration_settings.get("migrations_dir")
    if not migrations_dir:
        raise ValueError("Key 'migration.migrations_dir' is required in liquyd.toml.")

    liquyd_config_path = migration_settings.get("liquyd_config")
    if not liquyd_config_path:
        raise ValueError("Key 'migration.liquyd_config' is required in liquyd.toml.")

    liquyd_config = _load_liquyd_config_object(liquyd_config_path)

    migrations_path = Path(migrations_dir)
    if not migrations_path.is_absolute():
        migrations_path = Path.cwd() / migrations_path

    migrations_path.mkdir(parents=True, exist_ok=True)

    print("Liquyd TOML config:")
    pprint.pprint(config)
    print()

    print("Liquyd loaded config:")
    pprint.pprint(liquyd_config)
    print()

    print(f"Migrations directory ready: {migrations_path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="liquyd")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("makemigrations")
    subparsers.add_parser("migrate")
    subparsers.add_parser("validate")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "makemigrations":
        return _run_makemigrations()

    if args.command == "migrate":
        print("migrate is not implemented yet.")
        return 0

    if args.command == "validate":
        print("validate is not implemented yet.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
