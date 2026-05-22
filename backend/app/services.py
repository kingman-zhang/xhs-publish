import mimetypes
import secrets
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from .config import get_settings
from .models import (
    AssetResponse,
    NoteCreatePayload,
    NoteDetailResponse,
    NoteListItemResponse,
    SharePayloadResponse,
    ShareTokenResponse,
    SignatureResponse,
)
from .repository import (
    bind_assets_to_note,
    create_asset,
    create_note,
    delete_asset,
    get_asset,
    get_assets_by_ids,
    get_note,
    get_note_by_share_token,
    list_notes,
    soft_delete_note,
    update_note,
)
from .utils import (
    build_qr_code_data_url,
    build_share_url,
    generate_id,
    generate_share_token,
    public_asset_url,
    read_image_size,
    safe_excerpt,
    save_upload_file,
    utc_now,
)
from .xhs_auth import build_xhs_signature, get_access_token


def serialize_assets(asset_ids: list[str]) -> list[AssetResponse]:
    assets = get_assets_by_ids(asset_ids)
    return [
        AssetResponse(
            id=asset["id"],
            fileName=asset["fileName"],
            publicUrl=asset["publicUrl"],
            mimeType=asset["mimeType"],
            size=asset["size"],
            width=asset["width"],
            height=asset["height"],
            sortOrder=asset["sortOrder"],
        )
        for asset in assets
    ]


def create_note_service(payload: NoteCreatePayload) -> NoteDetailResponse:
    now = utc_now()
    note_id = generate_id()
    share_token = generate_share_token()
    create_note(
        {
            "id": note_id,
            "title": payload.title.strip(),
            "body": payload.body.strip(),
            "topics": [topic.strip().lstrip("#") for topic in payload.topics if topic.strip()],
            "coverAssetId": payload.coverAssetId,
            "assetIds": payload.assetIds,
            "shareToken": share_token,
            "contentType": payload.contentType,
            "createdAt": now,
            "updatedAt": now,
            "deletedAt": None,
        }
    )
    bind_assets_to_note(payload.assetIds, note_id)
    note = get_note(note_id)
    assert note is not None
    return map_note_detail(note)


def update_note_service(note_id: str, payload: NoteCreatePayload) -> NoteDetailResponse:
    existing = get_note(note_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文案不存在")
    now = utc_now()
    update_note(
        note_id,
        {
            "title": payload.title.strip(),
            "body": payload.body.strip(),
            "topics": [topic.strip().lstrip("#") for topic in payload.topics if topic.strip()],
            "coverAssetId": payload.coverAssetId,
            "assetIds": payload.assetIds,
            "contentType": payload.contentType,
            "updatedAt": now,
        },
    )
    bind_assets_to_note(payload.assetIds, note_id)
    note = get_note(note_id)
    assert note is not None
    return map_note_detail(note)


def map_note_detail(note: dict) -> NoteDetailResponse:
    share_url = build_share_url(note["shareToken"])
    return NoteDetailResponse(
        id=note["id"],
        title=note["title"],
        body=note["body"],
        topics=note.get("topics", []),
        coverAssetId=note.get("coverAssetId"),
        contentType=note.get("contentType", "image_post"),
        assetIds=note.get("assetIds", []),
        assets=serialize_assets(note.get("assetIds", [])),
        shareUrl=share_url,
        createdAt=note["createdAt"],
        updatedAt=note["updatedAt"],
    )


def list_notes_service(keyword: str | None, page: int, page_size: int) -> list[NoteListItemResponse]:
    skip = max(page - 1, 0) * page_size
    notes = list_notes(keyword, skip, page_size)
    response: list[NoteListItemResponse] = []
    for note in notes:
        assets = get_assets_by_ids(note.get("assetIds", []))
        cover_url = None
        if note.get("coverAssetId"):
            cover_asset = next((asset for asset in assets if asset["id"] == note["coverAssetId"]), None)
            cover_url = cover_asset["publicUrl"] if cover_asset else None
        elif assets:
            cover_url = assets[0]["publicUrl"]
        response.append(
            NoteListItemResponse(
                id=note["id"],
                title=note["title"],
                excerpt=safe_excerpt(note["body"]),
                coverUrl=cover_url,
                imageCount=len(note.get("assetIds", [])),
                updatedAt=note["updatedAt"],
                shareUrl=build_share_url(note["shareToken"]),
            )
        )
    return response


async def upload_asset_service(file: UploadFile) -> AssetResponse:
    settings = get_settings()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传文件不能为空")
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="图片大小超出限制")
    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if not mime_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持图片文件")
    target_path, relative_path = save_upload_file(file.filename or "upload.png", content)
    width, height = read_image_size(target_path)
    asset_id = generate_id()
    asset = {
        "id": asset_id,
        "noteId": None,
        "fileName": file.filename or target_path.name,
        "relativePath": relative_path,
        "publicUrl": public_asset_url(relative_path),
        "mimeType": mime_type,
        "size": len(content),
        "width": width,
        "height": height,
        "sortOrder": 0,
        "createdAt": utc_now(),
    }
    create_asset(asset)
    return AssetResponse(
        id=asset_id,
        fileName=asset["fileName"],
        publicUrl=asset["publicUrl"],
        mimeType=mime_type,
        size=asset["size"],
        width=width,
        height=height,
        sortOrder=0,
    )


