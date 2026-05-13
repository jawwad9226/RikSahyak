import os
import subprocess
from fastapi import APIRouter, Depends
import psutil
from app.api.deps import verify_admin_token

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(verify_admin_token)])

def read_sys_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except (PermissionError, FileNotFoundError):
        try:
            # Fallback to su if rooted (Magisk)
            result = subprocess.run(["su", "-c", f"cat {path}"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
    return "N/A"

@router.get("/health")
def get_system_health():
    # Battery
    battery_level = read_sys_file("/sys/class/power_supply/battery/capacity")
    
    # Try different thermal zones for CPU temp
    cpu_temp = "N/A"
    for zone in range(15):
        temp = read_sys_file(f"/sys/class/thermal/thermal_zone{zone}/temp")
        if temp != "N/A":
            try:
                # Often in millidegrees Celsius
                temp_int = int(temp)
                if temp_int > 1000:
                    temp_int = temp_int / 1000
                if temp_int > 0: # Sanity check
                    cpu_temp = f"{temp_int}°C"
                    break
            except ValueError:
                pass
    
    # Memory
    try:
        mem = psutil.virtual_memory()
        ram_used_mb = mem.used / (1024 * 1024)
        ram_total_mb = mem.total / (1024 * 1024)
        ram = f"{ram_used_mb:.0f}MB / {ram_total_mb:.0f}MB"
    except Exception:
        ram = "N/A"

    return {
        "battery_percent": battery_level,
        "cpu_temperature": cpu_temp,
        "ram_usage": ram
    }

@router.get("/logs")
def get_system_logs(lines: int = 100):
    try:
        # First try to see if PM2 is running and get its logs
        pm2_logs = subprocess.run(
            ["pm2", "logs", "riksahyak-api", "--raw", "--nostream", "--lines", str(lines)],
            capture_output=True, text=True, timeout=5
        )
        if pm2_logs.returncode == 0 and pm2_logs.stdout.strip():
            return {"logs": pm2_logs.stdout.splitlines()}
    except Exception:
        pass
        
    # Fallback to nohup.out
    try:
        # Resolve path to backend folder nohup.out
        nohup_path = os.path.join(os.getcwd(), "nohup.out")
        if os.path.exists(nohup_path):
            result = subprocess.run(["tail", "-n", str(lines), nohup_path], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return {"logs": result.stdout.splitlines()}
    except Exception:
        pass
        
    return {"logs": ["No logs found. Ensure PM2 is running with name 'riksahyak-api' or nohup.out exists."]}
