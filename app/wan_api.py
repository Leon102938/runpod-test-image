# app/wan_api.py
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import os, uuid, subprocess, threading, json, re

# ====== Pfade / Defaults ======
WAN_ROOT = os.getenv("WAN_ROOT", "/workspace/Wan2.2")
WAN_CKPT = os.getenv("WAN_CKPT_DIR", "/workspace/Wan2.2/Wan2.2-TI2V-5B")
JOBS_DIR = os.getenv("JOBS_DIR", "/workspace/jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

ALLOWED_SIZES = {
    "720*1280","1280*720","480*832","832*480","704*1280","1280*704","1024*704","704*1024"
}

# ====== Request-Model ======
class TI2VRequest(BaseModel):
    prompt: str
    size: Literal[
        "720*1280","1280*720","480*832","832*480","704*1280","1280*704","1024*704","704*1024"
    ] = "704*1280"
    frame_num: int = 8
    sample_steps: int = 8
    sample_guide_scale: float = 3.0
    offload_model: bool = True
    convert_model_dtype: bool = True
    ckpt_dir: Optional[str] = None
    infer_frames: int = 10 
    task: Literal["ti2v-5B"] = "ti2v-5B"

# ====== Hilfsfunktionen ======
def _job_paths(job_id: str) -> Dict[str, str]:
    jdir = os.path.join(JOBS_DIR, job_id)
    return {
        "dir": jdir,
        "meta": os.path.join(jdir, "job.json"),
        "log": os.path.join(jdir, "out.log"),
        "result": os.path.join(jdir, "result.json"),
    }

def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def _parse_saved_video(stdout: str) -> Optional[str]:
    # sucht nach Zeile: "Saving generated video to <path>.mp4"
    m = re.search(r"Saving generated video to\s+(.+?\.mp4)", stdout)
    return m.group(1).strip() if m else None

def _build_cmd(req: TI2VRequest) -> list:
    ckpt_dir = req.ckpt_dir or WAN_CKPT
    return [
        "python", os.path.join(WAN_ROOT, "generate.py"),
        "--task", req.task,
        "--ckpt_dir", ckpt_dir,
        "--prompt", req.prompt,
        "--size", req.size,
        "--frame_num", str(req.frame_num),
        "--sample_steps", str(req.sample_steps),
        "--sample_guide_scale", str(req.sample_guide_scale),
        "--offload_model", str(req.offload_model),
        "--convert_model_dtype",
        "--infer_frames", str(req.infer_frames),
    ]

# ====== Synchron (bestehend) ======
def run_wan_ti2v(req: TI2VRequest) -> dict:
    env = os.environ.copy()
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:64")

    p = subprocess.run(
        _build_cmd(req), cwd=WAN_ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout,
        "job_id": "sync-"+uuid.uuid4().hex[:8],
        "wan_root": WAN_ROOT,
    }

# ====== Asynchron (Submit → Status → Result) ======
def submit_job(req: TI2VRequest) -> str:
    job_id = uuid.uuid4().hex
    paths = _job_paths(job_id)
    meta = {
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat()+"Z",
        "status": "queued",
        "params": req.model_dump(),
        "wan_root": WAN_ROOT,
        "wan_ckpt": req.ckpt_dir or WAN_CKPT,
        "stdout_len": 0,
    }
    _write_json(paths["meta"], meta)

    # Background-Thread startet Subprozess
    def _runner():
        env = os.environ.copy()
        env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:64")
        # status: running
        meta = _read_json(paths["meta"]) or {}
        meta["status"] = "running"
        meta["started_at"] = datetime.utcnow().isoformat()+"Z"
        _write_json(paths["meta"], meta)

        with open(paths["log"], "w", encoding="utf-8") as logf:
            p = subprocess.Popen(
                _build_cmd(req), cwd=WAN_ROOT, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            stdout_accum = []
            for line in p.stdout:
                logf.write(line)
                stdout_accum.append(line)
            p.wait()
            full_out = "".join(stdout_accum)
            result_path = _parse_saved_video(full_out)

        # status: done/error
        meta = _read_json(paths["meta"]) or {}
        meta["finished_at"] = datetime.utcnow().isoformat()+"Z"
        meta["returncode"] = p.returncode
        if p.returncode == 0:
            meta["status"] = "done"
            _write_json(paths["result"], {
                "job_id": job_id,
                "video_path": result_path,
            })
        else:
            meta["status"] = "error"
        _write_json(paths["meta"], meta)

    threading.Thread(target=_runner, daemon=True).start()
    return job_id

def get_status(job_id: str) -> Dict[str, Any]:
    paths = _job_paths(job_id)
    meta = _read_json(paths["meta"])
    if not meta:
        return {"error":"job_not_found", "job_id": job_id}
    # Fortschritt (nur simpel): running = 0/1, done = 1
    prog = 1.0 if meta.get("status") == "done" else (0.0 if meta.get("status")=="queued" else 0.5)
    return {
        "job_id": job_id,
        "status": meta.get("status"),
        "progress": prog,
        "created_at": meta.get("created_at"),
        "started_at": meta.get("started_at"),
        "finished_at": meta.get("finished_at"),
        "returncode": meta.get("returncode"),
    }

def get_result(job_id: str) -> Dict[str, Any]:
    paths = _job_paths(job_id)
    meta = _read_json(paths["meta"])
    if not meta:
        return {"error":"job_not_found", "job_id": job_id}
    if meta.get("status") != "done":
        return {"error":"not_ready", "job_id": job_id, "status": meta.get("status")}
    res = _read_json(paths["result"]) or {}
    # Für RunPod-Proxy: absoluter Pfad → direkte Datei-URL anbieten ist Sache deiner App.
    return {
        "job_id": job_id,
        "status": "done",
        "video_path": res.get("video_path"),
    }
