from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from collections import defaultdict
import logging
from twilio.rest import Client
from app.db.session import async_session
from sqlalchemy.future import select

from app.core.logging import setup_logging
from app.core.request_id import RequestIDMiddleware
from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, get_current_user_id
from app.db.models.users import User
from app.db.models.user_sessions import UserSession
from app.routers.plant import router as plant_router
from app.routers.products import router as products_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router
from app.routers.admin import router as admin_router
from app.db.session import engine
from app.db.base import Base

# --- SETTINGS & LOGGER ---
settings = get_settings()
setup_logging("INFO")
logger = logging.getLogger(__name__)
logger.info("Starting AgriCure backend")

# --- TWILIO CLIENT ---
client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)

# --- APP INIT ---
app = FastAPI(title=settings.APP_NAME)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in PROD
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(plant_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(admin_router) 
# --- RATE LIMIT STORAGE (in-memory, replace with Redis for prod) ---
otp_request_counts = defaultdict(list)
OTP_LIMIT = 3  # Max 3 requests per hour
OTP_WINDOW = timedelta(hours=1)

# --- REQUEST MODELS ---
class MobileNumberRequest(BaseModel):
    mobileNumber: str

class OTPRequest(BaseModel):
    mobileNumber: str
    otp: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# --- OTP / AUTH ROUTES ---

@app.post("/auth/admin-login")
async def admin_login(request: MobileNumberRequest):
    """
    Admin login endpoint - bypasses OTP for admin users
    Only works for predefined admin phone numbers
    """
    mobile = request.mobileNumber
    
    # Admin phone numbers (should be in environment variables in production)
    ADMIN_PHONES = ["9999999999", "8888888888"]  # Replace with actual admin numbers
    
    if mobile not in ADMIN_PHONES:
        raise HTTPException(status_code=403, detail="Not an admin user")
    
    async with async_session() as session:
        # Upsert user
        result = await session.execute(select(User).where(User.phone == mobile))
        user: User | None = result.scalar_one_or_none()

        if not user:
            user = User(phone=mobile, name="Admin")
            session.add(user)
            await session.commit()
            await session.refresh(user)
        elif not user.is_active:
            user.is_active = True
            await session.commit()

        # Create refresh token
        refresh_token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)
        user_session = UserSession(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at
        )
        session.add(user_session)
        await session.commit()

        # Generate access token
        access_token = create_access_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "name": user.name,
            "language": user.language
        }
    }

@app.post("/auth/request-otp")
async def request_otp(request: MobileNumberRequest):
    mobile = request.mobileNumber
    if len(mobile) != 10 or not mobile.isdigit():
        raise HTTPException(status_code=400, detail="Invalid mobile number")

    # Rate limit
    now = datetime.utcnow()
    otp_request_counts[mobile] = [ts for ts in otp_request_counts[mobile] if now - ts < OTP_WINDOW]
    if len(otp_request_counts[mobile]) >= OTP_LIMIT:
        raise HTTPException(status_code=429, detail="Too many OTP requests. Try later.")
    otp_request_counts[mobile].append(now)

    try:
        client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=f"+91{mobile}",
            channel="sms"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"success": True, "message": f"OTP sent to {mobile}"}


@app.post("/auth/verify-otp")
async def verify_otp(request: OTPRequest):
    mobile = request.mobileNumber
    otp_input = request.otp

    # Twilio verification
    try:
        verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=f"+91{mobile}",
            code=otp_input
        )
        if verification_check.status != "approved":
            raise HTTPException(status_code=400, detail="Invalid OTP")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

    async with async_session() as session:
        # Upsert user
        result = await session.execute(select(User).where(User.phone == mobile))
        user: User | None = result.scalar_one_or_none()

        if not user:
            user = User(phone=mobile)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        elif not user.is_active:
            user.is_active = True
            await session.commit()

        # Create refresh token
        refresh_token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)
        user_session = UserSession(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at
        )
        session.add(user_session)
        await session.commit()

        # Generate access token
        access_token = create_access_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "phone": user.phone,
            "name": user.name,
            "language": user.language
        }
    }

@app.post("/auth/refresh")
async def refresh_token(request: RefreshTokenRequest):
    async with async_session() as session:
        result = await session.execute(
            select(UserSession).where(UserSession.token == request.refresh_token)
        )
        session_obj: UserSession | None = result.scalar_one_or_none()
        if not session_obj or session_obj.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Generate new access token
        access_token = create_access_token(subject=session_obj.user_id)
        return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout")
async def logout(request: RefreshTokenRequest):
    async with async_session() as session:
        result = await session.execute(
            select(UserSession).where(UserSession.token == request.refresh_token)
        )
        session_obj: UserSession | None = result.scalar_one_or_none()
        if session_obj:
            await session.delete(session_obj)
            await session.commit()
    return {"success": True, "message": "Logged out successfully"}

class UpdateUserRequest(BaseModel):
    language: str | None = None
    name: str | None = None

@app.put("/auth/user")
async def update_user(
    request: UpdateUserRequest,
    user_id: str = Depends(get_current_user_id)
):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == UUID(user_id)))
        user: User | None = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if request.language is not None:
            user.language = request.language
        if request.name is not None:
            user.name = request.name
        
        await session.commit()
        await session.refresh(user)
        
        return {
            "id": str(user.id),
            "phone": user.phone,
            "name": user.name,
            "language": user.language
        }

# --- STARTUP / SHUTDOWN ---
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("API started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("API shutdown")
