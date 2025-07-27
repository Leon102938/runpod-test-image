# 🚀 FASTAPI SERVER – FÜR Wan2.1(mini)-2 + text2vid + thinksound

# 📦 IMPORTS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os
import io
import base64
import imageio

# ✅ .env laden & BASE_URL setzen
load_dotenv("/workspace/.env")
BASE_URL = os.getenv("BASE_URL", "https://YOURPOD-8000.proxy.runpod.net")

# 🧠 IMPORTIERE TOOLS



# 🚀 INITIALISIERE FASTAPI
app = FastAPI()

# 📂 DYNAMISCHER OUTPUT-PFAD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))                    # → /workspace/app
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../output"))       # → /workspace/output

# 🛠️ Debug-Ausgabe
print("📂 BASE_DIR:", BASE_DIR)
print("📂 OUTPUT_DIR:", OUTPUT_DIR)
if os.path.exists(OUTPUT_DIR):
    print("📁 OUTPUT-Dateien:", os.listdir(OUTPUT_DIR))
else:
    print("⚠️  OUTPUT-Ordner fehlt!")

# 📂 MOUNTE BILDAUSGABE
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

# 📄 DATENSTRUKTUR 

# 🔁 ENDPOINT


