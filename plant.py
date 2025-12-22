from fastapi import FastAPI, File, UploadFile,APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import openai
from PIL import Image
import io

# Load env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

router = APIRouter(prefix="/plant", tags=["Plant"])

# Analyze plant endpoint
@router.post("/analyze")
async def analyze_plant(file: UploadFile = File(...)):
    contents = await file.read()

    if not contents or len(contents) < 1000:
        raise HTTPException(status_code=400, detail="Empty or invalid image file")

    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # verifies integrity
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # reopen after verify
    image = Image.open(io.BytesIO(contents))

    import base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a plant disease expert."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify disease and treatment"},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{img_str}"
                        }
                    ]
                }
            ],
            temperature=0
        )

        return {"disease": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

