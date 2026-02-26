"""
Restore Backup Utility — Restores models, data, and registries from backup snapshots. (Phase 34)
"""
import os
import shutil
from src.utils.logger import logger

def restore_backup(backup_id: str, backup_dir: str = "backups"):
    """
    Restores the system state closely matching the given backup ID.
    In a true prod scenario, this would pull from an S3 or GCP bucket.
    """
    target_backup = os.path.join(backup_dir, backup_id)
    if not os.path.exists(target_backup):
        logger.error("Backup %s not found.", target_backup)
        return False

    logger.info("Restoring from backup %s...", backup_id)
    
    # Example logic: Copying back core models and databases
    models_src = os.path.join(target_backup, "models")
    data_src = os.path.join(target_backup, "data")
    
    if os.path.exists(models_src):
        for item in os.listdir(models_src):
            s = os.path.join(models_src, item)
            d = os.path.join("models", item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
                
    if os.path.exists(data_src):
        for item in os.listdir(data_src):
            s = os.path.join(data_src, item)
            d = os.path.join("data", item)
            if os.path.isfile(s):
                shutil.copy2(s, d)

    logger.info("Restore complete.")
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python restore_backup.py <backup_id>")
        sys.exit(1)
    restore_backup(sys.argv[1])
