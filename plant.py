from fastapi import FastAPI, File, UploadFile, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from openai import OpenAI
from PIL import Image
import io
import base64

# Load env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment")

client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter(prefix="/plant", tags=["Plant"])

@router.post("/analyze")
async def analyze_plant(file: UploadFile = File(...)):

    print("Received file:", file.filename, file.content_type)
    contents = await file.read()

    if not contents or len(contents) < 1000:
        raise HTTPException(status_code=400, detail="Empty or invalid image file")

    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    # Reopen image after verify
    image = Image.open(io.BytesIO(contents))
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")

    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are an agricultural disease detection API. "
                                "Respond ONLY with valid JSON. "
                                "Keys: disease_name, confidence, symptoms, "
                                "organic_treatment, chemical_treatment, prevention."
                            )
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Identify the plant disease"},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    ]
                }
            ]
        )


        result = response.output_text
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
