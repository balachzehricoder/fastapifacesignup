import cv2, easyocr, re, os, shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.models.users import UserModel
from app.database import get_database

router = APIRouter()
UPLOAD_DIR = "uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

reader = easyocr.Reader(['en'])  # ✅ Load once for better performance


def extract_cnic_data(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    img_resized = cv2.resize(img, (800, 500))

    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=30)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 12)

    text_original = " ".join(str(line) for line in reader.readtext(img_resized, detail=0))
    text_thresh = " ".join(str(line) for line in reader.readtext(thresh, detail=0))
    full_text = text_original if len(text_original) > len(text_thresh) else text_thresh

    # ✅ Extract Name (3 words before Father Name)
    name_match = re.search(r"([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)\s+Father Name", full_text)
    name = name_match.group(1) if name_match else "Name not found"

    # ✅ Extract Father Name
    father_match = re.search(r"Father Name\s*([A-Z][a-z]+\s+[A-Z][a-z]+)", full_text)
    father_name = father_match.group(1) if father_match else "Father Name not found"

    # ✅ Extract CNIC, DOB, DOI
    cnic_match = re.search(r"(\d{5}-\d{7}-\d)", full_text)
    dob_match = re.search(r"(\d{2}[./-]\d{2}[./-]\d{4})", full_text)
    doi_match = re.search(r"(\d{2}[./-]\d{2}[./-]\d{4})", full_text)

    return {
        "name": name,
        "father_name": father_name,
        "cnic": cnic_match.group(1) if cnic_match else "CNIC not found",
        "dob": dob_match.group(1) if dob_match else "DOB not found",
        "doi": doi_match.group(1) if doi_match else "DOI not found",
        "country": "Pakistan" if "PAKISTAN" in full_text.upper() else "Not Detected",
        "gender": "Male" if " M " in full_text else ("Female" if " F " in full_text else "Not Detected")
    }



@router.post("/signup")
async def signup(
    name: str = Form(...),
    email: str = Form(...),
    aptech_branch: str = Form(...),
    skills: str = Form(...),
    photo: UploadFile = File(None),
    card_front: UploadFile = File(...),
    card_back: UploadFile = File(...),
    db=Depends(get_database)
):
    user_model = UserModel(db)

    # ✅ Check if user already exists
    if await user_model.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered.")

    # ✅ Save uploaded files
    def save_file(file: UploadFile):
        if not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
        path = os.path.join(UPLOAD_DIR, file.filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return path

    photo_path = save_file(photo) if photo and photo.filename else None
    front_path = save_file(card_front)
    back_path = save_file(card_back)

    # ✅ OCR Extraction from CNIC front
    ocr_data = extract_cnic_data(front_path)

    if not ocr_data["name"] and not ocr_data["cnic"]:
        raise HTTPException(status_code=400, detail="OCR failed to extract CNIC data.")

    # ✅ Prepare final user data (No name match validation)
    user_data = {
        "name": name,
        "email": email,
        "aptech_branch": aptech_branch,
        "skills": [s.strip() for s in skills.split(",")],
        "photo": photo_path,
        "card_front": front_path,
        "card_back": back_path,
        # ✅ Store OCR extracted data
        "ocr_name": ocr_data["name"],
        "ocr_father_name": ocr_data["father_name"],
        "ocr_cnic": ocr_data["cnic"],
        "ocr_dob": ocr_data["dob"],
        "ocr_doi": ocr_data["doi"],
        "ocr_country": ocr_data["country"],
        "ocr_gender": ocr_data["gender"]
    }

    user_id = await user_model.create_user(user_data)

    return {
        "status": "success",
        "user_id": user_id,
        "ocr_data": ocr_data
    }
