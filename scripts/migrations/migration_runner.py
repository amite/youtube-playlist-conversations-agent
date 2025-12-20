"""Core migration runner for SQLite database schema evolution."""

import importlib.util
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple


def get_current_version(db_path: Path) -> int:
    """Get the current schema version from the database.

    Returns 0 if schema_version table doesn't exist (unversioned database).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(version) FROM schema_version"
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] is not None else 0
    except sqlite3.OperationalError:
        # schema_version table doesn't exist
        return 0


def init_version_table(conn: sqlite3.Connection) -> None:
    """Create the schema_version tracking table."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def mark_version(conn: sqlite3.Connection, version: int) -> None:
    """Mark a migration version as applied."""
    init_version_table(conn)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (version, datetime.now().isoformat())
    )
    conn.commit()


def get_migration_versions() -> list[int]:
    """Get list of all available migration versions in order."""
    versions_dir = Path(__file__).parent / "versions"
    migration_files = sorted(versions_dir.glob("[0-9]*_*.py"))

    versions = []
    for file in migration_files:
        # Extract version number from filename (e.g., "001_initial_schema.py" -> 1)
        version_str = file.stem.split("_")[0]
        try:
            versions.append(int(version_str))
        except ValueError:
            continue

    return versions


def load_migration(version: int) -> Tuple[callable, callable]:
    """Load upgrade and downgrade functions from migration file.

    Returns: (upgrade_func, downgrade_func)
    """
    versions_dir = Path(__file__).parent / "versions"
    migration_files = sorted(versions_dir.glob("[0-9]*_*.py"))

    # Find the migration file for this version
    target_file = None
    for file in migration_files:
        version_str = file.stem.split("_")[0]
        if int(version_str) == version:
            target_file = file
            break

    if not target_file:
        raise ValueError(f"Migration {version:03d} not found")

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(target_file.stem, target_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "upgrade") or not hasattr(module, "downgrade"):
        raise ValueError(
            f"Migration {version:03d} must define upgrade() and downgrade() functions"
        )

    return module.upgrade, module.downgrade


def run_upgrade(db_path: Path, target_version: int | None = None) -> None:
    """Apply migrations up to target_version (or latest if not specified)."""
    conn = sqlite3.connect(db_path)

    try:
        current_version = get_current_version(db_path)
        available_versions = get_migration_versions()

        if target_version is None:
            target_version = available_versions[-1] if available_versions else 0

        if current_version == target_version:
            print(f"✓ Already at version {current_version}")
            return

        if current_version > target_version:
            print(f"✗ Current version {current_version} > target {target_version}")
            print("  Use downgrade to go to earlier versions")
            return

        # Apply migrations in order
        for version in available_versions:
            if version > current_version and version <= target_version:
                print(f"→ Applying migration {version:03d}...", end=" ")
                try:
                    upgrade_func, _ = load_migration(version)
                    upgrade_func(conn)
                    mark_version(conn, version)
                    print("✓")
                except Exception as e:
                    conn.rollback()
                    print(f"✗\n  Error: {e}")
                    raise

        print(f"✓ Successfully upgraded to version {target_version}")

    finally:
        conn.close()


def run_downgrade(db_path: Path, steps: int = 1) -> None:
    """Rollback the specified number of migrations."""
    conn = sqlite3.connect(db_path)

    try:
        current_version = get_current_version(db_path)
        available_versions = sorted(get_migration_versions())

        if current_version == 0:
            print("✗ Database is not versioned, cannot downgrade")
            return

        # Find the migration to downgrade to
        rollback_from = current_version
        rollback_count = 0

        for i in range(len(available_versions) - 1, -1, -1):
            if available_versions[i] >= rollback_from:
                continue

            if rollback_count >= steps:
                break

            version = available_versions[i]
            print(f"→ Rolling back migration {rollback_from:03d}...", end=" ")

            try:
                _, downgrade_func = load_migration(rollback_from)
                downgrade_func(conn)

                # Remove version record
                cursor = conn.cursor()
                cursor.execute("DELETE FROM schema_version WHERE version = ?", (rollback_from,))
                conn.commit()

                print("✓")
                rollback_from = version
                rollback_count += 1
            except Exception as e:
                conn.rollback()
                print(f"✗\n  Error: {e}")
                raise

        print(f"✓ Successfully downgraded {rollback_count} migration(s)")

    finally:
        conn.close()


def print_status(db_path: Path) -> None:
    """Print current migration status."""
    current_version = get_current_version(db_path)
    available_versions = get_migration_versions()

    print(f"Current version: {current_version}")
    print(f"Available migrations: {len(available_versions)}")

    if available_versions:
        latest_version = available_versions[-1]
        print(f"Latest version: {latest_version}")

        if current_version < latest_version:
            pending = [v for v in available_versions if v > current_version]
            print(f"Pending migrations: {len(pending)}")
            for v in pending:
                print(f"  - {v:03d}")
        else:
            print("✓ All migrations applied")
    else:
        print("✗ No migrations found")
