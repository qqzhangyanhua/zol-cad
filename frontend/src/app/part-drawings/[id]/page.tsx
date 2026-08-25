import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { ExtractionDisclaimer } from "@/components/ExtractionDisclaimer";
import { OriginalDrawingViewer } from "@/components/OriginalDrawingViewer";
import { PartDrawingQualityPanel } from "@/components/PartDrawingQualityPanel";
import { PartDrawingWorkspace } from "@/components/PartDrawingWorkspace";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parseOriginalAccess, parsePartDrawing, resolveOriginalSrc } from "@/lib/types";

type PartDrawingDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function PartDrawingDetailPage({ params }: PartDrawingDetailPageProps) {
  const { id } = await params;
  const [meResponse, drawingResponse, originalResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend(`/part-drawings/${id}`),
    fetchBackend(`/part-drawings/${id}/original`),
  ]);

  if (meResponse.status === 401 || drawingResponse.status === 401) {
    redirect("/login");
  }
  if (drawingResponse.status === 404 || originalResponse.status === 404) {
    notFound();
  }
  if (!meResponse.ok || !drawingResponse.ok || !originalResponse.ok) {
    throw new Error("无法读取零件图原图");
  }

  const user = parseCurrentUser(await meResponse.json());
  const drawing = parsePartDrawing(await drawingResponse.json());
  const original = parseOriginalAccess(await originalResponse.json());
  const originalSrc = resolveOriginalSrc(original.url);
  const showWorkspace =
    drawing.status === "已分级" ||
    drawing.status === "提取中" ||
    drawing.status === "已提取" ||
    drawing.status === "提取失败";

  return (
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <div className="flex items-center justify-between gap-4 border-b border-stone-200 bg-white px-6 py-3">
        <div className="min-w-0">
          <Link href="/part-drawings" className="text-xs text-stone-500 hover:text-stone-800">
            ← 返回列表
          </Link>
          <h1 className="truncate text-base font-semibold text-stone-900">{drawing.original_filename}</h1>
          <p className="text-xs text-stone-500">
            上传于 {new Date(drawing.uploaded_at).toLocaleString("zh-CN")}
            {drawing.content_type === "application/pdf"
              ? ` · 指定处理第 ${drawing.selected_page} 页（共 ${drawing.page_count} 页）`
              : null}
          </p>
        </div>
      </div>
      <ExtractionDisclaimer text={drawing.look_at_drawing_disclaimer} />
      <PartDrawingQualityPanel drawing={drawing} />
      {showWorkspace ? (
        <PartDrawingWorkspace drawing={drawing} originalSrc={originalSrc} original={original} />
      ) : (
        <OriginalDrawingViewer
          src={originalSrc}
          contentType={original.content_type}
          filename={original.original_filename}
        />
      )}
    </div>
  );
}
