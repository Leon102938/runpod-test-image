from prefigure.prefigure import get_all_args, push_wandb_config
import json
import os
import re
import torch
import torchaudio
import subprocess, shlex   # <- für FFmpeg-Muxing hinzugefügt
from lightning.pytorch import seed_everything
import random
from datetime import datetime
import numpy as np
from ThinkSound.models import create_model_from_config
from ThinkSound.models.utils import load_ckpt_state_dict, remove_weight_norm_from_model
from ThinkSound.inference.sampling import sample, sample_discrete_euler
from pathlib import Path

# --- FFmpeg-Muxing Helper (NEU) ---
def _mux_to_mp4(video_path: str, audio_path: str, out_mp4: str):
    cmd = (
        f'ffmpeg -y '
        f'-i {shlex.quote(video_path)} '
        f'-i {shlex.quote(audio_path)} '
        f'-c:v copy -map 0:v:0 -map 1:a:0 -shortest '
        f'-c:a aac -b:a 192k -ar 48000 -ac 2 '
        f'-movflags +faststart '
        f'{shlex.quote(out_mp4)}'
    )
    subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_mp4
# -----------------------------------

def predict_step(diffusion, batch, diffusion_objective, device='cuda:0'):
    diffusion = diffusion.to(device)

    reals, metadata = batch
    ids = [item['id'] for item in metadata]
    batch_size, length = reals.shape[0], reals.shape[2]
    print(f"Predicting {batch_size} samples with length {length} for ids: {ids}")
    with torch.amp.autocast('cuda'):
        conditioning = diffusion.conditioner(metadata, device)
    
    video_exist = torch.stack([item['video_exist'] for item in metadata],dim=0)
    conditioning['metaclip_features'][~video_exist] = diffusion.model.model.empty_clip_feat
    conditioning['sync_features'][~video_exist] = diffusion.model.model.empty_sync_feat

    cond_inputs = diffusion.get_conditioning_inputs(conditioning)
    if batch_size > 1:
        noise_list = []
        for _ in range(batch_size):
            noise_1 = torch.randn([1, diffusion.io_channels, length]).to(device)
            noise_list.append(noise_1)
        noise = torch.cat(noise_list, dim=0)
    else:
        noise = torch.randn([batch_size, diffusion.io_channels, length]).to(device)

    with torch.amp.autocast('cuda'):

        model = diffusion.model
        if diffusion_objective == "v":
            fakes = sample(model, noise, 24, 0, **cond_inputs, cfg_scale=5, batch_cfg=True)
        elif diffusion_objective == "rectified_flow":
            import time
            start_time = time.time()
            fakes = sample_discrete_euler(model, noise, 24, **cond_inputs, cfg_scale=5, batch_cfg=True)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"执行时间: {execution_time:.2f} 秒")
        if diffusion.pretransform is not None:
            fakes = diffusion.pretransform.decode(fakes)

    audios = fakes.to(torch.float32).div(torch.max(torch.abs(fakes))).clamp(-1, 1).mul(32767).to(torch.int16).cpu()
    return audios

def load_file(filename, info, latent_length):
    npz_file = filename
    if os.path.exists(npz_file): 
        npz_data = np.load(npz_file,allow_pickle=True)
        data = {key: npz_data[key] for key in npz_data.files}
        for key in data.keys():
            if isinstance(data[key], np.ndarray) and np.issubdtype(data[key].dtype, np.number):
                data[key] = torch.from_numpy(data[key])
    else:
        raise ValueError(f'error load file: {filename}')
    info.update(data)
    audio = torch.zeros((1, 64, latent_length), dtype=torch.float32)
    info['video_exist'] = torch.tensor(True)
    return audio, info['metaclip_features']

def load(filename,duration):
    assert os.path.exists(filename)
    info = {}
    audio, video = load_file(filename, info, round(44100/64/32*duration))
    info["path"] = filename

    info['id'] = Path(filename).stem
    info["relpath"] = 'demo.npz'

    return (audio, info)

def main():

    args = get_all_args()

    if (args.save_dir == ''):
        args.save_dir=args.results_dir

    seed = args.seed

    if os.environ.get("SLURM_PROCID") is not None:
        seed += int(os.environ.get("SLURM_PROCID"))

    seed_everything(seed, workers=True)

    if args.model_config == '':
        args.model_config = "ThinkSound/configs/model_configs/thinksound.json"
    with open(args.model_config) as f:
        model_config = json.load(f)

    duration=(float)(args.duration_sec)
    
    model_config["sample_size"] = duration * model_config["sample_rate"]
    model_config["model"]["diffusion"]["config"]["sync_seq_len"] = 24*int(duration)
    model_config["model"]["diffusion"]["config"]["clip_seq_len"] = 8*int(duration)
    model_config["model"]["diffusion"]["config"]["latent_seq_len"] = round(44100/64/32*duration)

    model = create_model_from_config(model_config)

    if args.compile:
        model = torch.compile(model)

    model.load_state_dict(torch.load(args.ckpt_dir))

    load_vae_state = load_ckpt_state_dict(args.pretransform_ckpt_path, prefix='autoencoder.') 
    model.pretransform.load_state_dict(load_vae_state)

    audio,meta=load(os.path.join(args.results_dir, "demo.npz") , duration)
    
    for k, v in meta.items():
        if isinstance(v, torch.Tensor):
            meta[k] = v.to('cuda:0')

    audio = predict_step(
        model, 
        batch=[audio,(meta,)],
        diffusion_objective=model_config["model"]["diffusion"]["diffusion_objective"], 
        device='cuda:0'
    )

    current_date = datetime.now()
    formatted_date = current_date.strftime('%m%d')
    
    audio_dir = os.path.join(args.save_dir, f'{formatted_date}_batch_size{args.test_batch_size}')
    os.makedirs(audio_dir, exist_ok=True)

    # sample_id aus ENV (von API), fallback "demo"
    sample_id = os.environ.get("TS_SAMPLE_ID") or "demo"
    audio_path = os.path.join(audio_dir, f"{sample_id}.wav")
    torchaudio.save(audio_path, audio[0], 44100)

    # Auto-Muxing: Quelle aus ENV, sonst Fallback auf demo.mp4
    src_video = os.environ.get("TS_SOURCE_VIDEO")
    if not src_video or not os.path.exists(src_video):
        candidate = "/workspace/ThinkSound/videos/demo.mp4"
        if os.path.exists(candidate):
            src_video = candidate

    if src_video and os.path.exists(src_video):
        try:
            # MP4 immer als <sample_id>_aud.mp4 speichern
            mp4_path = os.path.join(audio_dir, f"{sample_id}_aud.mp4")
            out_mp4 = _mux_to_mp4(src_video, audio_path, mp4_path)
            print(f"🎬 Muxed video written: {out_mp4}")
        except Exception as e:
            print(f"⚠️ FFmpeg mux failed: {e}")

    #trainer.predict(training_wrapper, dm, return_predictions=False)

if __name__ == '__main__':
    main()