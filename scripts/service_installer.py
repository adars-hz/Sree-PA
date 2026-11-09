import os
import subprocess
import sys
from pathlib import Path
from backend.app.core.config import settings
from backend.app.core.logger import logger

def install_sree_service():
    """
    Registers SREE as a Windows Service using NSSM (Non-Sucking Service Manager).
    Requires nssm.exe to be present in the scripts folder or in the system PATH.
    """
    nssm_path = Path("scripts/nssm.exe")
    if not nssm_path.exists():
        # Try looking in system path
        nssm_path = Path("nssm")

    if not nssm_path.exists() and nssm_path.name == "nssm.exe":
        logger.error("nssm.exe not found. Please download NSSM and place it in the scripts/ folder.")
        print("Error: nssm.exe not found. Please download NSSM and place it in the scripts/ folder.")
        return False

    service_name = "SREE_Assistant"
    python_exe = sys.executable
    # Using desktop_app.py as the entrypoint for background operation
    app_script = (Path(__file__).parent / "desktop_app.py").absolute()

    try:
        # Install service
        subprocess.run(["nssm", "install", service_name, python_exe, str(app_script)], check=True)
        # Set to Delayed Start (to ensure Ollama starts first)
        subprocess.run(["nssm", "set", service_name, "Start", "Delayed"], check=True)

        logger.info(f"SREE successfully registered as Windows Service: {service_name}")
        print(f"Successfully installed {service_name} as a Windows Service.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install SREE service: {e}")
        print(f"Error installing service: {e}")
        return False

if __name__ == "__main__":
    install_sree_service()
