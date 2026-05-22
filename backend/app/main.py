from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .models import NoteCreatePayload, NoteDetailResponse, NoteListItemResponse, SharePayloadResponse, ShareTokenResponse, SignatureResponse
from .repository import init_indexes
from .services import (
    create_note_service,
    delete_asset_service,
    delete_note_service,
    get_note_service,
    get_share_service,
    get_shared_note_payload,
    get_signature_service,
    list_notes_service,
    update_note_service,
    upload_asset_service,
)

settings = get_settings()

app = FastAPI(title="小红书文案管理 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.on_event("startup")
def on_startup() -> None:
    init_indexes()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/notes", response_model=list[NoteListItemResponse])
def list_notes(keyword: str | None = Query(default=None), page: int = Query(default=1, ge=1), pageSize: int = Query(default=20, ge=1, le=100)) -> list[NoteListItemResponse]:
    return list_notes_service(keyword, page, pageSize)


@app.post("/api/notes", response_model=NoteDetailResponse)
def create_note(payload: NoteCreatePayload) -> NoteDetailResponse:
    return create_note_service(payload)


@app.get("/api/notes/{note_id}", response_model=NoteDetailResponse)
def get_note(note_id: str) -> NoteDetailResponse:
    return get_note_service(note_id)


@app.put("/api/notes/{note_id}", response_model=NoteDetailResponse)
def update_note(note_id: str, payload: NoteCreatePayload) -> NoteDetailResponse:
    return update_note_service(note_id, payload)


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: str) -> dict[str, bool]:
    delete_note_service(note_id)
    return {"success": True}


@app.post("/api/assets/upload")
async def upload_asset(file: UploadFile = File(...)):
    return await upload_asset_service(file)


@app.delete("/api/assets/{asset_id}")
def delete_asset(asset_id: str) -> dict[str, bool]:
    delete_asset_service(asset_id)
    return {"success": True}


@app.post("/api/notes/{note_id}/share", response_model=ShareTokenResponse)
def share_note(note_id: str) -> ShareTokenResponse:
    return get_share_service(note_id)


@app.get("/api/share/{token}", response_model=SharePayloadResponse)
def get_shared_note(token: str) -> SharePayloadResponse:
    return get_shared_note_payload(token)


@app.get("/api/xhs/signature", response_model=SignatureResponse)
def get_signature(url: str = Query(...)) -> SignatureResponse:
    return get_signature_service(url)
