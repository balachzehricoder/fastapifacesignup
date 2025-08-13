import os, shutil, random, face_recognition
from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException, File
from app.models.users import UserModel
from app.database import get_database
from app.utils.email_sender import send_otp_email

router = APIRouter()
UPLOAD_DIR = "uploads/selfies"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def compare_faces(registered_photo, uploaded_photo):
    try:
        reg_img = face_recognition.load_image_file(registered_photo)
        up_img = face_recognition.load_image_file(uploaded_photo)

        reg_encs = face_recognition.face_encodings(reg_img)
        up_encs = face_recognition.face_encodings(up_img)

        if not reg_encs or not up_encs:
            return False

        return face_recognition.compare_faces([reg_encs[0]], up_encs[0])[0]
    except:
        return False

def mask_email(email):
    parts = email.split("@")
    masked = parts[0][:3] + "****" + parts[0][-1] if len(parts[0]) > 4 else parts[0][:1] + "****"
    return masked + "@" + parts[1]

@router.post("/login-cnic")
async def login_with_cnic(
    cnic: str = Form(...),
    selfie: UploadFile = File(...),
    db=Depends(get_database)
):
    user_model = UserModel(db)
    user = await user_model.get_user_by_cnic(cnic)

    if not user:
        raise HTTPException(status_code=404, detail="CNIC not found")

    selfie_path = os.path.join(UPLOAD_DIR, selfie.filename)
    with open(selfie_path, "wb") as f:
        shutil.copyfileobj(selfie.file, f)

    is_match = compare_faces(user["photo"], selfie_path)
    os.remove(selfie_path)

    if not is_match:
        raise HTTPException(status_code=401, detail="Face verification failed")

    otp = random.randint(100000, 999999)
    await user_model.save_otp(user["_id"], otp)

    send_otp_email(user["email"], otp)

    return {
        "status": "pending_verification",
        "masked_email": mask_email(user["email"]),
        "message": "OTP sent to your email"
    }
