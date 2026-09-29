import os
import wave
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Google Studio Human Voice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("GEMINI_API_KEY")

class VoiceRequest(BaseModel):
    text: str
    voice_name: str = "Puck"

@app.get("/")
def home():
    return {"status": "Google Studio Natural Voice Server is Active!"}

@app.post("/generate-audio")
def generate_audio(data: VoiceRequest):
    if not API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Render Environment-এ 'GEMINI_API_KEY' পাওয়া যায়নি।"
        )

    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="দয়া করে টেক্সট লিখুন।")

    try:
        client = genai.Client(api_key=API_KEY)

        # অডিও মোডালিটি দিয়ে রিকোয়েস্ট
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=data.text.strip(),
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=data.voice_name
                        )
                    )
                ),
            ),
        )

        audio_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                audio_part = part.inline_data
                break

        if not audio_part:
            raise HTTPException(status_code=500, detail="গুগল থেকে অডিও ডাটা পাওয়া যায়নি।")

        raw_pcm_data = audio_part.data

        # কাঁচা PCM অডিওকে প্লে-যোগ্য স্ট্যান্ডার্ড WAV ফরম্যাটে রূপান্তর
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)        # মোনো অডিও
            wav_file.setsampwidth(2)       # ১৬-বিট
            wav_file.setframerate(24000)   # গুগলের স্ট্যান্ডার্ড ২৪kHz রেট
            wav_file.writeframes(raw_pcm_data)

        wav_bytes = wav_buffer.getvalue()

        return Response(content=wav_bytes, media_type="audio/wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Studio সমস্যা: {str(e)}")
