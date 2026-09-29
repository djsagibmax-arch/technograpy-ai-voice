import os
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

        # অডিও বাইট এবং সঠিক মাইম টাইপ সংগ্রহ
        audio_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                audio_part = part.inline_data
                break

        if not audio_part:
            raise HTTPException(status_code=500, detail="গুগল থেকে অডিও তৈরি হয়নি।")

        audio_bytes = audio_part.data
        mime_type = audio_part.mime_type or "audio/wav"

        return Response(content=audio_bytes, media_type=mime_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Studio সমস্যা: {str(e)}")
