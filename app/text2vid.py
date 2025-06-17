from moviepy.editor import TextClip, CompositeVideoClip
from datetime import datetime

def generate_video(prompt: str) -> str:
    txt_clip = TextClip(prompt, fontsize=70, color='white', size=(640, 480))
    txt_clip = txt_clip.set_duration(3)

    video = CompositeVideoClip([txt_clip])
    path = f"/workspace/video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    video.write_videofile(path, fps=24)
    return path
