import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Google Studio Human Voice API")

# ওয়েবসাইট থেকে ফেচ করার জন্য CORS পলিসি উন্মুক্ত রাখা
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render-এর Environment Variable থেকে সরাসরি API Key নেওয়া
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
        # ক্লায়েন্ট তৈরি
        client = genai.Client(api_key=API_KEY)

        # Google Gemini 2.5 Flash TTS মডেল কল
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=data.text.strip(),
            config=types.GenerateContentConfig(
                response_mime_type="audio/mp3",
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=data.voice_name
                        )
                    )
                ),
            ),
        )

        # প্রাপ্ত অডিও বাইট এক্সট্র্যাক্ট করা
        audio_bytes = response.candidates[0].content.parts[0].inline_data.data
        return Response(content=audio_bytes, media_type="audio/mp3")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Studio সমস্যা: {str(e)}")
