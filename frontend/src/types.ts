export type Asset = {
  id: string;
  fileName: string;
  publicUrl: string;
  mimeType: string;
  size: number;
  width: number;
  height: number;
  sortOrder: number;
};

export type NoteListItem = {
  id: string;
  title: string;
  excerpt: string;
  coverUrl: string | null;
  imageCount: number;
  updatedAt: string;
  shareUrl: string;
};

export type NoteDetail = {
  id: string;
  title: string;
  body: string;
  topics: string[];
  coverAssetId: string | null;
  contentType: "image_post" | "video_post";
  assetIds: string[];
  assets: Asset[];
  shareUrl: string;
  createdAt: string;
  updatedAt: string;
};

export type NoteForm = {
  title: string;
  body: string;
  topics: string[];
  coverAssetId: string | null;
  contentType: "image_post" | "video_post";
  assetIds: string[];
};

export type SharePayload = {
  id: string;
  title: string;
  body: string;
  topics: string[];
  coverUrl: string | null;
  images: string[];
};

export type ShareResponse = {
  shareUrl: string;
  qrCodeDataUrl: string;
  token: string;
};

export type SignatureResponse = {
  appKey: string;
  appId: string;
  timestamp: number;
  timeStamp: number;
  nonce: string;
  nonceStr: string;
  signature: string;
  enabled: boolean;
  accessTokenExpiresAt?: number | null;
};
