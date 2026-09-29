from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import edge_tts
import io
import re

app = FastAPI(title="Technography AI Studio Voice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "bn-IN-BashkarNeural"  # সবচেয়ে স্পষ্ট ও ভারী কণ্ঠ
    rate: str = "-5%"                  # স্বাভাবিক মানুষের গতির মতো
    pitch: str = "-3Hz"                # কণ্ঠকে পুরুষালি ও গম্ভীর করার জন্য

@app.get("/")
def home():
    return {"status": "Technography TTS Server is Live!"}

# মানুষের মতো বিরতি (Pause) তৈরি করার ফাংশন
def build_ssml_text(text: str) -> str:
    # অপ্রয়োজনীয় বাজে চিহ্ন দূর করা
    clean = re.sub(r'[><*#_~`\[\]{}]', ' ', text)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # কমা থাকলে হালকা থামা (৩০০ms)
    clean = clean.replace(',', ' , <break time="300ms"/> ')
    clean = clean.replace(';', ' ; <break time="350ms"/> ')

    # বাক্য শেষ হলে (দাঁড়ি, প্রশ্ন বা বিস্ময়) স্বাভাবিক মানুষের মতো দম নেওয়ার বিরতি (৬৫০ms)
    clean = clean.replace('।', ' । <break time="650ms"/> ')
    clean = clean.replace('?', ' ? <break time="650ms"/> ')
    clean = clean.replace('!', ' ! <break time="650ms"/> ')
    clean = clean.replace('.', ' . <break time="650ms"/> ')

    return clean

@app.post("/generate-audio")
async def generate_audio(data: TTSRequest):
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="দয়া করে কোনো টেক্সট প্রদান করুন।")

    # অটো-পজ যুক্ত টেক্সট তৈরি
    processed_text = build_ssml_text(data.text)

    if len(processed_text) > 3000:
        raise HTTPException(status_code=400, detail="টেক্সট অনেক বড়, দয়া করে ছোট করুন।")

    try:
        # Edge TTS কমিউনিকেটর
        communicate = edge_tts.Communicate(
            text=processed_text,
            voice=data.voice,
            rate=data.rate,
            pitch=data.pitch
        )
        
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_bytes = audio_buffer.getvalue()
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="ভয়েস তৈরি হতে ব্যর্থ হয়েছে।")

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=voice.mp3"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ত্রুটি হয়েছে: {str(e)}")
