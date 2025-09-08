#!/usr/bin/env python3
import argparse, json, os, sys, torch, torchaudio, numpy as np
from datetime import datetime
from lightning.pytorch import seed_everything
from pathlib import Path
from ThinkSound.models import create_model_from_config
from ThinkSound.models.utils import load_ckpt_state_dict
from ThinkSound.inference.sampling import sample, sample_discrete_euler

# ----------------- args -----------------
def parse_args():
    p = argparse.ArgumentParser(prog="ThinkSound predict (clean)")
    # control
    p.add_argument("--cfg", type=float, default=3.2, help="Classifier-free guidance scale")
    p.add_argument("--steps", type=int, default=36, help="Sampling steps")
    p.add_argument("--half", action="store_true", help="Use FP16 autocast on CUDA")
    p.add_argument("--no_video_cond", action="store_true", help="Disable video conditioning")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--compile", action="store_true")
    p.add_argument("--test_batch_size", type=int, default=1)
    # io
    p.add_argument("--config", default="ThinkSound/configs/model_configs/thinksound.json")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--vae", required=True)
    p.add_argument("--synchformer", default="")  # accepted but not required here
    p.add_argument("--results-dir", default="results")
    p.add_argument("--features_dir", default="results/features")
    p.add_argument("--npz", default="", help="Explicit path to features npz")
    p.add_argument("--features-id", default="", help="Pick <features-id>.npz from features_dir")
    # text/meta
    p.add_argument("--duration-sec", type=float, default=7)
    p.add_argument("--title", default="")
    p.add_argument("--cot", default="")
    return p.parse_args()

# ----------------- helpers -----------------
def load_npz_as_metadata(npz_path, duration):
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"NPZ not found: {npz_path}")
    d = np.load(npz_path, allow_pickle=True)
    info = {k: d[k] for k in d.files}

    # Normalize arrays/objects -> tensors/strings
    for k, v in list(info.items()):
        if isinstance(v, np.ndarray):
            if v.dtype.kind in "iufb":
                info[k] = torch.from_numpy(v)
            else:
                v = v.tolist()
                info[k] = v[0] if isinstance(v, list) and len(v) == 1 else v
        elif isinstance(v, (bytes, bytearray)):
            try:
                info[k] = v.decode("utf-8", "ignore")
            except Exception:
                info[k] = str(v)
        elif not isinstance(v, (str, torch.Tensor)):
            info[k] = str(v)

    for tk in ("id", "caption", "caption_cot"):
        if tk in info and isinstance(info[tk], (list, tuple)):
            info[tk] = info[tk][0] if info[tk] else ""

    latent_len = round(44100/64/32*duration)  # matches training config
    audio = torch.zeros((1, 64, latent_len), dtype=torch.float32)
    # default: video present; may be flipped off via --no_video_cond
    info["video_exist"] = torch.tensor(True)
    return audio, info

def pick_npz(features_dir, cli_npz, cli_id):
    import csv
    # 1) Explicit path
    if cli_npz and os.path.exists(cli_npz):
        return cli_npz
    # 2) By id in features_dir
    if cli_id:
        p = os.path.join(features_dir, f"{cli_id}.npz")
        if os.path.exists(p): return p
    # 3) From CSV (repo root or alongside features_dir)
    repo_root = Path(__file__).resolve().parent
    csv_candidates = [
        os.path.join(str(repo_root), "cot_coarse", "cot.csv"),                      # demo.sh writes here
        os.path.join(os.path.dirname(features_dir), "cot_coarse", "cot.csv"),       # fallback
    ]
    for csv_path in csv_candidates:
        if os.path.exists(csv_path):
            try:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    r = csv.DictReader(f); row = next(r, None)
                    if row and "id" in row:
                        p = os.path.join(features_dir, f"{row['id']}.npz")
                        if os.path.exists(p): return p
            except Exception:
                pass
    # 4) Newest .npz in features_dir
    cands = [str(p) for p in Path(features_dir).glob("*.npz")]
    if not cands:
        raise FileNotFoundError(f"No .npz found in {features_dir}")
    return max(cands, key=os.path.getmtime)

def _load_ckpt_state(path: str):
    # safe torch.load + common prefix stripping
    try:
        ckpt = torch.load(path, map_location="cpu", weights_only=True)  # PyTorch >= 2.4
    except TypeError:
        ckpt = torch.load(path, map_location="cpu")
    state = ckpt.get("state_dict", ckpt)
    def strip(k: str):
        for p in ("module.", "ema_model.", "model.", "net."):
            if k.startswith(p): return k[len(p):]
        return k
    state = {strip(k): v for k, v in state.items()}
    # some repos expect model.model.*
    if any(k.startswith("model.") for k in state) and not any(k.startswith("model.model.") for k in state):
        state = {("model.model."+k[len("model."):]) if k.startswith("model.") else k: v for k, v in state.items()}
    return state

