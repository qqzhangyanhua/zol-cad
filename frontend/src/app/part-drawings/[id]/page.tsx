import { notFound, redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { AssignQuoteTaskPanel } from "@/components/AssignQuoteTaskPanel";
import { CadDrawingReviewSummary } from "@/components/CadDrawingReviewSummary";
import { ExtractionDisclaimer } from "@/components/ExtractionDisclaimer";
import { OriginalDrawingViewer } from "@/components/OriginalDrawingViewer";
import { PartDrawingQualityPanel } from "@/components/PartDrawingQualityPanel";
import { PartDrawingWorkspace } from "@/components/PartDrawingWorkspace";
import { fetchBackend } from "@/lib/backend";
import {
  parseCurrentUser,
  parseFactoryPreferences,
  parseOriginalAccess,
  parsePartDrawing,
  parseQuoteTaskList,
  resolveOriginalSrc,
} from "@/lib/types";

type PartDrawingDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function PartDrawingDetailPage({ params }: PartDrawingDetailPageProps) {
  const { id } = await params;
  const [meResponse, drawingResponse, originalResponse, tasksResponse, prefsResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend(`/part-drawings/${id}`),
    fetchBackend(`/part-drawings/${id}/original`),
    fetchBackend("/quote-tasks"),
    fetchBackend("/factory-preferences"),
  ]);

  if (
    meResponse.status === 401 ||
    drawingResponse.status === 401 ||
    tasksResponse.status === 401 ||
    prefsResponse.status === 401
  ) {
    redirect("/login");
  }
  if (drawingResponse.status === 404 || originalResponse.status === 404) {
    notFound();
  }
  if (
    !meResponse.ok ||
    !drawingResponse.ok ||
    !originalResponse.ok ||
    !tasksResponse.ok ||
    !prefsResponse.ok
  ) {
    throw new Error("无法读取零件图原图");
  }

  const user = parseCurrentUser(await meResponse.json());
  const drawing = parsePartDrawing(await drawingResponse.json());
  const original = parseOriginalAccess(await originalResponse.json());
  const tasks = parseQuoteTaskList(await tasksResponse.json());
  const prefs = parseFactoryPreferences(await prefsResponse.json());
  const originalSrc = resolveOriginalSrc(original.url);
  const showWorkspace =
    drawing.status === "已上传" ||
    drawing.status === "分级中" ||
    drawing.status === "已分级" ||
    drawing.status === "提取中" ||
    drawing.status === "已提取" ||
    drawing.status === "提取失败" ||
    drawing.status === "复核中" ||
    drawing.status === "已复核";

  const taskName = tasks.items.find((t) => t.id === drawing.quote_task_id)?.name;

  return (
    <AppShell user={user}>
      <AppHeader
        projectCode={taskName}
        title={drawing.original_filename}
        backHref="/part-drawings"
        backLabel="零件图列表"
        subtitle={`上传于 ${new Date(drawing.uploaded_at).toLocaleString("zh-CN")}${
          drawing.content_type === "application/pdf"
            ? ` · 指定处理第 ${drawing.selected_page} 页（共 ${drawing.page_count} 页）`
            : ""
        }`}
      />

      <main className="flex flex-1 flex-col gap-4 pb-8">
        {/* Quick Assignment & Warnings */}
        <AssignQuoteTaskPanel
          drawingId={drawing.id}
          currentTaskId={drawing.quote_task_id}
          tasks={tasks.items}
        />
        <ExtractionDisclaimer text={drawing.look_at_drawing_disclaimer} />
        <PartDrawingQualityPanel drawing={drawing} />

        <CadDrawingReviewSummary drawing={drawing} />

        {/* Detailed CAD/PDF Viewer & Field Review Workspace */}
        <div id="drawing-workspace" className="mt-2">
          <div className="mb-3 px-1">
            <h2 className="text-sm font-bold text-slate-800">图纸工作台与字段复核</h2>
            <p className="text-xs text-slate-500">缩放查看 CAD/PDF 原始图面并核对抽取字段</p>
          </div>
          {showWorkspace ? (
            <PartDrawingWorkspace
              drawing={drawing}
              originalSrc={originalSrc}
              original={original}
              materialCandidates={prefs.common_materials}
              riskLabelPriority={prefs.risk_label_priority}
            />
          ) : (
            <div className="glass-card overflow-hidden">
              <OriginalDrawingViewer
                src={originalSrc}
                contentType={original.content_type}
                filename={original.original_filename}
              />
            </div>
          )}
        </div>
      </main>
    </AppShell>
  );
}
