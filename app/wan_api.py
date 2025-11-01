# app/wan_api.py
from pydantic import BaseModel
from typing import Optional
import os, uuid, subprocess

class TI2VRequest(BaseModel):
    prompt: str
    size: str = "384*672"          # "H*W" wie im Wan-Repo
    frame_num: int = 8
    sample_steps: int = 8
    sample_guide_scale: float = 3.0
    offload_model: bool = True
    convert_model_dtype: bool = True
    ckpt_dir: Optional[str] = None
    task: str = "ti2v-5B"          # default: 5B TI2V

def run_wan_ti2v(req: TI2VRequest) -> dict:
    wan_root = os.getenv("WAN_ROOT", "/workspace/Wan2.2")
    ckpt_dir = req.ckpt_dir or os.getenv("WAN_CKPT_DIR", "/workspace/Wan2.2/Wan2.2-TI2V-5B")

    # optional: Output-Ordner (Wan schreibt i.d.R. selbst in outputs/)
    out_dir = os.path.join(wan_root, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    _job_id = uuid.uuid4().hex

    cmd = [
        "python", os.path.join(wan_root, "generate.py"),
        "--task", req.task,
        "--ckpt_dir", ckpt_dir,
        "--prompt", req.prompt,
        "--size", req.size,
        "--frame_num", str(req.frame_num),
        "--sample_steps", str(req.sample_steps),
        "--sample_guide_scale", str(req.sample_guide_scale),
        "--offload_model", str(req.offload_model),
        "--convert_model_dtype",
    ]
    env = os.environ.copy()
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:64")

    p = subprocess.run(
        cmd, cwd=wan_root, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout,
        "job_id": _job_id,
        "wan_root": wan_root,
    }
