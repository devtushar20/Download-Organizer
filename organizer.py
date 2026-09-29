import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification

DOWNLOADS_DIR = Path.home() / "Downloads"

FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".webm"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Installers": [".exe", ".msi"],
    "Audio": [".mp3", ".wav", ".aac", ".flac"],
}

# Temporary files, active downloads, and Windows system files to ignore
IGNORE_EXTENSIONS = {".crdownload", ".tmp", ".part", ".ini", ".lnk"}
IGNORE_FILENAMES = {"desktop.ini"}


def get_unique_path(target_folder: Path, filename: str) -> Path:
    path = target_folder / filename
    if not path.exists():
        return path

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while path.exists():
        path = target_folder / f"{stem}_{counter}{suffix}"
        counter += 1
    return path


def wait_until_ready(file_path: Path, timeout: int = 15) -> bool:
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        try:
            if not file_path.exists():
                return False
            current_size = file_path.stat().st_size
            if current_size > 0 and current_size == last_size:
                return True
            last_size = current_size
            time.sleep(1)
        except (PermissionError, FileNotFoundError):
            time.sleep(1)
    return False


def notify_user(title: str, message: str):
    """Triggers a native Windows desktop notification."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Downloads Organizer",
            timeout=4
        )
    except Exception:
        pass


def move_file_to_category(file_path: Path, notify: bool = True):
    """Core logic to organize a single file into its category/year/month folder."""
    if not wait_until_ready(file_path):
        return

    file_ext = file_path.suffix.lower()

    # 1. Match category
    target_category = "Others"
    for category, extensions in FILE_CATEGORIES.items():
        if file_ext in extensions:
            target_category = category
            break

    # 2. Date-based grouping based on actual file modification date
    file_mtime = file_path.stat().st_mtime
    file_date = datetime.fromtimestamp(file_mtime)
    year_str = file_date.strftime("%Y")
    month_str = file_date.strftime("%B")

    destination_folder = DOWNLOADS_DIR / target_category / year_str / month_str
    destination_folder.mkdir(parents=True, exist_ok=True)
    target_path = get_unique_path(destination_folder, file_path.name)

    try:
        shutil.move(str(file_path), str(target_path))
        rel_display = f"{target_category}/{year_str}/{month_str}"
        print(f"[Organized] {file_path.name} -> {rel_display}")
        if notify:
            notify_user("File Organized", f"{file_path.name} -> {rel_display}")
    except Exception as e:
        print(f"[Error] Could not move {file_path.name}: {e}")


def initial_cleanup():
    """Scans and organizes all pre-existing files sitting directly in Downloads."""
    print("Running initial cleanup on existing files...")
    organized_count = 0

    try:
        for item in DOWNLOADS_DIR.iterdir():
            # Skip directories (so we don't touch Images/, Documents/, etc.)
            if item.is_dir():
                continue

            # Skip system and ignored files
            if item.name.lower() in IGNORE_FILENAMES or item.suffix.lower() in IGNORE_EXTENSIONS:
                continue

            # Move file without spamming individual notifications
            move_file_to_category(item, notify=False)
            organized_count += 1

        if organized_count > 0:
            print(f"Initial cleanup finished: {organized_count} files organized.")
            notify_user(
                "Downloads Cleaned",
                f"Organized {organized_count} existing files on startup."
            )
        else:
            print("Initial cleanup finished: Downloads folder is already clean.")
    except Exception as e:
        print(f"[Error] Failed during initial cleanup: {e}")


class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.name.lower() in IGNORE_FILENAMES or file_path.suffix.lower() in IGNORE_EXTENSIONS:
            return
        move_file_to_category(file_path, notify=True)

    def on_moved(self, event):
        if event.is_directory:
            return
        file_path = Path(event.dest_path)
        if file_path.name.lower() in IGNORE_FILENAMES or file_path.suffix.lower() in IGNORE_EXTENSIONS:
            return
        move_file_to_category(file_path, notify=True)


if __name__ == "__main__":
    print(f"Monitoring folder: {DOWNLOADS_DIR}")

    # 1. Sweep existing clutter before watching for new downloads
    initial_cleanup()

    # 2. Start live filesystem monitoring
    event_handler = DownloadHandler()
    observer = Observer()
    observer.schedule(event_handler, str(DOWNLOADS_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nOrganizer stopped.")
    observer.join()