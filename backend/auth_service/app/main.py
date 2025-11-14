from fastapi import FastAPI

from app.api import auth as auth_router


app = FastAPI(title="Auth Service")
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Auth service is running"}
