#!/usr/bin/env python3
import argparse, json, os, torch, torchaudio, numpy as np
from datetime import datetime
from lightning.pytorch import seed_everything
from pathlib import Path
from ThinkSound.models import create_model_from_config
from ThinkSound.models.utils import load_ckpt_state_dict
from ThinkSound.inference.sampling import sample, sample_discrete_euler

def parse_args():
    p = argparse.ArgumentParser(prog="ThinkSound predict (clean)")
    p.add_argument("--config", default="ThinkSound/configs/model_configs/thinksound.json")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--vae", required=True)
    p.add_argument("--synchformer", default="")
    p.add_argument("--results-dir", default="results")
    p.add_argument("--features_dir", default="results/features")
    p.add_argument("--duration-sec", type=float, default=7)
    p.add_argument("--title", default="")
    p.add_argument("--cot", default="")
    p.add_argument("--half", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--compile", action="store_true")
    p.add_argument("--test_batch_size", type=int, default=1)
    return p.parse_args()

def load_npz_as_metadata(npz_path, duration):
    import numpy as np, torch, os
    from pathlib import Path
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"NPZ not found: {npz_path}")
    d = np.load(npz_path, allow_pickle=True)
    info = {k: d[k] for k in d.files}
    # Nur numerische Arrays -> Tensor; Strings/Objekte bleiben Python
    for k, v in list(info.items()):
        if isinstance(v, np.ndarray):
            if v.dtype.kind in "iufb":       # int/uint/float/bool
                info[k] = torch.from_numpy(v)
            else:                             # string/object etc.
                info[k] = v.tolist()
                if isinstance(info[k], list) and len(info[k]) == 1:
                    info[k] = info[k][0]
    # Sicherstellen, dass Textfelder Strings sind
    for tk in ("id", "caption", "caption_cot"):
        if tk in info and isinstance(info[tk], (list, tuple)):
            info[tk] = info[tk][0] if info[tk] else ""
        if tk in info and not isinstance(info[tk], str):
            info[tk] = str(info[tk])
    latent_len = round(44100/64/32*duration)
    audio = torch.zeros((1, 64, latent_len), dtype=torch.float32)
    info["video_exist"] = torch.tensor(True)
    return audio, info

@torch.no_grad()
def predict_step(diffusion, batch, diffusion_objective, device='cuda:0'):
    diffusion = diffusion.to(device)
    reals, metadata_list = batch
    with torch.amp.autocast('cuda'):
        conditioning = diffusion.conditioner(metadata_list, device)
    video_exist = torch.stack([m['video_exist'] for m in metadata_list], dim=0)
    conditioning['metaclip_features'][~video_exist] = diffusion.model.model.empty_clip_feat
    conditioning['sync_features'][~video_exist]     = diffusion.model.model.empty_sync_feat
    cond_inputs = diffusion.get_conditioning_inputs(conditioning)
    B = reals.shape[0]; L = reals.shape[2]
    noise = torch.randn([B, diffusion.io_channels, L], device=device)
    with torch.amp.autocast('cuda'):
        model = diffusion.model
        if diffusion_objective == "v":
            fakes = sample(model, noise, 24, 0, **cond_inputs, cfg_scale=5, batch_cfg=True)
        else:
            fakes = sample_discrete_euler(model, noise, 24, **cond_inputs, cfg_scale=5, batch_cfg=True)
        if diffusion.pretransform is not None:
            fakes = diffusion.pretransform.decode(fakes)
    audios = fakes.to(torch.float32)
    m = torch.max(torch.abs(audios))
    if m > 0: audios = audios / m
    return (audios.clamp(-1,1)*32767).to(torch.int16).cpu()

def main():
    args = parse_args()
    seed_everything(args.seed, workers=True)
    with open(args.config, "r", encoding="utf-8") as f:
        model_config = json.load(f)
    duration = float(args.duration_sec)
    model_config["sample_size"] = duration * model_config["sample_rate"]
    model_config["model"]["diffusion"]["config"]["sync_seq_len"]   = 24*int(duration)
    model_config["model"]["diffusion"]["config"]["clip_seq_len"]   = 8*int(duration)
    model_config["model"]["diffusion"]["config"]["latent_seq_len"] = round(44100/64/32*duration)
    diffusion = create_model_from_config(model_config)
    if args.compile: diffusion = torch.compile(diffusion)

    # Haupt-Checkpoint robust
    ckpt = torch.load(args.ckpt, map_location="cpu")
    if isinstance(ckpt, dict) and "state_dict" in ckpt: ckpt = ckpt["state_dict"]
    if any(k.startswith("module.") for k in ckpt): ckpt = { (k[7:] if k.startswith("module.") else k): v for k,v in ckpt.items() }
    if any(k.startswith("model.") for k in ckpt) and not any(k.startswith("model.model.") for k in ckpt):
        ckpt = { ("model.model."+k[len("model."):]) if k.startswith("model.") else k : v for k,v in ckpt.items() }
    missing, unexpected = diffusion.load_state_dict(ckpt, strict=False)
    print(f"load_state_dict -> missing:{len(missing)} unexpected:{len(unexpected)}")

    # VAE
    vae_state = load_ckpt_state_dict(args.vae, prefix='autoencoder.')
    diffusion.pretransform.load_state_dict(vae_state, strict=False)

    # Features
    npz_path = os.path.join(args.features_dir, "demo.npz")
    if not os.path.exists(npz_path):
        cands = list(Path(args.features_dir).glob("*.npz"))
        if not cands: raise FileNotFoundError(f"No .npz found in {args.features_dir}")
        npz_path = str(cands[0])

    audio, meta = load_npz_as_metadata(npz_path, duration)
    for k,v in list(meta.items()):
        if isinstance(v, torch.Tensor): meta[k] = v.to('cuda:0')

    aud = predict_step(diffusion, batch=[audio.to('cuda:0'), (meta,)],
                       diffusion_objective=model_config["model"]["diffusion"]["diffusion_objective"],
                       device='cuda:0')

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
