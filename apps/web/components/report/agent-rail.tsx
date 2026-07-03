"use client";

import { motion } from "framer-motion";
import { Check, Loader2, Circle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentProgress } from "@/types/report";

const ICON = {
  pending: Circle,
  running: Loader2,
  done: Check,
  error: AlertTriangle,
} as const;

export function AgentRail({ agents }: { agents: AgentProgress[] }) {
  return (
    <ol className="flex flex-col gap-1">
      {agents.map((a, i) => {
        const Icon = ICON[a.state];
        return (
          <motion.li
            key={a.key}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm",
              a.state === "running" && "bg-primary/10",
            )}
          >
            <span
              className={cn(
                "grid size-6 shrink-0 place-items-center rounded-full border",
                a.state === "done" &&
                  "border-conf-high/40 bg-conf-high/15 text-conf-high",
                a.state === "running" &&
                  "border-primary/40 bg-primary/15 text-primary",
                a.state === "pending" &&
                  "border-border text-muted-foreground",
                a.state === "error" &&
                  "border-conf-verylow/40 bg-conf-verylow/15 text-conf-verylow",
              )}
            >
              <Icon
                className={cn("size-3.5", a.state === "running" && "animate-spin")}
              />
            </span>
            <span
              className={cn(
                "flex-1",
                a.state === "pending" && "text-muted-foreground",
              )}
            >
              {a.label}
            </span>
            {a.detail && (
              <span className="text-xs text-muted-foreground">{a.detail}</span>
            )}
          </motion.li>
        );
      })}
    </ol>
  );
}
