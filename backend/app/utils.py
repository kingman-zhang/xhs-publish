import base64
import hashlib
import io
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

import qrcode
from PIL import Image

from .config import get_settings


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_id() -> str:
    return uuid.uuid4().hex


def generate_share_token() -> str:
    return secrets.token_urlsafe(18)


def safe_excerpt(text: str, limit: int = 90) -> str:
    clean = " ".join(text.strip().split())
    if len(clean) <= limit:
        return clean
    return f"{clean[:limit].rstrip()}..."


def build_share_url(token: str) -> str:
    settings = get_settings()
    base = settings.public_base_url.rstrip("/") + "/"
    return urljoin(base, f"s/{token}")


def public_asset_url(relative_path: str) -> str:
    settings = get_settings()
    base = settings.public_base_url.rstrip("/") + "/"
    return urljoin(base, relative_path.lstrip("/"))


def save_upload_file(file_name: str, content: bytes) -> tuple[Path, str]:
    settings = get_settings()
    extension = Path(file_name).suffix.lower()
    generated_name = f"{uuid.uuid4().hex}{extension}"
    relative_path = f"/uploads/{generated_name}"
    target = settings.upload_dir / generated_name
    target.write_bytes(content)
    return target, relative_path


def read_image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.width, image.height


def build_qr_code_data_url(text: str) -> str:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def sha1_hex(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
