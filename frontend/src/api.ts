import type { Asset, NoteDetail, NoteForm, NoteListItem, SharePayload, ShareResponse, SignatureResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(data.detail || "请求失败");
  }
  return response.json() as Promise<T>;
}

export async function fetchNotes(keyword?: string): Promise<NoteListItem[]> {
  const query = keyword ? `?keyword=${encodeURIComponent(keyword)}` : "";
  return request<NoteListItem[]>(`/notes${query}`);
}

export async function fetchNote(noteId: string): Promise<NoteDetail> {
  return request<NoteDetail>(`/notes/${noteId}`);
}

export async function createNote(payload: NoteForm): Promise<NoteDetail> {
  return request<NoteDetail>("/notes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateNote(noteId: string, payload: NoteForm): Promise<NoteDetail> {
  return request<NoteDetail>(`/notes/${noteId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteNote(noteId: string): Promise<void> {
  await request(`/notes/${noteId}`, { method: "DELETE" });
}

export async function uploadAsset(file: File): Promise<Asset> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_BASE_URL}/assets/upload`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "上传失败" }));
    throw new Error(data.detail || "上传失败");
  }
  return response.json() as Promise<Asset>;
}

export async function removeAsset(assetId: string): Promise<void> {
  await request(`/assets/${assetId}`, { method: "DELETE" });
}

export async function createShare(noteId: string): Promise<ShareResponse> {
  return request<ShareResponse>(`/notes/${noteId}/share`, { method: "POST" });
}

export async function fetchSharedNote(token: string): Promise<SharePayload> {
  return request<SharePayload>(`/share/${token}`);
}

export async function fetchSignature(url: string): Promise<SignatureResponse> {
  return request<SignatureResponse>(`/xhs/signature?url=${encodeURIComponent(url)}`);
}
