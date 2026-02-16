# VAPIX Test Tool

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Build](https://img.shields.io/badge/Build-PyInstaller-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

## Overview

**VAPIX Test Tool** is a desktop QA utility for testing **Axis VAPIX API
endpoints**.\
It allows engineers and testers to:

-   Send single API requests
-   Execute multiple presets sequentially
-   Generate **happy & unhappy test payloads**
-   Log responses automatically
-   Run as a **standalone executable** built with PyInstaller

------------------------------------------------------------------------

## Features

### API Testing

-   Supports **GET / SET / REMOVE** VAPIX endpoints
-   Sends authenticated HTTP Digest requests
-   Displays formatted JSON responses in UI

### Preset System

-   Load & save reusable presets
-   Filter by:
    -   **Test mode** → happy / unhappy
    -   **Search text**
-   Automatic JSON payload binding

### Unhappy Testing Generator

Creates negative test cases:

-   No data
-   Invalid values
-   Wrong data types
-   Fuzz payloads

### Logging

-   Timestamped log files
-   Separate logs for multi‑preset runs
-   Stored inside `/logs` directory

### Desktop UI

-   Built with **PySide6**
-   Clean light theme
-   Async requests using **QThread**

------------------------------------------------------------------------

## Project Structure

    src/
     ├── main.py
     ├── ui/
     ├── dialogs/
     ├── requests_manager.py
     ├── presets.py
     ├── constants.py
     ├── json_configs/
     └── logs/

------------------------------------------------------------------------

## Installation

### Requirements

-   Python **3.10+**
-   pip

### Install dependencies

``` bash
pip install -r requirements.txt
```

### Run application

``` bash
python main.py
```

------------------------------------------------------------------------

## Build Standalone Executable

The project can be packaged using **PyInstaller**.

### Build command

``` bash
pyinstaller --onefile --noconsole --icon=vapix_icon.ico main.py
```

### Output

    dist/
     └── main.exe

This executable:

-   Requires **no Python installation**
-   Includes all dependencies
-   Ready for distribution to QA teams

------------------------------------------------------------------------

## Usage

1.  Enter **device IP**
2.  Select **preset**
3.  Click **SEND REQUEST**\
    or\
    **RUN MULTIPLE PRESETS**
4.  View formatted response & logs

------------------------------------------------------------------------

## Logging

Logs are automatically saved:

    logs/log_<preset>_<timestamp>.log

Includes:

-   URL
-   Payload
-   Status code
-   Response body

------------------------------------------------------------------------

## License

MIT License --- free to use in internal QA and automation workflows.

------------------------------------------------------------------------

## Author

Developed for **Axis VAPIX QA automation & testing workflows**.
