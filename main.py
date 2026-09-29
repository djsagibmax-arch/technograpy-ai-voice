from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import edge_tts
import io

app = FastAPI(title="Technography AI Voice API")

# ফ্রন্টএন্ড যাতে ব্যাকএন্ডে রিকোয়েস্ট পাঠাতে পারে (CORS সমাধান)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# রিকোয়েস্ট ডেটা ফরম্যাট
class TTSRequest(BaseModel):
    text: str
    voice: str = "bn-BD-PradeepNeural"

@app.get("/")
def home():
    return {"status": "Technography TTS Server is Live & Running!"}

@app.post("/generate-audio")
async def generate_audio(data: TTSRequest):
    # টেক্সট ভ্যালিডেশন
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="দয়া করে কোনো টেক্সট প্রদান করুন।")

    # ক্যারেক্টার লিমিট (ফ্রি সার্ভার ক্র্যাশ হওয়া প্রতিরোধে)
    if len(data.text) > 1500:
        raise HTTPException(
            status_code=400, 
            detail="টেক্সট অনেক বড়! অনুগ্রহ করে ১,৫০০ অক্ষরের মধ্যে রাখুন।"
        )

    try:
        # Edge TTS কমিউনিকেটর তৈরি
        communicate = edge_tts.Communicate(text=data.text.strip(), voice=data.voice)
        
        # অডিও সরাসরি মেমোরিতে (RAM) রাখা যাতে ডিস্কে অতিরিক্ত ফাইল জমা না হয়
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        # সরাসরি ব্রাউজারে অডিও স্ট্রিম পাঠানো
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
