"use client";

import type { KeyboardEvent, PointerEvent, ReactNode, WheelEvent } from "react";
import { useRef, useState } from "react";

type ZoomPanViewportProps = {
  children: ReactNode;
};

const MIN_SCALE = 0.25;
const MAX_SCALE = 8;
const PAN_STEP = 40;

export function ZoomPanViewport({ children }: ZoomPanViewportProps) {
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef<{ x: number; y: number; originX: number; originY: number } | null>(
    null,
  );

  function clampScale(value: number): number {
    return Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));
  }

  function zoomBy(factor: number): void {
    setScale((value) => clampScale(value * factor));
  }

  function resetView(): void {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }

  function panBy(deltaX: number, deltaY: number): void {
    setOffset((current) => ({ x: current.x + deltaX, y: current.y + deltaY }));
  }

  function onWheel(event: WheelEvent<HTMLDivElement>): void {
    event.preventDefault();
    zoomBy(event.deltaY < 0 ? 1.12 : 0.9);
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

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      panBy(PAN_STEP, 0);
      return;
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      panBy(-PAN_STEP, 0);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      panBy(0, PAN_STEP);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      panBy(0, -PAN_STEP);
      return;
    }
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      zoomBy(1.2);
      return;
    }
    if (event.key === "-" || event.key === "_") {
      event.preventDefault();
      zoomBy(1 / 1.2);
      return;
    }
    if (event.key === "0") {
      event.preventDefault();
      resetView();
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200/80 bg-white/60 px-3 py-2 backdrop-blur-md md:px-4">
        <button
          type="button"
          aria-label="放大"
          className="btn-secondary-capsule h-7 cursor-pointer px-3 text-xs text-slate-700"
          onClick={() => {
            zoomBy(1.2);
          }}
        >
          放大
        </button>
        <button
          type="button"
          aria-label="缩小"
          className="btn-secondary-capsule h-7 cursor-pointer px-3 text-xs text-slate-700"
          onClick={() => {
            zoomBy(1 / 1.2);
          }}
        >
          缩小
        </button>
        <button
          type="button"
          aria-label="重置缩放与位置"
          className="btn-secondary-capsule h-7 cursor-pointer px-3 text-xs text-slate-700"
          onClick={resetView}
        >
          重置
        </button>
        <span className="ml-2 font-mono text-xs font-medium text-slate-600">{Math.round(scale * 100)}%</span>
        <span className="ml-auto text-[11px] text-slate-400">
          滚轮或加减键缩放 · 拖拽或方向键平移
        </span>
      </div>
      <div
        role="region"
        tabIndex={0}
        aria-label="零件图原图，可用方向键平移，加号减号缩放，数字 0 重置"
        className="blueprint-grid-bg relative min-h-0 flex-1 cursor-grab overflow-hidden bg-slate-200/40 touch-none active:cursor-grabbing"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onKeyDown={onKeyDown}
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
