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
    <section className="border-b border-stone-200 bg-white px-6 py-5">
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
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragOver ? "border-stone-700 bg-stone-50" : "border-stone-300 bg-stone-50/60 hover:border-stone-400"
        }`}
      >
        <p className="text-sm font-medium text-stone-800">
          拖拽零件图到这里，或<span className="underline">选择文件</span>
        </p>
        <p className="mt-2 max-w-lg text-xs leading-5 text-stone-500">
          支持 PDF、JPEG、PNG、WebP、TIFF · 单文件不超过 {MAX_FILE_SIZE_MB} MB · PDF 不超过{" "}
          {MAX_PDF_PAGES} 页 · 可一次选多张。装配图、爆炸图不在处理范围，请只上传单个零件的零件图。
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
        <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900">
          多页 PDF 只处理你指定的那一页，默认第 1 页。后面的读图取数不会看其他页。
        </p>
      ) : null}

      {staged.length > 0 ? (
        <ul className="mt-4 divide-y divide-stone-100 rounded-lg border border-stone-200">
          {staged.map((item) => (
            <li key={item.id} className="flex flex-wrap items-center gap-3 px-3 py-2.5">
              <span className="min-w-0 flex-1 truncate text-sm text-stone-800">{item.file.name}</span>
              {isPdfFile(item.file) ? (
                <label className="flex items-center gap-2 text-xs text-stone-600">
                  处理第
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
                    className="h-8 w-16 rounded-md border border-stone-200 px-2 text-sm"
                  />
                  页
                </label>
              ) : item.file.type.startsWith("image/") ||
                /\.(png|jpe?g|webp|tiff?)$/i.test(item.file.name) ? (
                <span className="text-xs text-stone-400">图片</span>
              ) : (
                <span className="text-xs text-stone-400">待校验</span>
              )}
              <button
                type="button"
                className="text-xs text-stone-500 hover:text-stone-800"
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
          className="h-10 rounded-lg bg-stone-900 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-50"
        >
          {pending ? "上传中…" : staged.length > 1 ? `上传 ${staged.length} 张零件图` : "上传零件图"}
        </button>
        {staged.length > 0 ? (
          <button
            type="button"
            disabled={pending}
            onClick={() => setStaged([])}
            className="h-10 rounded-lg px-3 text-sm text-stone-600 hover:bg-stone-100"
          >
            清空
          </button>
        ) : null}
      </div>

      {messages.map((message) => (
        <p key={message} className="mt-3 text-sm text-emerald-700">
          {message}
        </p>
      ))}
      {errors.map((message) => (
        <p key={message} className="mt-2 text-sm text-red-600" role="alert">
          {message}
        </p>
      ))}
    </section>
  );
}
