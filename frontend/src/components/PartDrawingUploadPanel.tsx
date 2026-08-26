"use client";

import { useRouter } from "next/navigation";
import { useId, useMemo, useState } from "react";
import { isPdfFile, MAX_FILE_SIZE_MB, MAX_PDF_PAGES, UPLOAD_ACCEPT } from "@/lib/uploadLimits";
import { parseUploadResult, readErrorDetail } from "@/lib/types";

type StagedFile = {
  id: string;
  file: File;
  selectedPage: number;
};

export function PartDrawingUploadPanel() {
  const router = useRouter();
  const inputId = useId();
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [pending, setPending] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  const hasPdf = useMemo(() => staged.some((item) => isPdfFile(item.file)), [staged]);

  function addFiles(fileList: FileList | File[]): void {
    const incoming = Array.from(fileList).map((file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`,
      file,
      selectedPage: 1,
    }));
    setStaged((current) => [...current, ...incoming]);
    setMessages([]);
    setErrors([]);
  }

  async function onSubmit(): Promise<void> {
    if (staged.length === 0 || pending) {
      return;
    }
    setPending(true);
    setMessages([]);
    setErrors([]);
    const form = new FormData();
    const pages: number[] = [];
    for (const item of staged) {
      form.append("files", item.file, item.file.name);
      pages.push(item.selectedPage);
    }
    form.append("selected_pages", JSON.stringify(pages));
    const response = await fetch("/api/part-drawings", { method: "POST", body: form });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      setErrors([readErrorDetail(payload) ?? "上传失败"]);
      setPending(false);
      return;
    }
    const result = parseUploadResult(payload);
    const nextErrors = result.rejected.map((item) => item.detail);
    const nextMessages =
      result.items.length > 0 ? [`已上传 ${result.items.length} 张零件图`] : [];
    setErrors(nextErrors);
    setMessages(nextMessages);
    if (result.items.length > 0) {
      setStaged([]);
      router.refresh();
    }
    setPending(false);
  }

  return (
    <section className="glass-card mb-4 p-5 backdrop-blur-xl">
      <label
        htmlFor={inputId}
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragOver(false);
          if (event.dataTransfer.files.length > 0) {
            addFiles(event.dataTransfer.files);
          }
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-8 text-center transition-all ${
          dragOver
            ? "border-blue-500 bg-blue-50/60"
            : "border-slate-300/80 bg-white/50 hover:border-blue-400 hover:bg-white/80"
        }`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-100/60 text-blue-600 mb-3 shadow-xs">
          <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className="text-sm font-semibold text-slate-800">
          拖拽零件图到这里，或 <span className="text-blue-600 hover:underline">点击浏览文件</span>
        </p>
        <p className="mt-1.5 max-w-lg text-xs leading-5 text-slate-500">
          支持 PDF、JPEG、PNG、WebP、TIFF · 单文件不超过 {MAX_FILE_SIZE_MB} MB · PDF 不超过{" "}
          {MAX_PDF_PAGES} 页 · 支持批量多选。
        </p>
        <input
          id={inputId}
          type="file"
          multiple
          accept={UPLOAD_ACCEPT}
          className="sr-only"
          onChange={(event) => {
            if (event.target.files && event.target.files.length > 0) {
              addFiles(event.target.files);
              event.target.value = "";
            }
          }}
        />
      </label>

      {hasPdf ? (
        <div className="glass-warning-pill mt-3 px-3.5 py-2 text-xs leading-5">
          ℹ️ 多页 PDF 仅处理指定单页（默认第 1 页），后续 AI 读图取数将以该页为准。
        </div>
      ) : null}

      {staged.length > 0 ? (
        <ul className="mt-4 divide-y divide-slate-100 rounded-xl border border-white/80 bg-white/70 shadow-xs">
          {staged.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center gap-3 px-4 py-2.5">
              <span className="min-w-0 flex-1 truncate text-xs font-medium text-slate-800">{item.file.name}</span>
              {isPdfFile(item.file) ? (
                <label className="flex items-center gap-2 text-xs text-slate-600">
                  指定处理第
                  <input
                    type="number"
                    min={1}
                    max={MAX_PDF_PAGES}
                    value={item.selectedPage}
                    onChange={(event) => {
                      const next = Number(event.target.value);
                      setStaged((current) =>
                        current.map((row) =>
                          row.id === item.id
                            ? { ...row, selectedPage: Number.isFinite(next) ? next : 1 }
                            : row,
                        ),
                      );
                    }}
                    className="h-7 w-14 rounded-lg border border-slate-200 bg-white px-2 text-xs text-center font-medium shadow-xs"
                  />
                  页
                </label>
              ) : item.file.type.startsWith("image/") ||
                /\.(png|jpe?g|webp|tiff?)$/i.test(item.file.name) ? (
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500 font-mono">IMAGE</span>
              ) : (
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">待校验</span>
              )}
              <button
                type="button"
                className="text-xs text-red-500 hover:text-red-700 transition font-medium"
                onClick={() => setStaged((current) => current.filter((row) => row.id !== item.id))}
              >
                移除
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          disabled={pending || staged.length === 0}
          onClick={() => {
            void onSubmit();
          }}
          className="btn-primary-capsule h-9 px-5 text-xs text-white disabled:opacity-50 cursor-pointer"
        >
          {pending
            ? "上传并读图取数中…"
            : staged.length > 1
              ? `上传 ${staged.length} 张零件图`
              : "上传零件图"}
        </button>
        {staged.length > 0 ? (
          <button
            type="button"
            disabled={pending}
            onClick={() => setStaged([])}
            className="btn-secondary-capsule h-9 px-4 text-xs text-slate-600 cursor-pointer"
          >
            清空
          </button>
        ) : null}
      </div>

      {messages.map((message) => (
        <p key={message} className="mt-3 text-xs font-semibold text-emerald-700">
          ✓ {message}
        </p>
      ))}
      {errors.map((message) => (
        <p key={message} className="mt-2 text-xs font-medium text-red-600" role="alert">
          ⚠ {message}
        </p>
      ))}
    </section>
  );
}
