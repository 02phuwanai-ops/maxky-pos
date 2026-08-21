import os
import shutil
from datetime import datetime

DB_FILE = "data/maxky_pos.db"
BACKUP_DIR = "backup"


def backup_database():

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_file = os.path.join(
        BACKUP_DIR,
        f"maxky_pos_{timestamp}.db"
    )

    shutil.copy2(DB_FILE, backup_file)

    return backup_file