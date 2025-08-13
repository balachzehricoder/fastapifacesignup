from fastapi import APIRouter, Form, Depends, HTTPException
from app.models.users import UserModel
from app.database import get_database

router = APIRouter()

@router.post("/verify-otp")
async def verify_otp(
    email: str = Form(...),
    otp: int = Form(...),
    db=Depends(get_database)
):
    user_model = UserModel(db)
    user = await user_model.verify_otp(email, otp)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "name": user["name"],
            "email": user["email"],
            "cnic": user["ocr_cnic"]
        }
    }
