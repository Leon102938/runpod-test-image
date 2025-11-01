# /workspace/app/wan_api.py
import os, shlex, subprocess, uuid, pathlib

WAN_ROOT = "/workspace/Wan2.2"
DEFAULT_CKPT = os.getenv("WAN_CKPT_DIR", "/workspace/Wan2.2-TI2V-5B")

def run_wan_ti2v(
    prompt: str,
    size: str = "704*1280",
    frame_num: int = 16,
    sample_steps: int = 12,
    sample_guide_scale: float = 3.0,
    offload_model: bool = True,
    convert_model_dtype: bool = True,
    task: str = "ti2v-5B",
    env: dict | None = None,
) -> dict:
    """
    Ruft Wan2.2 generate.py als Subprozess auf und gibt Pfad/Log zurück.
    """
    assert os.path.isdir(WAN_ROOT), f"WAN_ROOT nicht gefunden: {WAN_ROOT}"
    assert os.path.isdir(DEFAULT_CKPT), f"Checkpoint-Ordner fehlt: {DEFAULT_CKPT}"

    # Log-Datei pro Run
    run_id = str(uuid.uuid4())[:8]
    logs_dir = "/workspace/logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_path = f"{logs_dir}/wan_{run_id}.log"

    # CLI bauen
    cmd = [
        "python", f"{WAN_ROOT}/generate.py",
        "--task", task,
        "--ckpt_dir", DEFAULT_CKPT,
        "--prompt", prompt,
        "--size", size,
        "--frame_num", str(frame_num),
        "--sample_steps", str(sample_steps),
        "--sample_guide_scale", str(sample_guide_scale),
    ]
    if offload_model:
        cmd.append("--offload_model")
    if convert_model_dtype:
        cmd.append("--convert_model_dtype")

    # Optionales, schlankes CUDA-Alloc-Tuning (gegen Fragmentierung)
    base_env = os.environ.copy()
    base_env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:64")
    base_env.setdefault("TORCH_BACKENDS_MATMUL_ALLOW_TF32", "1")
    if env:
        base_env.update(env)

    with open(log_path, "w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=lf, cwd=WAN_ROOT)

    # Output-Datei nach Konvention: generate.py speichert ins WAN-Repo (z. B. out/*.mp4)
    # Wir geben hier nur die Run-ID + Log zurück. Der Client kann Polling machen / Log einsehen.
    return {"run_id": run_id, "log": log_path, "status": "started"}
