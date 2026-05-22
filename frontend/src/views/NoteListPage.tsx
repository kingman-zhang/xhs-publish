import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { createShare, deleteNote, fetchNote, fetchNotes } from "../api";
import type { NoteDetail, NoteListItem, ShareResponse } from "../types";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function NoteListPage() {
  const [keyword, setKeyword] = useState("");
  const [notes, setNotes] = useState<NoteListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<NoteDetail | null>(null);
  const [share, setShare] = useState<ShareResponse | null>(null);

  async function loadNotes(search?: string) {
    try {
      setLoading(true);
      setError("");
      setNotes(await fetchNotes(search));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNotes();
  }, []);

  async function handleDelete(noteId: string) {
    if (!window.confirm("确认删除这条文案吗？")) {
      return;
    }
    try {
      await deleteNote(noteId);
      await loadNotes(keyword.trim());
    } catch (deleteError) {
      window.alert(deleteError instanceof Error ? deleteError.message : "删除失败");
    }
  }

  async function handlePreview(noteId: string) {
    try {
      setPreview(await fetchNote(noteId));
    } catch (previewError) {
      window.alert(previewError instanceof Error ? previewError.message : "预览失败");
    }
  }

  async function handleShare(noteId: string) {
    try {
      setShare(await createShare(noteId));
    } catch (shareError) {
      window.alert(shareError instanceof Error ? shareError.message : "生成分享失败");
    }
  }

  return (
    <section className="page-section">
      <header className="hero-card">
        <div>
          <p className="eyebrow">MVP 控制台</p>
          <h1>小红书图文文案中心</h1>
          <p className="hero-copy">
            在桌面端整理标题、正文、话题与配图，生成二维码后用手机扫码继续发布。
          </p>
        </div>
        <Link className="button button-primary" to="/notes/new">
          + 新建文案
        </Link>
      </header>

      <div className="toolbar-card">
        <label className="search-input">
          <span>搜索文案</span>
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="输入标题或正文关键词"
          />
        </label>
        <button className="button button-secondary" type="button" onClick={() => void loadNotes(keyword.trim())}>
          搜索
        </button>
      </div>

      <div className="table-card">
        {loading ? <div className="empty-state">正在加载文案列表...</div> : null}
        {!loading && error ? <div className="empty-state error-text">{error}</div> : null}
        {!loading && !error && notes.length === 0 ? <div className="empty-state">还没有文案，先新建一条试试。</div> : null}
        {!loading && !error && notes.length > 0 ? (
          <table className="note-table">
            <thead>
              <tr>
                <th>封面</th>
                <th>标题</th>
                <th>正文摘要</th>
                <th>图片数</th>
                <th>更新时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {notes.map((note) => (
                <tr key={note.id}>
                  <td>
                    <div className="cover-thumb">
                      {note.coverUrl ? <img alt={note.title} src={note.coverUrl} /> : <span>无图</span>}
                    </div>
                  </td>
                  <td className="title-cell">{note.title}</td>
                  <td>{note.excerpt}</td>
                  <td>{note.imageCount} 张</td>
                  <td>{formatDate(note.updatedAt)}</td>
                  <td>
                    <div className="action-row">
                      <button className="tag-button tag-blue" type="button" onClick={() => void handleShare(note.id)}>
                        分享二维码
                      </button>
                      <button className="tag-button tag-green" type="button" onClick={() => void handlePreview(note.id)}>
                        预览
                      </button>
                      <Link className="tag-button tag-amber" to={`/notes/${note.id}/edit`}>
                        编辑
                      </Link>
                      <button className="tag-button tag-red" type="button" onClick={() => void handleDelete(note.id)}>
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>

      {preview ? (
        <div className="modal-backdrop" onClick={() => setPreview(null)}>
          <div className="modal-card preview-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h2>{preview.title}</h2>
              <button className="ghost-close" type="button" onClick={() => setPreview(null)}>
                关闭
              </button>
            </div>
            <div className="preview-grid">
              {preview.assets.map((asset) => (
                <img key={asset.id} alt={asset.fileName} src={asset.publicUrl} />
              ))}
            </div>
            <div className="preview-body">
              <p>{preview.body}</p>
              <div className="topic-wrap">
                {preview.topics.map((topic) => (
                  <span key={topic} className="topic-pill">
                    #{topic}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {share ? (
        <div className="modal-backdrop" onClick={() => setShare(null)}>
          <div className="modal-card share-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h2>分享二维码</h2>
              <button className="ghost-close" type="button" onClick={() => setShare(null)}>
                关闭
              </button>
            </div>
            <img className="qr-image" alt="分享二维码" src={share.qrCodeDataUrl} />
            <input className="share-link" readOnly value={share.shareUrl} />
            <div className="share-actions">
              <button
                className="button button-secondary"
                type="button"
                onClick={() => navigator.clipboard.writeText(share.shareUrl)}
              >
                复制链接
              </button>
              <a className="button button-primary" href={share.shareUrl} rel="noreferrer" target="_blank">
                打开预览页
              </a>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
