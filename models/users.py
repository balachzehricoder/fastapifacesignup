from typing import Optional
from bson import ObjectId

class UserModel:
    def __init__(self, db):
        self.collection = db["users"]

    async def create_user(self, user_data: dict) -> str:
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        user = await self.collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def get_user_by_cnic(self, cnic: str) -> Optional[dict]:
        user = await self.collection.find_one({"ocr_cnic": cnic})
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def save_otp(self, user_id: str, otp: int):
        """ Save OTP temporarily in DB """
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"login_otp": otp}}
        )

    async def verify_otp(self, email: str, otp: int) -> Optional[dict]:
        """ Verify OTP and remove it after success """
        user = await self.collection.find_one({"email": email, "login_otp": otp})
        if user:
            await self.collection.update_one(
                {"_id": ObjectId(user["_id"])},
                {"$unset": {"login_otp": ""}}
            )
            user["_id"] = str(user["_id"])
            return user
        return None
