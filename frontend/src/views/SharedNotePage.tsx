import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { fetchSharedNote, fetchSignature } from "../api";
import type { SharePayload, SignatureResponse } from "../types";

declare global {
  interface Window {
    xhs?: {
      config?: (params: Record<string, unknown>) => void;
      verifyConfig?: (params: Record<string, unknown>) => void;
      ready?: (callback: () => void) => void;
      error?: (callback: (error: unknown) => void) => void;
      invoke?: (method: string, payload?: Record<string, unknown>) => void;
      share?: (payload: Record<string, unknown>) => Promise<unknown> | unknown;
    };
  }
}

const SDK_URL =
  import.meta.env.VITE_XHS_SDK_URL || "https://fe-static.xhscdn.com/biz-static/goten/xhs-1.0.1.js";
const XHS_TITLE_LIMIT = 20;
const XHS_CONTENT_LIMIT = 1000;

function buildShareContent(body: string, topics: string[]) {
  const merged = `${body} ${topics.map((topic) => `#${topic}`).join(" ")}`.trim();
  return merged.slice(0, XHS_CONTENT_LIMIT);
}

function buildShareTitle(title: string) {
  return title.trim().slice(0, XHS_TITLE_LIMIT);
}

function ensureSdkLoaded(onLoad: () => void, onError: () => void) {
  const existing = document.querySelector<HTMLScriptElement>(`script[data-xhs-sdk="${SDK_URL}"]`);
  if (existing) {
    if (window.xhs) {
      onLoad();
      return;
    }
    existing.addEventListener("load", onLoad, { once: true });
    existing.addEventListener("error", onError, { once: true });
    return;
  }
  const script = document.createElement("script");
  script.src = SDK_URL;
  script.async = true;
  script.dataset.xhsSdk = SDK_URL;
  script.addEventListener("load", onLoad, { once: true });
  script.addEventListener("error", onError, { once: true });
  document.body.appendChild(script);
}

export function SharedNotePage() {
  const { token } = useParams();
  const [payload, setPayload] = useState<SharePayload | null>(null);
  const [error, setError] = useState("");
  const [signature, setSignature] = useState<SignatureResponse | null>(null);
  const [statusText, setStatusText] = useState("正在加载分享内容...");
  const [sdkState, setSdkState] = useState<"loading" | "loaded" | "error">("loading");
  const [hasXhsObject, setHasXhsObject] = useState(false);
  const [lastSdkError, setLastSdkError] = useState("");

  useEffect(() => {
    ensureSdkLoaded(
      () => {
        setSdkState("loaded");
        setHasXhsObject(Boolean(window.xhs));
      },
      () => {
        setSdkState("error");
        setHasXhsObject(Boolean(window.xhs));
        setLastSdkError("SDK 脚本加载失败");
      },
    );
    if (!token) {
      setError("分享链接无效");
      return;
    }
    void (async () => {
      try {
        const [note, sign] = await Promise.all([
          fetchSharedNote(token),
          fetchSignature(window.location.href.split("#")[0]),
        ]);
        setPayload(note);
        setSignature(sign);
        setHasXhsObject(Boolean(window.xhs));
        setStatusText(sign.enabled ? "内容已准备好，可尝试发布到小红书" : "当前未配置开放平台签名，请先完成服务端配置");
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "加载失败");
      }
    })();
  }, [token]);

  function refreshSdkState() {
    setHasXhsObject(Boolean(window.xhs));
  }

  async function publishToXhs() {
    if (!payload) {
      return;
    }
    refreshSdkState();
    if (!signature?.enabled || !window.xhs) {
      window.alert(
        "当前环境暂时无法直接唤起。调试信息："
          + `签名=${signature?.enabled ? "已生成" : "未生成"}，`
          + `SDK=${sdkState}，`
          + `window.xhs=${window.xhs ? "存在" : "不存在"}。`
          + "请优先在小红书内或官方支持的浏览器环境中打开。",
      );
      return;
    }

    const configParams = {
      appKey: signature.appKey,
      timeStamp: signature.timeStamp,
      nonce: signature.nonce,
      signature: signature.signature,
    };
    const shareTitle = buildShareTitle(payload.title);
    const shareContent = buildShareContent(payload.body, payload.topics);
    try {
      await window.xhs.share?.({
        shareInfo: {
          type: "normal",
          title: shareTitle,
          content: shareContent,
          images: payload.images,
          cover: payload.coverUrl || payload.images[0] || "",
        },
        verifyConfig: {
          appKey: configParams.appKey,
          nonce: configParams.nonce,
          timestamp: String(configParams.timeStamp),
          signature: configParams.signature,
        },
        fail: (sdkError: unknown) => {
          const message = sdkError instanceof Error ? sdkError.message : JSON.stringify(sdkError);
          setLastSdkError(`share fail: ${message}`);
          window.alert("小红书分享调用失败，请在兼容环境下重试。");
        },
      });
      setLastSdkError("");
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : JSON.stringify(caughtError);
      setLastSdkError(`share exception: ${message}`);
      window.alert("当前环境暂时无法直接唤起，请复制链接后在支持的小红书浏览器环境中打开。");
    }
  }

  return (
    <main className="shared-page">
      <section className="shared-phone">
        <div className="shared-head">
          <span className="shared-badge">小红书发布预览</span>
          <p>{statusText}</p>
        </div>

        {error ? <div className="empty-state error-text">{error}</div> : null}

        {payload ? (
          <>
            <div className="shared-gallery">
              {payload.images.map((image, index) => (
                <img key={image} alt={`${payload.title}-${index + 1}`} src={image} />
              ))}
            </div>

            <div className="shared-copy">
              <h1>{payload.title}</h1>
              <p>{payload.body}</p>
              <div className="topic-wrap">
                {payload.topics.map((topic) => (
                  <span key={topic} className="topic-pill">
                    #{topic}
                  </span>
                ))}
              </div>
            </div>

            <div className="shared-footer">
              <button className="button button-primary button-block" type="button" onClick={publishToXhs}>
                发布到小红书
              </button>
              <div className="debug-panel">
                <strong>调试信息</strong>
                <div>签名状态：{signature?.enabled ? "已生成" : "未生成"}</div>
                <div>SDK 脚本：{sdkState === "loading" ? "加载中" : sdkState === "loaded" ? "已加载" : "加载失败"}</div>
                <div>`window.xhs`：{hasXhsObject ? "存在" : "不存在"}</div>
                <div>标题长度：{buildShareTitle(payload.title).length} / {XHS_TITLE_LIMIT}</div>
                <div>正文长度：{buildShareContent(payload.body, payload.topics).length} / {XHS_CONTENT_LIMIT}</div>
                <div>UA：{navigator.userAgent}</div>
                {lastSdkError ? <div>最近错误：{lastSdkError}</div> : null}
              </div>
              <p className="compat-text">
                如果当前页面无法直接唤起，请复制本链接并在系统浏览器或小红书兼容环境中重新打开。
              </p>
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}
