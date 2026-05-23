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

A folder picker will open — select your project folder and `project-Info.md` will be generated in the same directory as `main.py`.

---

## How to use

1. Copy `read.projectignore` into your project root
2. Edit the `[PROJECT_INFO]` section with your project details
3. Run `main.py` and select that project folder

---

## Files

| File | Description |
|---|---|
| `main.py` | Main script — run this |
| `read.projectignore` | Config file — place this in your project root |
| `project-Info.md` | Generated output |

---

## read.projectignore sections

| Section | Description |
|---|---|
| `[PROJECT_INFO]` | Free-text info shown at the top of the output |
| `[TREE_IGNORE]` | Folders/files to hide from the project tree |
| `[CONTENT_IGNORE]` | Files to skip when collecting source code |