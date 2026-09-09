"""
app/documents/storage_service.py
---------------------------------
Sprint 4 — RAG Knowledge Engine

Handles all filesystem interactions for uploaded documents:
  - Computing a SHA-256 hash of uploaded file bytes (for duplicate detection).
  - Saving a Werkzeug FileStorage object to the local documents/ directory.
  - Deleting a file from disk (called during document deletion).

The storage root defaults to <project_root>/documents/ and can be overridden
via the DOCUMENTS_STORAGE_DIR environment variable.
"""

from __future__ import annotations

import hashlib
import os
import sys

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import logger  # noqa: E402

# --------------------------------------------------------------------------- #
# Storage directory
# --------------------------------------------------------------------------- #
STORAGE_DIR: str = os.getenv(
    "DOCUMENTS_STORAGE_DIR",
    os.path.join(_PROJECT_ROOT, "documents"),
)


def _ensure_storage_dir() -> None:
    """Create the storage directory if it does not already exist."""
    os.makedirs(STORAGE_DIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def compute_file_hash(file_storage: FileStorage) -> str:
    """
    Compute the SHA-256 hex digest of the uploaded file's bytes.

    The file pointer is rewound to position 0 after reading so the caller
    can still save the file normally.

    Parameters
    ----------
    file_storage : FileStorage
        Werkzeug ``FileStorage`` object from the Flask request.

    Returns
    -------
    str
        64-character lowercase SHA-256 hex string.
    """
    sha256 = hashlib.sha256()
    # Read in 64 KB chunks to handle large files without exhausting memory.
    file_storage.stream.seek(0)
    while chunk := file_storage.stream.read(65_536):
        sha256.update(chunk)
    file_storage.stream.seek(0)  # rewind for subsequent save
    return sha256.hexdigest()


def save_file(file_storage: FileStorage, filename: str) -> str:
    """
    Persist an uploaded file to the local documents/ storage directory.

    Parameters
    ----------
    file_storage : FileStorage
        Werkzeug ``FileStorage`` object from the Flask request.
    filename : str
        The sanitised filename to use when saving (caller must sanitise).

    Returns
    -------
    str
        Absolute filesystem path of the saved file.

    Raises
    ------
    OSError
        If the file cannot be written to disk.
    """
    _ensure_storage_dir()
    safe_name  = secure_filename(filename)
    dest_path  = os.path.join(STORAGE_DIR, safe_name)
    file_storage.stream.seek(0)
    file_storage.save(dest_path)
    logger.info(f"[storage_service] File saved: {dest_path}")
    return dest_path


def delete_file(file_path: str) -> bool:
    """
    Remove a file from the local documents/ directory.

    Parameters
    ----------
    file_path : str
        Absolute filesystem path of the file to delete.

    Returns
    -------
    bool
        ``True`` if the file was deleted, ``False`` if it did not exist.
    """
    if not os.path.exists(file_path):
        logger.warning(f"[storage_service] File not found for deletion: {file_path}")
        return False
    os.remove(file_path)
    logger.info(f"[storage_service] File deleted: {file_path}")
    return True
