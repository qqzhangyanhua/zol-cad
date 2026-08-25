import { AddCriticalDimensionForm } from "@/components/AddCriticalDimensionForm";
import { RetryExtractionButton } from "@/components/RetryExtractionButton";
import { ReviewFieldRow } from "@/components/ReviewFieldRow";
import { ReviewProgress } from "@/components/ReviewProgress";
import { FIELD_CATEGORIES, type ExtractedField, type FieldCategory, type PartDrawing } from "@/lib/types";

type ReviewFormProps = {
  drawing: PartDrawing;
  materialCandidates: string[];
};

const CATEGORY_HINT: Record<FieldCategory, string> = {
  标题栏: "从图纸标题栏抄出的字段",
  关键尺寸: "驱动成本的尺寸与公差，不是全图标注",
  技术要求: "热处理、表面处理、粗糙度等图面要求",
};

function fieldsForCategory(fields: ExtractedField[], category: FieldCategory): ExtractedField[] {
  return fields.filter((field) => field.category === category);
}

export function ReviewForm({ drawing, materialCandidates }: ReviewFormProps) {
  const readOnly = drawing.status === "已复核";
  return (
    <div className="space-y-6" aria-label="复核提取结果">
      <ReviewProgress
        key={`${drawing.pending_confirmation_count}:${drawing.pending_confirmation_labels.join(",")}`}
        drawingId={drawing.id}
        pendingCount={drawing.pending_confirmation_count}
        pendingLabels={drawing.pending_confirmation_labels}
        reviewed={readOnly}
      />
      {FIELD_CATEGORIES.map((category) => {
        const items = fieldsForCategory(drawing.extracted_fields, category);
        if (items.length === 0) {
          return null;
        }
        return (
          <section key={category} aria-labelledby={`review-group-${category}`}>
            <div className="mb-3">
              <h2 id={`review-group-${category}`} className="text-sm font-semibold text-stone-900">
                {category}
              </h2>
              <p className="mt-0.5 text-xs text-stone-500">{CATEGORY_HINT[category]}</p>
            </div>
            <div className="space-y-2">
              {items.map((field) => (
                <ReviewFieldRow
                  key={`${field.key}:${field.value ?? ""}:${String(field.confirmed)}:${String(field.ignored)}`}
                  drawingId={drawing.id}
                  field={field}
                  readOnly={readOnly}
                  materialCandidates={materialCandidates}
                />
              ))}
            </div>
            {category === "关键尺寸" && !readOnly ? (
              <div className="mt-3">
                <AddCriticalDimensionForm drawingId={drawing.id} />
              </div>
            ) : null}
          </section>
        );
      })}
      {!readOnly ? (
        <div className="rounded-lg border border-stone-200 bg-white px-3 py-3">
          <p className="text-xs text-stone-500">
            重试读图取数不会覆盖已确认、已忽略或手工补录的项。
          </p>
          <div className="mt-2">
            <RetryExtractionButton drawingId={drawing.id} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
