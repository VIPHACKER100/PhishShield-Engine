#!/usr/bin/env python
"""
Backup — Create timestamped backups of models, data, and registry.
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.utils.logger import logger

BACKUP_ROOT = os.path.join(os.path.dirname(__file__), "..", "backups")

DIRS_TO_BACKUP = [
    "models",
    "data/processed",
    "data/versions",
    "data/feedback",
    "data/features",
    "experiments",
]


def create_backup(backup_dir: str | None = None, dirs: list[str] | None = None) -> str:
    """
    Create a timestamped backup of specified directories.

    Returns
    -------
    Path to the created backup directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_dir is None:
        backup_dir = os.path.join(BACKUP_ROOT, f"backup_{timestamp}")

    os.makedirs(backup_dir, exist_ok=True)
    targets = dirs or DIRS_TO_BACKUP

    for d in targets:
        src = os.path.join(os.path.dirname(__file__), "..", d)
        if not os.path.exists(src):
            logger.warning("Skipping %s — does not exist", src)
            continue
        dest = os.path.join(backup_dir, d.replace("/", os.sep))
        shutil.copytree(src, dest, dirs_exist_ok=True)
        logger.info("Backed up %s → %s", src, dest)

    logger.info("Backup complete → %s", backup_dir)
    return backup_dir


def restore_backup(backup_dir: str, project_root: str | None = None):
    """
    Restore from a backup directory back into the project.
    """
    if project_root is None:
        project_root = os.path.join(os.path.dirname(__file__), "..")

    for d in DIRS_TO_BACKUP:
        src = os.path.join(backup_dir, d.replace("/", os.sep))
        if not os.path.exists(src):
            continue
        dest = os.path.join(project_root, d)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        logger.info("Restored %s → %s", src, dest)

    logger.info("Restore complete from %s", backup_dir)


def main():
    parser = argparse.ArgumentParser(description="Backup & Restore utility")
    sub = parser.add_subparsers(dest="command")

    bk = sub.add_parser("backup", help="Create a backup")
    bk.add_argument("--output", default=None, help="Output directory")

    rs = sub.add_parser("restore", help="Restore from a backup")
    rs.add_argument("backup_dir", help="Path to backup directory")
    rs.add_argument("--project_root", default=None, help="Project root to restore into")

    args = parser.parse_args()
    if args.command == "backup":
        create_backup(args.output)
    elif args.command == "restore":
        restore_backup(args.backup_dir, args.project_root)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
