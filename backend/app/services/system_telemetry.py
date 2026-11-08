"""
System Telemetry Service for SREE
Provides hardware, CPU, memory, and runtime metrics.
"""

import psutil
from typing import Dict, Any

class TelemetryService:
    def get_system_telemetry(self) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
            "hardware": {
                "ram_total_gb": round(vm.total / (1024**3), 2),
                "ram_used_gb": round(vm.used / (1024**3), 2),
                "ram_percent": vm.percent,
                "cpu_percent": psutil.cpu_percent(interval=None)
            }
        }

telemetry_service = TelemetryService()

