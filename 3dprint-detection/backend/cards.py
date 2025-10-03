from fastapi import APIRouter, UploadFile, File, HTTPException, Header
import uuid, os, datetime
from backend.model import detect
from backend.schemas import Card
from backend.storage import save_upload
from backend.config import ALLOWED_MIME, MAX_FILE_SIZE, KEY_TTL, MODEL_PATH
from . import database as db

router = APIRouter()

def _validate_upload(image: UploadFile) -> None:
    if image.content_type not in ALLOWED_MIME:
        raise HTTPException(400, "Only JPEG/PNG allowed")

@router.post("/cards", response_model=Card, status_code=201)
async def create_card(image: UploadFile = File(...)):
    _validate_upload(image)
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 20MB)")

    card_id = uuid.uuid4().hex[:8]
    save_upload(card_id, image.filename, content)  # ถ้าไม่อยากเก็บ สามารถข้ามได้
    res = detect(content, card_id)
    card = {
        "card_id": card_id,
        "detected_image_url": res["detected_image_url"],
        "status": res["status"],
        "scores": res["scores"],
        "updated_at": res["updated_at"],
        "model": os.path.basename(MODEL_PATH),
    }
    db.upsert_card(card)
    return card

@router.post("/cards/{card_id}/apikey")
async def get_apikey(card_id: str):
    card = db.get_card(card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    rec = db.create_apikey(card_id, KEY_TTL)
    return rec

@router.post("/cards/{card_id}/replace", response_model=Card)
async def replace_card(card_id: str, image: UploadFile = File(...), x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(401, "Missing API key")
    if not db.verify_apikey(x_api_key, card_id):
        raise HTTPException(401, "API key expired/invalid")

    _validate_upload(image)
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 20MB)")

    res = detect(content, card_id)
    card = {
        "card_id": card_id,
        "detected_image_url": res["detected_image_url"],
        "status": res["status"],
        "scores": res["scores"],
        "updated_at": res["updated_at"],
        "model": os.path.basename(MODEL_PATH),
    }
    db.upsert_card(card)
    # ถ้าต้องการ one-time key ให้ uncomment:
    # db.mark_apikey_used(x_api_key)
    return card

@router.get("/cards")
async def list_cards(limit: int = 50, cursor: str | None = None):
    items = db.list_cards(limit=limit, cursor=cursor)
    # เพื่อลด payload หน้าหลักจะไม่ต้องส่ง scores ก็ได้ แต่เราคงไว้
    return {"items": items, "next_cursor": None}

@router.get("/cards/{card_id}", response_model=Card)
async def get_card(card_id: str):
    card = db.get_card(card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    return card
