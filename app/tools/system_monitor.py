import psutil
from typing import Dict, Any, List

def get_cpu_usage() -> Dict[str, Any]:
    try:
        overall = psutil.cpu_percent(interval=1, percpu=False)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        return {
            "success": True,
            "data": {
                "overall_percent": overall,
                "per_core_percent": per_core
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_ram_usage() -> Dict[str, Any]:
    try:
        mem = psutil.virtual_memory()
        return {
            "success": True,
            "data": {
                "total": mem.total,
                "used": mem.used,
                "available": mem.available,
                "percent": mem.percent
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_disk_usage(path: str = "C:\\") -> Dict[str, Any]:
    try:
        disk = psutil.disk_usage(path)
        return {
            "success": True,
            "data": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_gpu_usage() -> Dict[str, Any]:
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {
                "success": True,
                "data": {"available": False, "message": "No GPU found by GPUtil."},
                "error": None
            }
        
        gpu_data = []
        for gpu in gpus:
            gpu_data.append({
                "id": gpu.id,
                "name": gpu.name,
                "load_percent": gpu.load * 100,
                "memory_total": gpu.memoryTotal,
                "memory_used": gpu.memoryUsed,
                "memory_free": gpu.memoryFree,
                "memory_percent": gpu.memoryUtil * 100,
                "temperature": gpu.temperature
            })
            
        return {
            "success": True,
            "data": {"available": True, "gpus": gpu_data},
            "error": None
        }
    except ImportError:
        return {
            "success": True,
            "data": {"available": False, "message": "GPUtil is not installed."},
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_top_processes(n: int = 5) -> Dict[str, Any]:
    try:
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        # Sort by memory percent descending
        processes.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
        top_mem = processes[:n]
        
        # Sort by cpu percent descending
        processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
        top_cpu = processes[:n]
        
        return {
            "success": True,
            "data": {
                "top_by_memory": top_mem,
                "top_by_cpu": top_cpu
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}

def get_network_status() -> Dict[str, Any]:
    try:
        stats = psutil.net_if_stats()
        up_interfaces = [name for name, stat in stats.items() if stat.isup]
        
        return {
            "success": True,
            "data": {
                "network_up": len(up_interfaces) > 0,
                "up_interfaces": up_interfaces
            },
            "error": None
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}
