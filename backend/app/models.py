from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AssetDocument(BaseModel):
    id: str
    noteId: str | None = None
    fileName: str
    relativePath: str
    publicUrl: str
    mimeType: str
    size: int
    width: int
    height: int
    sortOrder: int = 0
    createdAt: datetime


class NoteDocument(BaseModel):
    id: str
    title: str
    body: str
    topics: list[str] = Field(default_factory=list)
    coverAssetId: str | None = None
    assetIds: list[str] = Field(default_factory=list)
    shareToken: str
    contentType: Literal["image_post", "video_post"] = "image_post"
    createdAt: datetime
    updatedAt: datetime
    deletedAt: datetime | None = None


class NoteCreatePayload(BaseModel):
    title: str
    body: str
    topics: list[str] = Field(default_factory=list)
    coverAssetId: str | None = None
    assetIds: list[str] = Field(default_factory=list)
    contentType: Literal["image_post", "video_post"] = "image_post"


class NoteUpdatePayload(NoteCreatePayload):
    pass


class ShareTokenResponse(BaseModel):
    shareUrl: str
    qrCodeDataUrl: str
    token: str


class SignatureResponse(BaseModel):
    appKey: str
    appId: str
    timestamp: int
    timeStamp: int
    nonce: str
    nonceStr: str
    signature: str
    enabled: bool
    accessTokenExpiresAt: int | None = None


class AssetResponse(BaseModel):
    id: str
    fileName: str
    publicUrl: str
    mimeType: str
    size: int
    width: int
    height: int
    sortOrder: int


class NoteDetailResponse(BaseModel):
    id: str
    title: str
    body: str
    topics: list[str]
    coverAssetId: str | None
    contentType: str
    assetIds: list[str]
    assets: list[AssetResponse]
    shareUrl: str
    createdAt: datetime
    updatedAt: datetime


class NoteListItemResponse(BaseModel):
    id: str
    title: str
    excerpt: str
    coverUrl: str | None
    imageCount: int
    updatedAt: datetime
    shareUrl: str


class SharePayloadResponse(BaseModel):
    id: str
    title: str
    body: str
    topics: list[str]
    coverUrl: str | None
    images: list[str]
