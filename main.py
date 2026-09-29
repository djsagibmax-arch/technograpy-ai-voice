from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import edge_tts
import io
import re

app = FastAPI(title="Technography AI Voice API")

# CORS সমাধান (সব ডোমেইন থেকে অ্যাক্সেস অনুমোদিত)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# রিকোয়েস্ট মডেল
class TTSRequest(BaseModel):
    text: str
    voice: str = "bn-IN-BashkarNeural"  # ডিফল্ট সুপার ন্যাচারাল ভয়েস
    rate: str = "-4%"                  # ন্যাচারাল স্পিড
    pitch: str = "+0Hz"                # স্বাভাবিক পিচ

@app.get("/")
def home():
    return {"status": "Technography TTS Server is Live & Running!"}

@app.post("/generate-audio")
async def generate_audio(data: TTSRequest):
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="দয়া করে কোনো টেক্সট প্রদান করুন।")

    # রোবোটিক ভাব দূর করতে বিশেষ চিহ্ন ক্লিন করা (যেমন >, <, *, #, _ ইত্যাদি)
    cleaned_text = re.sub(r'[><*#_~`\[\]{}]', ' ', data.text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    if len(cleaned_text) > 2000:
        raise HTTPException(status_code=400, detail="টেক্সট ২,০০০ অক্ষরের মধ্যে রাখুন।")

    try:
        # ন্যাচারাল স্পিড ও পিচ দিয়ে ভয়েস তৈরি
        communicate = edge_tts.Communicate(
            text=cleaned_text,
            voice=data.voice,
            rate=data.rate,
            pitch=data.pitch
        )
        
        # মেমোরিতে (RAM) অডিও সংরক্ষণ
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
