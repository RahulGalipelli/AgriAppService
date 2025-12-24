# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from twilio.rest import Client
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.db.models.auth import User, UserSession

settings = get_settings()
client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)

router = APIRouter(prefix="/auth", tags=["auth"])

# ----- Request Models -----
class MobileRequest(BaseModel):
    mobileNumber: str

class OTPVerifyRequest(BaseModel):
    mobileNumber: str
    otp: str

class RefreshRequest(BaseModel):
    refresh_token: str

# ----- Endpoints -----

@router.post("/request-otp")
async def request_otp(request: MobileRequest):
    mobile = request.mobileNumber
    if len(mobile) != 10 or not mobile.isdigit():
        raise HTTPException(status_code=400, detail="Invalid mobile number")

    try:
        client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=f"+91{mobile}",
            channel="sms"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"success": True, "message": f"OTP sent to {mobile}"}


@router.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    mobile = request.mobileNumber
    otp_input = request.otp

    # Verify OTP with Twilio
    verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
        to=f"+91{mobile}", code=otp_input
    )

    if verification_check.status != "approved":
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Upsert user
    user = db.query(User).filter(User.phone == mobile).first()
    if not user:
        user = User(phone=mobile)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create session (refresh token)
    refresh_token = str(uuid4())
    session = UserSession(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(session)
    db.commit()

    # Create access token with JWT util
    access_token = create_access_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user.id
    }


@router.post("/refresh")
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(
        UserSession.token == request.refresh_token,
        UserSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token = create_access_token(subject=session.user_id)
    return {"access_token": access_token}


@router.post("/logout")
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(
        UserSession.token == request.refresh_token
    ).first()
    if session:
        db.delete(session)
        db.commit()

    return {"success": True, "message": "Logged out successfully"}
