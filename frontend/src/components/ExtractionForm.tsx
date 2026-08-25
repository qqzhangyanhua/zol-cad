import { FIELD_CATEGORIES, type ExtractedField, type FieldCategory } from "@/lib/types";

type ExtractionFormProps = {
  fields: ExtractedField[];
};

const CATEGORY_HINT: Record<FieldCategory, string> = {
  标题栏: "从图纸标题栏抄出的字段",
  关键尺寸: "驱动成本的尺寸与公差，不是全图标注",
  技术要求: "热处理、表面处理、粗糙度等图面要求",
};

function fieldsForCategory(fields: ExtractedField[], category: FieldCategory): ExtractedField[] {
  return fields.filter((field) => field.category === category);
}

export function ExtractionForm({ fields }: ExtractionFormProps) {
  return (
    <form className="space-y-6" aria-label="读图取数结果">
      {FIELD_CATEGORIES.map((category) => {
        const items = fieldsForCategory(fields, category);
        if (items.length === 0) {
          return null;
        }
        return (
          <section key={category} aria-labelledby={`field-group-${category}`}>
            <div className="mb-3">
              <h2
                id={`field-group-${category}`}
                className="text-sm font-semibold text-stone-900"
              >
                {category}
              </h2>
              <p className="mt-0.5 text-xs text-stone-500">{CATEGORY_HINT[category]}</p>
            </div>
            <dl className="space-y-2">
              {items.map((field) => (
                <div
                  key={field.key}
                  className="grid grid-cols-[7rem_minmax(0,1fr)] items-start gap-3 rounded-lg border border-stone-200 bg-white px-3 py-2.5"
                >
                  <dt className="pt-0.5 text-xs text-stone-500">
                    <span className="block font-medium text-stone-800">{field.label}</span>
                    <span className="mt-0.5 block text-[11px] text-stone-400">{category}</span>
                  </dt>
                  <dd className="min-h-8 rounded-md bg-stone-50 px-2.5 py-1.5 text-sm text-stone-900">
                    {field.value === null || field.value === "" ? (
                      <span className="text-stone-400">（空）</span>
                    ) : (
                      field.value
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        );
      })}
    </form>
  );
}
