# Project Setup Guide

This guide provides instructions to set up a Python virtual environment using a specific Python version and install the project dependencies.

## Prerequisites

Ensure you have Python 3.9.6 installed on your system. You can check your installed version by running:

```bash
python3 --version
```

If you have multiple Python versions installed, you may need to specify the exact path to the Python 3.9.6 executable (e.g., `/usr/local/bin/python3.9` or `C:\Python39\python.exe`).

## Setup Instructions

Follow these steps to create the virtual environment and install the required packages.

### 1. Clone or Navigate to the Project Directory

Open your terminal or command prompt and change to the project root directory:

```bash
cd path/to/your/project
```

### 2. Create the Virtual Environment

Create a new virtual environment named `.venv` using Python 3.9.6. 

**On macOS/Linux:**
```bash
python3.9 -m venv .venv
```
*(Replace `python3.9` with the absolute path to your 3.9.6 executable if necessary)*

**On Windows:**
```cmd
py -3.9 -m venv .venv
```

### 3. Activate the Virtual Environment

You must activate the virtual environment before installing packages or running the project.

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

Once activated, your terminal prompt will show `(.venv)`.

### 4. Upgrade Pip (Recommended)

Ensure you have the latest version of `pip` installed inside your environment:

```bash
python -m pip install --upgrade pip
```

### 5. Install Dependencies

Install the required packages listed in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

---

## Deactivation

When you are done working on the project, you can exit the virtual environment by running:

```bash
deactivate
```
