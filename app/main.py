from fastapi import FastAPI

from app.routers.posts import router as posts_router

app = FastAPI(title="Blog API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(posts_router)