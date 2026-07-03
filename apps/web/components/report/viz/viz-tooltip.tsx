"use client";

import type { ReactNode } from "react";
import { useCallback, useState } from "react";
import { createPortal } from "react-dom";

export interface Tip {
  x: number;
  y: number;
  content: ReactNode;
}

/** Cursor-following tooltip state shared by the evidence charts. */
export function useTip() {
  const [tip, setTip] = useState<Tip | null>(null);
  const show = useCallback((e: { clientX: number; clientY: number }, content: ReactNode) => {
    setTip({ x: e.clientX, y: e.clientY, content });
  }, []);
  const hide = useCallback(() => setTip(null), []);
  return { tip, show, hide };
}

export function TipLayer({ tip }: { tip: Tip | null }) {
  if (!tip || typeof document === "undefined") return null;
  return createPortal(
    <div
      className="pointer-events-none fixed z-50 max-w-[240px] rounded-md border border-border bg-card px-2.5 py-1.5 text-xs leading-snug text-card-foreground shadow-lg"
      style={{ left: tip.x + 14, top: tip.y + 14 }}
      role="tooltip"
    >
      {tip.content}
    </div>,
    document.body,
  );
}