# ----------------- core -----------------
@torch.no_grad()
def predict_step(diffusion, batch, diffusion_objective, device='cuda:0',
                 use_autocast=False, steps=36, cfg=3.2):
    diffusion = diffusion.to(device)
    if use_autocast and str(device).startswith("cuda"):
        diffusion = diffusion.half()

    reals, metadata_list = batch
    autocast = torch.amp.autocast
    amp_enabled = use_autocast and str(device).startswith("cuda")
    amp_kwargs = dict(dtype=torch.float16, enabled=amp_enabled)

    with autocast('cuda', **amp_kwargs):
        conditioning = diffusion.conditioner(metadata_list, device)

    # Handle missing video features gracefully
    video_exist = torch.stack([m['video_exist'] for m in metadata_list], dim=0)
    if 'metaclip_features' in conditioning:
        conditioning['metaclip_features'][~video_exist] = diffusion.model.model.empty_clip_feat
    if 'sync_features' in conditioning:
        conditioning['sync_features'][~video_exist]     = diffusion.model.model.empty_sync_feat

    cond_inputs = diffusion.get_conditioning_inputs(conditioning)
    B = reals.shape[0]; L = reals.shape[2]

    model = diffusion.model
    noise_dtype = next(model.parameters()).dtype
    noise = torch.randn([B, diffusion.io_channels, L], device=device, dtype=noise_dtype)

    with autocast('cuda', **amp_kwargs):
        if diffusion_objective == "v":
            fakes = sample(model, noise, steps, 0, **cond_inputs, cfg_scale=cfg, batch_cfg=True)
        else:
            fakes = sample_discrete_euler(model, noise, steps, **cond_inputs, cfg_scale=cfg, batch_cfg=True)
        if diffusion.pretransform is not None:
            fakes = diffusion.pretransform.decode(fakes)

    audios = fakes.float()
    m = torch.max(torch.abs(audios))
    if m > 0: audios = audios / m
    return (audios.clamp(-1,1)*32767).to(torch.int16).cpu()

def main():
    args = parse_args()
    seed_everything(args.seed, workers=True)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    with open(args.config, "r", encoding="utf-8") as f:
        model_config = json.load(f)
    duration = float(args.duration_sec)
    model_config["sample_size"] = duration * model_config["sample_rate"]
    model_config["model"]["diffusion"]["config"]["sync_seq_len"]   = 24*int(duration)
    model_config["model"]["diffusion"]["config"]["clip_seq_len"]   = 8*int(duration)
    model_config["model"]["diffusion"]["config"]["latent_seq_len"] = round(44100/64/32*duration)

    diffusion = create_model_from_config(model_config)
    if args.compile: diffusion = torch.compile(diffusion)

    # checkpoint (robust)
    state = _load_ckpt_state(args.ckpt)
    info = diffusion.load_state_dict(state, strict=False)
    mk = getattr(info, "missing_keys", getattr(info, "missing", []))
    uk = getattr(info, "unexpected_keys", getattr(info, "unexpected", []))
    print(f"load_state_dict -> missing:{len(mk)} unexpected:{len(uk)}", file=sys.stderr)

    # VAE
    vae_state = load_ckpt_state_dict(args.vae, prefix='autoencoder.')
    diffusion.pretransform.load_state_dict(vae_state, strict=False)

    # features
    npz_path = pick_npz(args.features_dir, args.npz, args.features_id)
    audio, meta = load_npz_as_metadata(npz_path, duration)

    # CLI text overrides → ensure the model uses your prompt
    if args.title:
        meta["caption"] = args.title
    if args.cot:
        meta["caption_cot"] = args.cot

    # Optional: hard disable video conditioning
    if args.no_video_cond:
        meta["video_exist"] = torch.tensor(False)

    # Move tensors to device
    for k, v in list(meta.items()):
        if isinstance(v, torch.Tensor):
            meta[k] = v.to(device)

    aud = predict_step(
        diffusion,
        batch=[audio.to(device), (meta,)],
        diffusion_objective=model_config["model"]["diffusion"]["diffusion_objective"],
        device=device,
        use_autocast=bool(args.half),
        steps=args.steps,
        cfg=args.cfg,
    )

    os.makedirs(args.results_dir, exist_ok=True)
    wav1 = os.path.join(args.results_dir, "demo.wav")
    torchaudio.save(wav1, aud[0], 44100)
    print("Wrote:", wav1)
    mmdd = datetime.now().strftime("%m%d")
    dated_dir = os.path.join(args.results_dir, f"{mmdd}_batch_size{args.test_batch_size}")
    os.makedirs(dated_dir, exist_ok=True)
    wav2 = os.path.join(dated_dir, "demo.wav")
    torchaudio.save(wav2, aud[0], 44100)
    print("Wrote:", wav2)

if __name__ == "__main__":
    main()