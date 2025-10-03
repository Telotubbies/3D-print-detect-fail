from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from . import cards
from backend.database import init_db

# -----------------------------
# Init app & DB
# -----------------------------
app = FastAPI()
init_db()

# -----------------------------
# CORS middleware
# -----------------------------
# ในโปรดักชันให้เปลี่ยน allow_origins เป็นโดเมนจริง
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: ["https://prints.yourdomain.tld"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include API router
# -----------------------------
app.include_router(cards.router)

# -----------------------------
# Serve static folders
# -----------------------------
# สำหรับไฟล์อัปโหลดและผลลัพธ์
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/results", StaticFiles(directory="/Buildweb-3dprint/results"), name="results")

# สำหรับไฟล์ frontend static (CSS/JS)
frontend_static = Path(__file__).resolve().parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=frontend_static), name="static")

# -----------------------------
# Serve index.html
# -----------------------------
frontend_index = Path(__file__).resolve().parent.parent / "frontend" / "index.html"

@app.get("/", response_class=HTMLResponse)
def read_index():
    return frontend_index.read_text(encoding="utf-8")
