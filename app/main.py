from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from random import randint
from datetime import datetime, timedelta
from twilio.rest import Client
from app.routers.plant import router as plant_analysis_router
from app.health.router import router as health_router
import logging
from app.core.logging import setup_logging
from app.core.request_id import RequestIDMiddleware
from app.core.config import get_settings

import os

# Load environment variables from .env
settings = get_settings()
setup_logging("INFO")

logger = logging.getLogger(__name__)
logger.info("Starting AgriCure backend")


# Initialize Twilio client
client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    RequestIDMiddleware
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #tighten in PROD
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(plant_analysis_router)

# In-memory OTP store (for production use Redis or DB)
otp_store = {}

# Request models
class MobileNumberRequest(BaseModel):
    mobileNumber: str

class OTPRequest(BaseModel):
    mobileNumber: str
    otp: str

# Send OTP endpoint
@app.post("/send-otp")
async def send_otp(request: MobileNumberRequest):
    mobile = request.mobileNumber

    if len(mobile) != 10 or not mobile.isdigit():
        raise HTTPException(status_code=400, detail="Invalid mobile number")

    try:
        client.verify.v2.services(
            settings.TWILIO_VERIFY_SERVICE_SID
        ).verifications.create(
            to=f"+91{mobile}",
            channel="sms"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"success": True, "message": f"OTP sent to {mobile}"}


# Verify OTP endpoint
@app.post("/verify-otp")
async def verify_otp(request: OTPRequest):
    mobile = request.mobileNumber
    otp_input = request.otp

    try:
        verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
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
        verification = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=f"+91{mobile}",  # user's mobile number with country code
            channel="sms"
        )
        print(f"Twilio Verify OTP sent: SID={verification.sid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resend OTP: {str(e)}")

    return {"success": True, "message": f"OTP resent to {mobile}"}


@app.on_event("startup")
async def startup():
    logger.info("API started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("API shutdown")
