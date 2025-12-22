from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from random import randint
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.rest import Client
from plant import router as plant_analysis_router
import os

# Load environment variables from .env
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

# Initialize Twilio client
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

app = FastAPI(title="OTP Login API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(plant_analysis_router)

# In-memory OTP store (for production use Redis or DB)
otp_store = {}

# Request models
class MobileNumberRequest(BaseModel):
    mobileNumber: str

class OTPRequest(BaseModel):
    mobileNumber: str
    otp: str

# Helper to generate 6-digit OTP
def generate_otp() -> str:
    return f"{randint(100000, 999999)}"

# Function to send OTP via Twilio
def send_otp_sms(mobile: str, otp: str):
    try:
        print(mobile)
        message = client.messages.create(
            body=f"Your OTP is {otp}",
            from_=TWILIO_PHONE,
            to=f"+91{mobile}"  # adjust country code
        )
        print(f"Twilio message sent: SID={message.sid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

# Send OTP endpoint
@app.post("/send-otp")
async def send_otp(request: MobileNumberRequest):
    mobile = request.mobileNumber
    if len(mobile) != 10 or not mobile.isdigit():
        raise HTTPException(status_code=400, detail="Invalid mobile number")

    try:
        print(f"+91{mobile}")
        verification = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=f"+91{mobile}",
            channel="sms"
        )
        print(f"Twilio Verify OTP SID: {verification.sid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"success": True, "message": f"OTP sent to {mobile}"}


# Verify OTP endpoint
@app.post("/verify-otp")
async def verify_otp(request: OTPRequest):
    mobile = request.mobileNumber
    otp_input = request.otp

    try:
        verification_check = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=f"+91{mobile}",
            code=otp_input
        )
        if verification_check.status == "approved":
            return {"success": True, "message": "OTP verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


# Resend OTP endpoint
@app.post("/resend-otp")
async def resend_otp(request: MobileNumberRequest):
    mobile = request.mobileNumber
    if len(mobile) != 10 or not mobile.isdigit():
        raise HTTPException(status_code=400, detail="Invalid mobile number")

    try:
        verification = client.verify.v2.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=f"+91{mobile}",  # user's mobile number with country code
            channel="sms"
        )
        print(f"Twilio Verify OTP sent: SID={verification.sid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resend OTP: {str(e)}")

    return {"success": True, "message": f"OTP resent to {mobile}"}
