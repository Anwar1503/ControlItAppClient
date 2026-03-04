import os
import shutil
import subprocess
import sys
from logger import setup_logger

REQUIRED_PYTHON = (3, 12)

if sys.version_info[:2] != REQUIRED_PYTHON:
    raise RuntimeError(
        f"Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]} is required. "
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}"
    )

logger = setup_logger("build_service")

PROJECT_NAME = "agent"
ENTRY_FILE = "agent.py"

def run(cmd):
    logger.debug(">> %s", " ".join(cmd))
    subprocess.check_call(cmd)

def clean():
    for item in ["build", "dist", f"{PROJECT_NAME}.spec"]:
        if os.path.exists(item):
            logger.debug("Removing %s", item)
            shutil.rmtree(item) if os.path.isdir(item) else os.remove(item)

def main():
    logger.info("=== ControlIt Agent Build ===")

    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    clean()

    run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        ENTRY_FILE
    ])

    logger.info("✅ Build complete")
    logger.info("📦 EXE located in dist/")

if __name__ == "__main__":
    main()
