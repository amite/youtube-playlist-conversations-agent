#!/usr/bin/env python3
"""CLI for managing database migrations."""

import sys
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from migrations.migration_runner import (
    run_upgrade,
    run_downgrade,
    print_status,
    get_migration_versions,
)


def create_migration(name: str) -> None:
    """Create a new migration file template."""
    versions = get_migration_versions()
    next_version = (max(versions) if versions else 0) + 1

    # Normalize name: lowercase, replace spaces with underscores
    name = name.lower().replace(" ", "_")
    # Remove any non-alphanumeric characters except underscores
    name = re.sub(r"[^a-z0-9_]", "", name)

    if not name:
        print("✗ Invalid migration name")
        return

    filename = f"{next_version:03d}_{name}.py"
    filepath = Path(__file__).parent / "migrations" / "versions" / filename

    if filepath.exists():
        print(f"✗ Migration file already exists: {filename}")
        return

    template = f'''"""
Migration {next_version:03d}: {name.replace('_', ' ').title()}

Created: {Path(__file__).read_text()[:0]}
"""


def upgrade(conn):
    """Apply migration."""
    cursor = conn.cursor()
    # TODO: Add your migration SQL here
    # cursor.execute("""
    #     CREATE TABLE new_table (
    #         id INTEGER PRIMARY KEY,
    #         ...
    #     )
    # """)
    # conn.commit()
    pass


def downgrade(conn):
    """Rollback migration."""
    cursor = conn.cursor()
    # TODO: Add rollback SQL here
    # cursor.execute("DROP TABLE IF EXISTS new_table")
    # conn.commit()
    pass
'''

    filepath.write_text(template)
    print(f"✓ Created migration: {filename}")
    print(f"  Location: {filepath}")
    print(f"  Edit the upgrade() and downgrade() functions to define your schema changes")


def main() -> None:
    """Main CLI entry point."""
    db_path = Path(__file__).parent.parent / "data" / "videos.db"

    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command> [args]")
        print()
        print("Commands:")
        print("  upgrade [--to N]     Apply pending migrations (optionally to version N)")
        print("  downgrade [--steps N] Rollback N migration(s) (default: 1)")
        print("  status              Show current migration status")
        print("  create <name>       Create a new migration file")
        return

    command = sys.argv[1]

    if command == "upgrade":
        target_version = None
        if len(sys.argv) > 2 and sys.argv[2] == "--to":
            if len(sys.argv) > 3:
                try:
                    target_version = int(sys.argv[3])
                except ValueError:
                    print("✗ Invalid version number")
                    return
            else:
                print("✗ --to requires a version number")
                return

        run_upgrade(db_path, target_version)

    elif command == "downgrade":
        steps = 1
        if len(sys.argv) > 2 and sys.argv[2] == "--steps":
            if len(sys.argv) > 3:
                try:
                    steps = int(sys.argv[3])
                except ValueError:
                    print("✗ Invalid step count")
                    return
            else:
                print("✗ --steps requires a number")
                return

        run_downgrade(db_path, steps)

    elif command == "status":
        print_status(db_path)

    elif command == "create":
        if len(sys.argv) < 3:
            print("✗ create requires a migration name")
            print("  Usage: python migrate.py create <name>")
            return

        name = " ".join(sys.argv[2:])
        create_migration(name)

    else:
        print(f"✗ Unknown command: {command}")
        print()
        print("Valid commands: upgrade, downgrade, status, create")


if __name__ == "__main__":
    main()
