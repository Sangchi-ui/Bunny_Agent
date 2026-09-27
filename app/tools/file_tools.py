import os
import shutil
import uuid
import time
from pathlib import Path
from typing import Dict, Any

from app.safety import DELETE_REQUIRES_CONFIRMATION

# In-memory store for pending deletions
_pending_deletions = {}

def list_files(folder: str) -> Dict[str, Any]:
    try:
        p = Path(folder)
        if not p.is_dir():
            return {"success": False, "error": f"{folder} is not a directory."}
        
        items = []
        for child in p.iterdir():
            items.append({
                "name": child.name,
                "is_dir": child.is_dir(),
                "size": child.stat().st_size if child.is_file() else None
            })
        return {"success": True, "data": items}
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_file(path: str, max_bytes: int = 100_000) -> Dict[str, Any]:
    try:
        p = Path(path)
        if not p.is_file():
            return {"success": False, "error": f"{path} is not a file."}
            
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read(max_bytes)
            
        return {"success": True, "data": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_file(path: str, content: str) -> Dict[str, Any]:
    try:
        p = Path(path)
        if p.exists():
            return {"success": False, "error": f"File {path} already exists. Use write_file to modify."}
            
        # Ensure parent exists
        p.parent.mkdir(parents=True, exist_ok=True)
        
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {"success": True, "data": f"Created {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_file(path: str, content: str, mode: str = "overwrite") -> Dict[str, Any]:
    try:
        p = Path(path)
        file_mode = 'a' if mode == "append" else 'w'
        
        # Ensure parent exists
        p.parent.mkdir(parents=True, exist_ok=True)
        
        with open(p, file_mode, encoding='utf-8') as f:
            f.write(content)
            
        return {"success": True, "data": f"Successfully wrote to {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def rename_file(old_path: str, new_path: str) -> Dict[str, Any]:
    try:
        p_old = Path(old_path)
        p_new = Path(new_path)
        
        if not p_old.exists():
            return {"success": False, "error": f"{old_path} does not exist."}
            
        p_new.parent.mkdir(parents=True, exist_ok=True)
        p_old.rename(p_new)
        
        return {"success": True, "data": f"Renamed {old_path} to {new_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def move_file(src: str, dest: str) -> Dict[str, Any]:
    try:
        p_src = Path(src)
        p_dest = Path(dest)
        
        if not p_src.exists():
            return {"success": False, "error": f"{src} does not exist."}
            
        p_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p_src), str(p_dest))
        
        return {"success": True, "data": f"Moved {src} to {dest}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_file(path: str, confirmation_token: str = None) -> Dict[str, Any]:
    try:
        p = Path(path)
        
        if not p.exists():
            return {"success": False, "error": f"{path} does not exist."}
            
        if DELETE_REQUIRES_CONFIRMATION:
            resolved_path = str(p.resolve())
            now = time.time()
            
            # Clean up expired tokens
            expired = [k for k, v in _pending_deletions.items() if now > v['expiry']]
            for k in expired:
                del _pending_deletions[k]
                
            if confirmation_token:
                if confirmation_token in _pending_deletions:
                    pending = _pending_deletions[confirmation_token]
                    if pending['path'] == resolved_path:
                        # Perform delete
                        del _pending_deletions[confirmation_token]
                        if p.is_dir():
                            shutil.rmtree(p)
                        else:
                            p.unlink()
                        return {"success": True, "data": f"Deleted {path}"}
                    else:
                        return {"success": False, "error": "Token does not match the requested path."}
                else:
                    return {"success": False, "error": "Invalid or expired confirmation token."}
            else:
                # Generate token
                token = str(uuid.uuid4())
                _pending_deletions[token] = {
                    'path': resolved_path,
                    'expiry': now + 60
                }
                return {
                    "success": False, 
                    "error": f"Deletion requires confirmation. Call delete_file again with confirmation_token='{token}' within 60 seconds."
                }
                
        # If no confirmation required
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return {"success": True, "data": f"Deleted {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
