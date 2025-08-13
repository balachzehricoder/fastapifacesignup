from fastapi import FastAPI
from .database import db
from app.routes import users, userlogin
from app.routes.verify_otp import router as verify_otp_router 

app = FastAPI(
    title="Aptech Freelancing Platform API's",
    version="1.0.0",
    description="Backend API for student and company users"
)

@app.get("/")
def root():
    return {"message": "API is working 🚀"}

@app.get("/test-db")
async def test_db():
    try:
        await db.command("ping")
        return {"message": "MongoDB connected successfully ✅"}
    except Exception as e:
        return {"error": str(e)}

# Register all routers
app.include_router(users.router, prefix="/users")
app.include_router(userlogin.router, prefix="/users")
app.include_router(verify_otp_router, prefix="/users")  
