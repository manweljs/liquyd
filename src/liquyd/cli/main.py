# src/liquyd/cli/main.py
from __future__ import annotations

import argparse
import importlib.util
import tomllib
from pathlib import Path
from typing import Any

from liquyd.cli.commands.makemigrations import makemigrations


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


def _resolve_config_module_file_path(config_reference: str) -> tuple[Path, str]:
    module_path_text, separator, attribute_name = config_reference.rpartition(".")
    if separator == "":
        raise ValueError(
            "Key 'migration.liquyd_config' must be in the format "
            "'relative_file.py.ATTRIBUTE'."
        )

    module_file_path = Path.cwd() / module_path_text.replace(".", "/")
    if module_file_path.suffix != ".py":
        module_file_path = module_file_path.with_suffix(".py")

    return module_file_path, attribute_name


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
    module_file_path, attribute_name = _resolve_config_module_file_path(
        config_reference
    )
    module = _load_python_file_module(module_file_path)

    try:
        return getattr(module, attribute_name)
    except AttributeError as error:
        raise AttributeError(
            f"Attribute '{attribute_name}' was not found in file "
            f"'{module_file_path}'."
        ) from error


def _collect_document_module_paths(liquyd_config: Any) -> list[str]:
    if not isinstance(liquyd_config, dict):
        raise ValueError("LIQUYD_CONFIG must be a dictionary.")

    document_module_paths: list[str] = []

    for client_settings in liquyd_config.values():
        if not isinstance(client_settings, dict):
            continue

        documents = client_settings.get("documents")
        if documents is None:
            continue

        if not isinstance(documents, list):
            raise ValueError("Key 'documents' must be a list of module paths.")

        for document_module_path in documents:
            if not isinstance(document_module_path, str):
                raise ValueError(
                    "Each item in 'documents' must be a string module path."
                )

            normalized_document_module_path = document_module_path.strip()
            if not normalized_document_module_path:
                continue

            if normalized_document_module_path not in document_module_paths:
                document_module_paths.append(normalized_document_module_path)

    return document_module_paths


def _resolve_document_module_file_path(
    config_file_path: Path,
    document_module_path: str,
) -> Path:
    relative_module_path = Path(*document_module_path.split("."))

    search_directories = [config_file_path.parent, *config_file_path.parent.parents]

    for search_directory in search_directories:
        module_file_path = search_directory / relative_module_path.with_suffix(".py")
        if module_file_path.exists():
            return module_file_path

        package_file_path = search_directory / relative_module_path / "__init__.py"
        if package_file_path.exists():
            return package_file_path

        if search_directory == Path.cwd():
            break

    raise FileNotFoundError(
        f"Document module '{document_module_path}' could not be resolved from "
        f"config file '{config_file_path}'."
    )


def _import_document_modules(
    liquyd_config: Any,
    config_file_path: Path,
) -> list[Path]:
    imported_module_paths: list[Path] = []

    for document_module_path in _collect_document_module_paths(liquyd_config):
        module_file_path = _resolve_document_module_file_path(
            config_file_path=config_file_path,
            document_module_path=document_module_path,
        )
        _load_python_file_module(module_file_path)
        imported_module_paths.append(module_file_path)

    return imported_module_paths


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
    config_file_path, _ = _resolve_config_module_file_path(liquyd_config_path)

    imported_module_paths = _import_document_modules(
        liquyd_config=liquyd_config,
        config_file_path=config_file_path,
    )

    if imported_module_paths:
        print("Imported document modules:")
        for imported_module_path in imported_module_paths:
            print(f"  - {imported_module_path}")
    else:
        print("Imported document modules:")
        print("  - <none>")

    migrations_path = Path(migrations_dir)
    if not migrations_path.is_absolute():
        migrations_path = Path.cwd() / migrations_path

    migrations_path.mkdir(parents=True, exist_ok=True)

    migration_file_path = makemigrations(base_directory=migrations_path)

    if migration_file_path is None:
        print("No changes detected.")
        return 0

    print(f"Migration created: {migration_file_path}")
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
