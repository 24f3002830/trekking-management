"""
Submission Packager Script for Trekking Management Application (TMA).
Packages the project into the exact required structure specified in the rubric:
- Root directory inside zip: trekking_management_24f3002830/
  ├── frontend/
  │   └── src/components/
  ├── backend/
  │   ├── models/
  │   ├── routes/
  │   └── app.py
  ├── README.md
  └── requirements.txt
Excludes unnecessary files (__pycache__, .git, virtual environments, sqlite db files).
"""

import os
import zipfile

STUDENT_ROLL = "24f3002830"
PROJECT_NAME = "trekking_management"
ARCHIVE_ROOT = f"{PROJECT_NAME}_{STUDENT_ROLL}"
ZIP_FILENAME = f"{ARCHIVE_ROOT}.zip"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_ZIP_PATH = os.path.join(BASE_DIR, ZIP_FILENAME)

EXCLUDE_DIRS = {
    '.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules',
    '.pytest_cache', '.idea', '.vscode'
}

EXCLUDE_FILES = {
    'trekking.db', ZIP_FILENAME, '.DS_Store', 'Thumbs.db', 'notifications.log'
}

EXCLUDE_EXTENSIONS = {
    '.pyc', '.pyo', '.sqlite', '.db'
}


def should_include(rel_path):
    parts = rel_path.split(os.sep)
    for part in parts:
        if part in EXCLUDE_DIRS:
            return False

    base_name = os.path.basename(rel_path)
    if base_name in EXCLUDE_FILES:
        return False

    _, ext = os.path.splitext(base_name)
    if ext in EXCLUDE_EXTENSIONS:
        return False

    return True


def create_submission_zip():
    print(f"📦 Packaging submission into {ZIP_FILENAME}...")
    file_count = 0

    with zipfile.ZipFile(OUTPUT_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_DIR)

                if should_include(rel_path):
                    archive_path = os.path.join(ARCHIVE_ROOT, rel_path)
                    zipf.write(full_path, archive_path)
                    file_count += 1

    print(f"✅ Successfully created {ZIP_FILENAME} with {file_count} files.")
    print(f"📍 Location: {OUTPUT_ZIP_PATH}")


if __name__ == '__main__':
    create_submission_zip()
