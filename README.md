# Directory Size Analyzer

![UI Screenshot](UI_Photo.png)

A lightweight, minimal graphical utility for Windows that analyzes directory sizes down to every file and nested folder. It recursively calculates the comprehensive sizes of all folders, enabling you to rapidly pinpoint what is occupying your disk space on a granular level.

## ✨ Features
- **Clean Graphical UI:** An intuitive, responsive Tkinter-based interface designed to visualize large quantities of files smoothly.
- **Deep Scanning:** Select any directory, and the tool dynamically analyzes the cumulative size of all underlying files and folders.
- **Sort & Filter:** Click on column headers (Name, Type, Size) to automatically sort your data. Utilize the real-time filter bar to search for specific file types (e.g. `mp4`, `pdf`) or specific names.
- **Native File Explorer Integration:** Double-click any row item in the list to instantly launch its native graphical location in the Windows File Explorer.
- **JSON Reports:** Keep a record of your analyzed data. One-click JSON generation natively snapshots your current list to a gracefully formatted JSON file located in the generated `reports/` folder.

## 🚀 How to Run
Because this software strictly adheres to standard built-in Python libraries, you do NOT need to install any massive third-party packages or frameworks!

1. Clone or download this repository.
2. Ensure you have Python 3 installed on your Windows machine.
3. Simply execute the script via terminal or command prompt:
```bash
python analyze.py
```

## 📦 Requirements
This tool is built on **Zero External Dependencies**. All dependencies utilized are part of the standard Python 3 Library.
(See `requirements.txt` for more context).
