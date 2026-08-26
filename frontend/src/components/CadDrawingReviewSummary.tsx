"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangleIcon,
  CalendarIcon,
  CheckCircleIcon,
  ExportIcon,
  HistoryQuoteIcon,
  SaveDraftIcon,
  SubmitIcon,
} from "@/components/Icons";
import type { PartDrawing } from "@/lib/types";

type CadDrawingReviewSummaryProps = {
  drawing: PartDrawing;
  onScrollToForm?: () => void;
};

export function CadDrawingReviewSummary({ drawing, onScrollToForm }: CadDrawingReviewSummaryProps) {
  const [selectedBatch, setSelectedBatch] = useState<number>(1000);

  // Extract key field values with fallback
  const materialField = drawing.extracted_fields.find((f) => f.key === "material")?.value || "AL6061-T6";
  const partNumber = drawing.extracted_fields.find((f) => f.key === "drawing_number")?.value || drawing.original_filename.replace(/\.[^/.]+$/, "");

  // Dynamic calculations based on extracted info or reasonable engineering defaults
  const riskCount = drawing.risk_labels.length;
  const riskScore = useMemo(() => {
    if (riskCount === 0) return 3.5;
    return Math.min(9.5, Number((5.5 + riskCount * 0.85).toFixed(1)));
  }, [riskCount]);

  const riskLevel = riskScore > 7.0 ? "高风险" : riskScore > 5.0 ? "中等风险" : "低风险";

  // Base pricing simulation based on batch
  const batchPrices: Record<number, number> = {
    100: 2450.8,
    500: 2012.6,
    1000: 1856.4,
    5000: 1528.7,
  };

  const currentPrice = batchPrices[selectedBatch] || 1856.4;

  const costBreakdown = useMemo(() => {
    const ratio = currentPrice / 1856.4;
    return {
      material: (412.6 * ratio).toFixed(1),
      machining: (1103.8 * ratio).toFixed(1),
      surface: (126.0 * ratio).toFixed(1),
      testing: (84.0 * ratio).toFixed(1),
      subtotal: currentPrice.toFixed(1),
    };
  }, [currentPrice]);

  return (
    <div className="flex flex-col gap-4">
      {/* Top Main Bento Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Left 8 Cols: Blueprint & Review Main Card */}
        <div className="glass-card relative flex flex-col justify-between overflow-hidden p-6 lg:col-span-8 backdrop-blur-xl">
          {/* Blueprint SVG watermark background */}
          <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 opacity-15">
            <svg width="340" height="260" viewBox="0 0 340 260" fill="none" stroke="#2563eb" strokeWidth="1.2">
              {/* CAD technical drawing outlines */}
              <circle cx="170" cy="130" r="100" strokeDasharray="4 4" />
              <circle cx="170" cy="130" r="70" />
              <circle cx="170" cy="130" r="35" />
              <rect x="50" y="50" width="240" height="160" rx="8" strokeDasharray="6 3" />
              <line x1="20" y1="130" x2="320" y2="130" strokeDasharray="3 3" />
              <line x1="170" y1="10" x2="170" y2="250" strokeDasharray="3 3" />
              <circle cx="95" cy="75" r="12" />
              <circle cx="245" cy="75" r="12" />
              <circle cx="95" cy="185" r="12" />
              <circle cx="245" cy="185" r="12" />
            </svg>
          </div>

          <div>
            {/* Card Header */}
            <div className="flex items-center justify-between border-b border-slate-100/80 pb-4">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">图纸评审</h3>
                <span className="flex h-4.5 w-4.5 items-center justify-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-500">
                  i
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span>图纸版本: <strong className="text-slate-800 font-semibold">V2.1</strong></span>
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-slate-600 font-medium cursor-pointer hover:bg-slate-200">
                  变更 ⌃
                </span>
              </div>
            </div>

            {/* Metrics Matrix */}
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="glass-card-subtle p-3">
                <p className="text-xs text-slate-400">材料</p>
                <p className="mt-1 text-base font-bold text-slate-900">{materialField}</p>
                <p className="text-[11px] text-slate-500">铝合金</p>
              </div>
              <div className="glass-card-subtle p-3">
                <p className="text-xs text-slate-400">净重</p>
                <p className="mt-1 text-base font-bold text-slate-900 font-mono">2.348 <span className="text-xs font-normal text-slate-500">kg</span></p>
                <p className="text-[11px] text-slate-500">精加工后</p>
              </div>
              <div className="glass-card-subtle p-3">
                <p className="text-xs text-slate-400">毛重</p>
                <p className="mt-1 text-base font-bold text-slate-900 font-mono">2.812 <span className="text-xs font-normal text-slate-500">kg</span></p>
                <p className="text-[11px] text-slate-500">胚料毛坯</p>
              </div>
              <div className="glass-card-subtle p-3">
                <p className="text-xs text-slate-400">总体积</p>
                <p className="mt-1 text-base font-bold text-slate-900 font-mono">318.7 <span className="text-xs font-normal text-slate-500">cm³</span></p>
                <p className="text-[11px] text-slate-500">外廓包络</p>
              </div>
            </div>

            {/* Manufacturing Risk Row */}
            <div className="mt-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800">制造风险</span>
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500 animate-pulse" />
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-xs text-slate-500">风险评分</span>
                  <span className="text-xl font-black text-amber-600 font-mono">{riskScore}</span>
                  <span className="text-xs text-slate-400">/ 10</span>
                </div>
              </div>

              {/* Warning Pills Grid */}
              <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {drawing.risk_labels.length > 0 ? (
                  drawing.risk_labels.slice(0, 4).map((label) => (
                    <div key={label.rule_id} className="glass-warning-pill p-2.5 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-900">
                        <AlertTriangleIcon className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                        <span className="truncate">{label.name}</span>
                      </div>
                      <p className="mt-1 truncate text-[11px] text-amber-800/90">{label.triggering_value || label.reason}</p>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="glass-warning-pill p-2.5 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-900">
                        <AlertTriangleIcon className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                        <span>薄壁风险</span>
                      </div>
                      <p className="mt-1 text-[11px] text-amber-800/90">多处壁厚 &lt; 2.0mm</p>
                    </div>
                    <div className="glass-warning-pill p-2.5 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-900">
                        <AlertTriangleIcon className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                        <span>深孔加工</span>
                      </div>
                      <p className="mt-1 text-[11px] text-amber-800/90">ф6.0 深径比 &gt; 6</p>
                    </div>
                    <div className="glass-warning-pill p-2.5 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-900">
                        <AlertTriangleIcon className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                        <span>公差累积</span>
                      </div>
                      <p className="mt-1 text-[11px] text-amber-800/90">关键尺寸链较紧</p>
                    </div>
                    <div className="glass-warning-pill p-2.5 text-xs">
                      <div className="flex items-center gap-1.5 font-bold text-amber-900">
                        <AlertTriangleIcon className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                        <span>材料去除率</span>
                      </div>
                      <p className="mt-1 text-[11px] text-amber-800/90">局部 &gt; 85%</p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Review Bullet Points */}
            <div className="mt-5 border-t border-slate-100/80 pt-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">评审要点</h4>
              <ul className="mt-2.5 space-y-2 text-xs text-slate-700">
                <li className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-emerald-500 shrink-0" />
                  <span>建议增加内圆角 R1.5 以降低应力集中与走刀磨损</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-emerald-500 shrink-0" />
                  <span>3x M6 螺纹孔建议改为通孔以优化攻丝加工</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-emerald-500 shrink-0" />
                  <span>关键尺寸（42.00 ±0.02）需确保对刀与三坐标测量基准</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircleIcon className="h-4 w-4 text-emerald-500 shrink-0" />
                  <span>表面处理建议：本色阳极氧化（耐腐蚀 + 耐磨）</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Footer Action */}
          <div className="mt-5 flex justify-end">
            <button
              type="button"
              onClick={onScrollToForm}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 cursor-pointer"
            >
              查看完整提取与复核表单 →
            </button>
          </div>
        </div>

        {/* Right 4 Cols: Quote Summary & Insight Card */}
        <div className="glass-card flex flex-col justify-between p-6 lg:col-span-4 backdrop-blur-xl">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100/80 pb-3">
              <h3 className="text-sm font-bold text-slate-900">报价摘要（估算）</h3>
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                试制批量
              </span>
            </div>

            {/* Price Display */}
            <div className="mt-4">
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold text-slate-900">¥</span>
                <span className="text-3xl font-black tracking-tight text-slate-900 font-mono">
                  {costBreakdown.subtotal}
                </span>
                <span className="text-xs font-medium text-slate-500">/ 件</span>
              </div>
              <div className="mt-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100/70 border border-amber-200/80 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                  {riskLevel}
                </span>
              </div>
            </div>

            {/* Cost Breakdown Details */}
            <div className="mt-5 space-y-2.5 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span>材料成本</span>
                <span className="font-mono text-slate-900 font-semibold">¥ {costBreakdown.material}</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>加工成本</span>
                <span className="font-mono text-slate-900 font-semibold">¥ {costBreakdown.machining}</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>表面处理</span>
                <span className="font-mono text-slate-900 font-semibold">¥ {costBreakdown.surface}</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>检测与包装</span>
                <span className="font-mono text-slate-900 font-semibold">¥ {costBreakdown.testing}</span>
              </div>
              <div className="border-t border-slate-200/80 pt-2.5 flex items-center justify-between font-bold text-slate-900">
                <span>小计（未税）</span>
                <span className="font-mono text-base">¥ {costBreakdown.subtotal}</span>
              </div>
            </div>

            {/* Quote Insight Card */}
            <div className="glass-card-subtle mt-5 p-3.5">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-slate-800">
                <span className="text-blue-600 font-bold">📊 报价洞察</span>
              </div>
              <p className="mt-1.5 text-[11px] leading-4.5 text-slate-600">
                与历史同类项目相比，加工成本高出约 12%，主要来自深孔加工与局部薄壁放慢进给。
              </p>
              <div className="mt-3 flex justify-end">
                <button
                  type="button"
                  onClick={onScrollToForm}
                  className="text-[11px] font-semibold text-blue-600 hover:text-blue-700"
                >
                  调整参数与重新计算 →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row Bento Tiles */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-12">
        {/* Ladder Pricing (6 cols) */}
        <div className="glass-card p-5 md:col-span-6 backdrop-blur-xl">
          <div className="flex items-center justify-between pb-3">
            <h4 className="text-xs font-bold text-slate-800">批量价格参考</h4>
            <span className="text-[11px] text-slate-400">阶梯单价</span>
          </div>
          <div className="grid grid-cols-4 gap-2 pt-1">
            {[100, 500, 1000, 5000].map((batch) => {
              const active = selectedBatch === batch;
              return (
                <button
                  key={batch}
                  type="button"
                  onClick={() => setSelectedBatch(batch)}
                  className={`flex flex-col items-center justify-center rounded-xl p-2.5 text-center transition cursor-pointer ${
                    active
                      ? "bg-amber-100/70 border border-amber-300 text-amber-900 shadow-xs font-semibold"
                      : "glass-card-subtle text-slate-700 hover:bg-white/80"
                  }`}
                >
                  <span className="text-xs">{batch} 件</span>
                  <span className="mt-1 font-mono text-xs font-bold">
                    ¥ {batchPrices[batch]?.toFixed(1)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Lead Time Estimation (3 cols) */}
        <div className="glass-card p-5 md:col-span-3 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-800">交付周期（估算）</h4>
          </div>
          <div className="py-2">
            <div className="flex items-center gap-2">
              <CalendarIcon className="h-5 w-5 text-slate-700 shrink-0" />
              <span className="text-lg font-black text-slate-900 font-mono">12 - 15</span>
              <span className="text-xs text-slate-500 font-medium">工作日</span>
            </div>
            <div className="mt-2">
              <span className="inline-block rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700 border border-blue-100">
                含样件验证
              </span>
            </div>
          </div>
        </div>

        {/* Similar History Projects (3 cols) */}
        <div className="glass-card p-5 md:col-span-3 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-800">类似历史项目</h4>
            <span className="text-slate-400 text-xs">→</span>
          </div>
          <div className="py-2">
            <p className="text-sm font-bold text-slate-800">3D-VALVE-017</p>
            <div className="mt-1.5 flex items-center justify-between text-xs text-slate-500">
              <span className="font-mono font-semibold text-slate-700">¥ 1,782.0</span>
              <span className="font-mono text-[11px] text-slate-400">2024-03-11</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