def delete_asset_service(asset_id: str) -> None:
    asset = get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")
    path = Path(get_settings().upload_dir / Path(asset["relativePath"]).name)
    if path.exists():
        path.unlink()
    delete_asset(asset_id)


def delete_note_service(note_id: str) -> None:
    existing = get_note(note_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文案不存在")
    soft_delete_note(note_id, utc_now())


def get_note_service(note_id: str) -> NoteDetailResponse:
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文案不存在")
    return map_note_detail(note)


def get_share_service(note_id: str) -> ShareTokenResponse:
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文案不存在")
    share_url = build_share_url(note["shareToken"])
    return ShareTokenResponse(
        shareUrl=share_url,
        qrCodeDataUrl=build_qr_code_data_url(share_url),
        token=note["shareToken"],
    )


def get_shared_note_payload(token: str) -> SharePayloadResponse:
    note = get_note_by_share_token(token)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享内容不存在")
    assets = get_assets_by_ids(note.get("assetIds", []))
    cover_url = None
    if note.get("coverAssetId"):
        cover_asset = next((asset for asset in assets if asset["id"] == note["coverAssetId"]), None)
        cover_url = cover_asset["publicUrl"] if cover_asset else None
    elif assets:
        cover_url = assets[0]["publicUrl"]
    return SharePayloadResponse(
        id=note["id"],
        title=note["title"],
        body=note["body"],
        topics=note.get("topics", []),
        coverUrl=cover_url,
        images=[asset["publicUrl"] for asset in assets],
    )


def get_signature_service(url: str) -> SignatureResponse:
    settings = get_settings()
    if not settings.xhs_app_key or not settings.xhs_app_secret:
        return SignatureResponse(
            appKey=settings.xhs_app_key,
            appId=settings.xhs_app_key,
            timestamp=0,
            timeStamp=0,
            nonce="",
            nonceStr="",
            signature="",
            enabled=False,
            accessTokenExpiresAt=None,
        )
    access_token_state = get_access_token()
    timestamp = int(utc_now().timestamp() * 1000)
    nonce = secrets.token_hex(16)
    signature = build_xhs_signature(
        settings.xhs_app_key,
        nonce,
        timestamp,
        access_token_state.token,
    )
    return SignatureResponse(
        appKey=settings.xhs_app_key,
        appId=settings.xhs_app_key,
        timestamp=timestamp,
        timeStamp=timestamp,
        nonce=nonce,
        nonceStr=nonce,
        signature=signature,
        enabled=True,
        accessTokenExpiresAt=access_token_state.expires_at_ms,
    )
