import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createNote, fetchNote, removeAsset, updateNote, uploadAsset } from "../api";
import type { Asset, NoteForm } from "../types";

type NoteEditorPageProps = {
  mode: "create" | "edit";
};

const XHS_TITLE_LIMIT = 20;
const XHS_BODY_LIMIT = 1000;

const defaultForm: NoteForm = {
  title: "",
  body: "",
  topics: [],
  coverAssetId: null,
  contentType: "image_post",
  assetIds: [],
};

export function NoteEditorPage({ mode }: NoteEditorPageProps) {
  const navigate = useNavigate();
  const { noteId } = useParams();
  const [form, setForm] = useState<NoteForm>(defaultForm);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [topicInput, setTopicInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(mode === "edit");

  useEffect(() => {
    if (mode !== "edit" || !noteId) {
      return;
    }
    void (async () => {
      const detail = await fetchNote(noteId);
      setForm({
        title: detail.title,
        body: detail.body,
        topics: detail.topics,
        coverAssetId: detail.coverAssetId,
        contentType: detail.contentType,
        assetIds: detail.assetIds,
      });
      setAssets(detail.assets);
      setLoading(false);
    })();
  }, [mode, noteId]);

  const orderedAssets = useMemo(
    () =>
      form.assetIds
        .map((assetId) => assets.find((asset) => asset.id === assetId))
        .filter((asset): asset is Asset => Boolean(asset)),
    [assets, form.assetIds],
  );

  function addTopic() {
    const cleaned = topicInput.trim().replace(/^#/, "");
    if (!cleaned || form.topics.includes(cleaned)) {
      setTopicInput("");
      return;
    }
    setForm((current) => ({ ...current, topics: [...current.topics, cleaned] }));
    setTopicInput("");
  }

  function removeTopic(topic: string) {
    setForm((current) => ({ ...current, topics: current.topics.filter((item) => item !== topic) }));
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const fileList = event.target.files;
    if (!fileList?.length) {
      return;
    }
    const uploaded: Asset[] = [];
    for (const file of Array.from(fileList)) {
      uploaded.push(await uploadAsset(file));
    }
    setAssets((current) => [...current, ...uploaded]);
    setForm((current) => ({
      ...current,
      assetIds: [...current.assetIds, ...uploaded.map((item) => item.id)],
      coverAssetId: current.coverAssetId ?? uploaded[0]?.id ?? null,
    }));
    event.target.value = "";
  }

  async function handleRemoveAsset(assetId: string) {
    try {
      await removeAsset(assetId);
      setAssets((current) => current.filter((asset) => asset.id !== assetId));
      setForm((current) => ({
        ...current,
        assetIds: current.assetIds.filter((item) => item !== assetId),
        coverAssetId:
          current.coverAssetId === assetId ? current.assetIds.filter((item) => item !== assetId)[0] ?? null : current.coverAssetId,
      }));
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "删除图片失败");
    }
  }

  function moveAsset(assetId: string, direction: -1 | 1) {
    setForm((current) => {
      const index = current.assetIds.indexOf(assetId);
      const targetIndex = index + direction;
      if (index < 0 || targetIndex < 0 || targetIndex >= current.assetIds.length) {
        return current;
      }
      const next = [...current.assetIds];
      [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
      return { ...current, assetIds: next };
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim() || !form.body.trim()) {
      window.alert("标题和正文不能为空");
      return;
    }
    if (form.title.trim().length > XHS_TITLE_LIMIT) {
      window.alert(`标题不能超过 ${XHS_TITLE_LIMIT} 个字符`);
      return;
    }
    if (form.body.trim().length > XHS_BODY_LIMIT) {
      window.alert(`正文不能超过 ${XHS_BODY_LIMIT} 个字符`);
      return;
    }
    try {
      setSaving(true);
      if (mode === "edit" && noteId) {
        await updateNote(noteId, form);
      } else {
        await createNote(form);
      }
      navigate("/");
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="page-section"><div className="empty-state">正在加载文案详情...</div></div>;
  }

  return (
    <section className="page-section">
      <header className="editor-header">
        <div>
          <p className="eyebrow">{mode === "edit" ? "编辑文案" : "新建文案"}</p>
          <h1>{mode === "edit" ? "更新这条图文内容" : "发布前先把素材整理好"}</h1>
        </div>
        <Link className="button button-secondary" to="/">
          返回列表
        </Link>
      </header>

      <form className="editor-layout" onSubmit={handleSubmit}>
        <div className="editor-form-card">
          <label className="field">
            <span>标题</span>
            <input
              value={form.title}
              maxLength={XHS_TITLE_LIMIT}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value.slice(0, XHS_TITLE_LIMIT) }))}
              placeholder="输入标题"
            />
            <small>{form.title.length} / {XHS_TITLE_LIMIT}</small>
          </label>

          <label className="field">
            <span>正文内容</span>
            <textarea
              rows={10}
              value={form.body}
              onChange={(event) =>
                setForm((current) => ({ ...current, body: event.target.value.slice(0, XHS_BODY_LIMIT) }))
              }
              placeholder="输入正文内容"
            />
            <small>{form.body.length} / {XHS_BODY_LIMIT}</small>
          </label>

          <div className="field">
            <span>话题</span>
            <div className="topic-editor">
              <input
                value={topicInput}
                onChange={(event) => setTopicInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addTopic();
                  }
                }}
                placeholder="输入话题，按回车添加"
              />
              <button className="button button-secondary" type="button" onClick={addTopic}>
                添加话题
              </button>
            </div>
            <div className="topic-wrap">
              {form.topics.map((topic) => (
                <button key={topic} className="topic-pill removable" type="button" onClick={() => removeTopic(topic)}>
                  #{topic} ×
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <span>图片上传</span>
            <label className="upload-panel">
              <input accept="image/*" hidden multiple type="file" onChange={(event) => void handleUpload(event)} />
              <strong>点击上传图片</strong>
              <small>支持多图上传，单张大小受后端配置限制</small>
            </label>
          </div>

          <div className="submit-row">
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? "正在保存..." : mode === "edit" ? "保存修改" : "创建文案"}
            </button>
          </div>
        </div>

        <aside className="editor-side-card">
          <div className="side-header">
            <h2>图片与封面</h2>
            <span>{orderedAssets.length} 张</span>
          </div>
          {orderedAssets.length === 0 ? <div className="empty-state">上传图片后会显示在这里。</div> : null}
          <div className="asset-stack">
            {orderedAssets.map((asset, index) => {
              const isCover = asset.id === form.coverAssetId;
              return (
                <div key={asset.id} className={`asset-card ${isCover ? "asset-card--cover" : ""}`}>
                  <img alt={asset.fileName} src={asset.publicUrl} />
                  <div className="asset-meta">
                    <strong>{isCover ? "当前封面" : `第 ${index + 1} 张`}</strong>
                    <small>{asset.fileName}</small>
                  </div>
                  <div className="asset-actions">
                    <button className="mini-button" type="button" onClick={() => moveAsset(asset.id, -1)}>
                      上移
                    </button>
                    <button className="mini-button" type="button" onClick={() => moveAsset(asset.id, 1)}>
                      下移
                    </button>
                    <button
                      className="mini-button"
                      type="button"
                      onClick={() => setForm((current) => ({ ...current, coverAssetId: asset.id }))}
                    >
                      设为封面
                    </button>
                    <button className="mini-button danger" type="button" onClick={() => void handleRemoveAsset(asset.id)}>
                      删除
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>
      </form>
    </section>
  );
}
