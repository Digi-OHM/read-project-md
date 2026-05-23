# read-project-md

A Python utility that generates a complete project overview as `project-Info.md` — ready to share with AI tools or team members for analysis, documentation, and code reviews.

---

## Setup

**1. Create virtual environment**
```bash
python -m venv venv
```

**2. Activate** *(if PowerShell blocks activation, run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` first)*
```bash
.\venv\Scripts\Activate
```

**3. Install dependencies**
```bash
pip install chardet
```

---

## Run

```bash
python .\main.py
```

A folder picker will open — select your project folder and `project-Info.md` will be generated in the **current working directory**.

---

## Build .exe

**1. Install PyInstaller**
```bash
pip install pyinstaller
```

**2. Build**
```bash
pyinstaller --onefile --windowed --icon=read-project-md.ico --name="read-project-md" main.py
```

The `.exe` will be in the `dist/` folder after building.

> If `pyinstaller` is not recognized, use `python -m PyInstaller` instead.

**3. Run**

Double-click `read-project-md.exe` or run it from any folder — `project-Info.md` will be saved in the folder you run it from.

| Flag | Description |
|---|---|
| `--onefile` | Packages everything into a single `.exe` |
| `--windowed` | Hides the terminal window |
| `--icon` | Sets the `.exe` icon (must be `.ico` format) |
| `--name` | Sets the output filename |

---

## How to use

1. Copy `read.projectignore` into your project root
2. Edit the `[PROJECT_INFO]` section with your project details
3. Run `main.py` or `read-project-md.exe` and select that project folder
4. A toast notification will confirm success or show an error

---

## Files

| File | Description |
|---|---|
| `main.py` | Main script — run this |
| `read.projectignore` | Config file — place this in your project root |
| `read-project-md.ico` | Icon used for the `.exe` build |
| `project-Info.md` | Generated output |

---

## read.projectignore sections

| Section | Description |
|---|---|
| `[PROJECT_INFO]` | Free-text info shown at the top of the output |
| `[TREE_IGNORE]` | Folders/files to hide from the project tree |
| `[CONTENT_IGNORE]` | Files to skip when collecting source code |
