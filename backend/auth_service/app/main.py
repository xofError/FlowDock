from fastapi import FastAPI

app = FastAPI(title="Auth Service")


@app.get("/")
async def root():
    return {"message": "Auth service is running"}
