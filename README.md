# Download Organizer

A Windows Python utility that watches the user's `Downloads` folder and sorts files into category, year, and month directories.

## How It Works

When started, the program:

1. Scans files that are already directly inside `%USERPROFILE%\\Downloads`.
2. Classifies each file by its lowercase extension.
3. Places files in a structure like:

```text
Downloads/
├── Images/2026/September/
├── Documents/2026/September/
├── Videos/2026/September/
├── Archives/2026/September/
├── Installers/2026/September/
├── Audio/2026/September/
└── Others/2026/September/
```

4. Starts a non-recursive filesystem watcher for newly created or moved files.
5. Sends a Windows desktop notification after a file is organized.

The year and month are based on the file's last modification time, not the time when the download event is received.

## Supported Categories

| Category | Extensions |
| --- | --- |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp` |
| Videos | `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm` |
| Documents | `.pdf`, `.docx`, `.doc`, `.txt`, `.xlsx`, `.pptx`, `.csv` |
| Archives | `.zip`, `.rar`, `.7z`, `.tar`, `.gz` |
| Installers | `.exe`, `.msi` |
| Audio | `.mp3`, `.wav`, `.aac`, `.flac` |
| Others | Any extension not listed above |

The program ignores active download and Windows system files with these extensions or names:

- `.crdownload`, `.tmp`, `.part`, `.ini`, `.lnk`
- `desktop.ini`

## Requirements

- Windows
- Python 3.9 or newer
- The `watchdog` and `plyer` packages

Install the dependencies with:

```powershell
python -m pip install watchdog plyer
```

## Running

From the project directory, run:

```powershell
python organizer.py
```

The program keeps running until it receives `Ctrl+C`.

## Duplicate Names

If a file with the same name already exists in the destination folder, the program adds a numeric suffix:

```text
report.pdf
report_1.pdf
report_2.pdf
```

## Operational Notes

- The watcher monitors only the top level of the Downloads folder; it does not recursively monitor existing category folders.
- Files are considered ready only after their size is non-zero and unchanged for one polling interval.
- Readiness checks time out after 15 seconds.
- The initial cleanup count currently increments for each candidate file even if that file is not successfully moved.
- `plyer` notification errors are intentionally suppressed, so notification failures do not stop file organization.

## Stopping the Program

Press `Ctrl+C` in the terminal. The observer is stopped and the process exits.
