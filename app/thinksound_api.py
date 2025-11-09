# app/thinksound_api.py
# Minimal wie bei WAN: Sync + Async-Jobs für ThinkSound/demos.sh

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import os, uuid, subprocess, threading, json, re

# Basis-Pfade (wie bei deinem Setup)
THINK_ROOT = os.getenv("THINK_ROOT", "/workspace/ThinkSound")
THINK_DEMO = os.getenv("THINK_DEMO", os.path.join(THINK_ROOT, "scripts", "demo.sh"))
JOBS_DIR = os.getenv("JOBS_DIR", "/workspace/jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

class TSRequest(BaseModel):
    video_path: str              # Eingabevideo (absoluter Pfad)
    text: str                    # Beschreibungstext
    sample_id: Optional[str] = None  # optionaler Name für demo.sh

def _job_paths(job_id: str) -> Dict[str, str]:
    jdir = os.path.join(JOBS_DIR, job_id)
    return {
        "dir": jdir,
        "meta": os.path.join(jdir, "job.json"),
        "log": os.path.join(jdir, "out.log"),
        "result": os.path.join(jdir, "result.json"),
    }

def _wjson(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _rjson(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def _parse_audio(stdout: str) -> Optional[str]:
    # Erwartet Zeile: "Audio file path: /…/demo.wav"
    m = re.search(r"Audio file path:\s*(.+?\.wav)", stdout)
    return m.group(1).strip() if m else None

def _cmd(req: TSRequest) -> list:
    sid = (req.sample_id or uuid.uuid4().hex[:8])
    return ["bash", THINK_DEMO, req.video_path, sid, req.text]

# ---- Sync (blockierend, wie /wan/generate) ----
def run_thinksound(req: TSRequest) -> dict:
    env = os.environ.copy()
    # Gleiche Speicher-Flags wie bei dir
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:64")
    p = subprocess.run(
        _cmd(req), cwd=THINK_ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    audio_path = _parse_audio(p.stdout or "")
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout,
        "audio_path": audio_path,
    }

# ---- Async (submit/status/result wie bei WAN) ----
def submit_ts_job(req: TSRequest) -> str:
    job_id = uuid.uuid4().hex
    paths = _job_paths(job_id)
    _wjson(paths["meta"], {
        "job_id": job_id, "status": "queued",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "params": req.model_dump()
    })

    def _runner():
        env = os.environ.copy()
        env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:64")
        meta = _rjson(paths["meta"]) or {}
        meta["status"] = "running"
        meta["started_at"] = datetime.utcnow().isoformat() + "Z"
        _wjson(paths["meta"], meta)

        with open(paths["log"], "w", encoding="utf-8") as logf:
            p = subprocess.Popen(
                _cmd(req), cwd=THINK_ROOT, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            out = []
            for line in p.stdout:
                logf.write(line)
                out.append(line)
            p.wait()
            full_out = "".join(out)
            audio_path = _parse_audio(full_out)

        meta = _rjson(paths["meta"]) or {}
        meta["finished_at"] = datetime.utcnow().isoformat() + "Z"
        meta["returncode"] = p.returncode
        if p.returncode == 0:
            meta["status"] = "done"
            _wjson(paths["result"], {"job_id": job_id, "audio_path": audio_path})
        else:
            meta["status"] = "error"
        _wjson(paths["meta"], meta)

    threading.Thread(target=_runner, daemon=True).start()
    return job_id

def get_ts_status(job_id: str) -> Dict[str, Any]:
    paths = _job_paths(job_id)
    meta = _rjson(paths["meta"])
    if not meta:
        return {"error": "job_not_found", "job_id": job_id}
    prog = 1.0 if meta.get("status") == "done" else (0.5 if meta.get("status") == "running" else 0.0)
    return {"job_id": job_id, "status": meta.get("status"), "progress": prog}

def get_ts_result(job_id: str) -> Dict[str, Any]:
    paths = _job_paths(job_id)
    meta = _rjson(paths["meta"])
    if not meta:
        return {"error": "job_not_found", "job_id": job_id}
    if meta.get("status") != "done":
        return {"error": "not_ready", "job_id": job_id, "status": meta.get("status")}
    res = _rjson(paths["result"]) or {}
    return {"job_id": job_id, "status": "done", "audio_path": res.get("audio_path")}
