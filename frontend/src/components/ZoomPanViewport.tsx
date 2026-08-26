"use client";

import type { PointerEvent, ReactNode, WheelEvent } from "react";
import { useRef, useState } from "react";

type ZoomPanViewportProps = {
  children: ReactNode;
};

const MIN_SCALE = 0.25;
const MAX_SCALE = 8;

export function ZoomPanViewport({ children }: ZoomPanViewportProps) {
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef<{ x: number; y: number; originX: number; originY: number } | null>(
    null,
  );

  function clampScale(value: number): number {
    return Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));
  }

  function onWheel(event: WheelEvent<HTMLDivElement>): void {
    event.preventDefault();
    const next = clampScale(scale * (event.deltaY < 0 ? 1.12 : 0.9));
    setScale(next);
  }

  function onPointerDown(event: PointerEvent<HTMLDivElement>): void {
    dragging.current = {
      x: event.clientX,
      y: event.clientY,
      originX: offset.x,
      originY: offset.y,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function onPointerMove(event: PointerEvent<HTMLDivElement>): void {
    if (!dragging.current) {
      return;
    }
    setOffset({
      x: dragging.current.originX + event.clientX - dragging.current.x,
      y: dragging.current.originY + event.clientY - dragging.current.y,
    });
  }

  function onPointerUp(): void {
    dragging.current = null;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center gap-2 border-b border-slate-200/80 bg-white/60 px-4 py-2 backdrop-blur-md">
        <button
          type="button"
          className="btn-secondary-capsule h-7 px-3 text-xs text-slate-700 cursor-pointer"
          onClick={() => setScale((value) => clampScale(value * 1.2))}
        >
          放大
        </button>
        <button
          type="button"
          className="btn-secondary-capsule h-7 px-3 text-xs text-slate-700 cursor-pointer"
          onClick={() => setScale((value) => clampScale(value / 1.2))}
        >
          缩小
        </button>
        <button
          type="button"
          className="btn-secondary-capsule h-7 px-3 text-xs text-slate-700 cursor-pointer"
          onClick={() => {
            setScale(1);
            setOffset({ x: 0, y: 0 });
          }}
        >
          重置
        </button>
        <span className="text-xs font-mono font-medium text-slate-600 ml-2">{Math.round(scale * 100)}%</span>
        <span className="ml-auto text-[11px] text-slate-400">💡 滚轮缩放 · 拖拽平移</span>
      </div>
      <div
        className="relative min-h-0 flex-1 cursor-grab overflow-hidden bg-slate-200/40 blueprint-grid-bg touch-none active:cursor-grabbing"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
            transformOrigin: "center center",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
