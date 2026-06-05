from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.documents import router as documents_router
from backend.api.chat import router as chat_router
from backend.db.base import engine, Base


app = FastAPI(title="DocuSense", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}
