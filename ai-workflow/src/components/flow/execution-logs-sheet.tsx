"use client";

import React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { ExecutionState } from "@/lib/execution-store";
import { Clock, CheckCircle2, AlertCircle } from "lucide-react";

interface ExecutionLogsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  execution: ExecutionState | null;
}

export default function ExecutionLogsSheet({
  open,
  onOpenChange,
  execution,
}: ExecutionLogsSheetProps) {
  if (!execution) return null;

  const results = Object.values(execution.stepResults || {});

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md w-full overflow-y-auto">
        <SheetHeader className="pb-4 border-b">
          <div className="flex items-center justify-between pr-6">
            <SheetTitle className="text-base font-bold">Execution Logs</SheetTitle>
            <Badge
              variant={execution.status === "completed" ? "default" : "secondary"}
              className="uppercase text-[10px]"
            >
              {execution.status}
            </Badge>
          </div>
          <SheetDescription className="text-xs">
            Workflow Run ID: <span className="font-mono">{execution.workflowId}</span>
          </SheetDescription>
        </SheetHeader>

        <div className="py-4 space-y-4 text-xs">
          {/* Input Context Box */}
          <div className="p-3 bg-muted/40 rounded-lg border space-y-1">
            <span className="font-semibold text-foreground block">Evaluated Input:</span>
            <p className="text-muted-foreground italic font-mono text-[11px] leading-relaxed">
              "{execution.inputContext}"
            </p>
          </div>

          {/* Traversal Summary */}
          <div className="space-y-1">
            <span className="font-semibold text-foreground">Execution Path ({execution.executionPath.length} steps):</span>
            <div className="font-mono text-[11px] text-muted-foreground flex flex-wrap items-center gap-1.5 pt-1">
              {execution.executionPath.map((nodeId, idx) => (
                <React.Fragment key={nodeId}>
                  <span className="bg-muted px-2 py-0.5 rounded border border-border">
                    {nodeId}
                  </span>
                  {idx < execution.executionPath.length - 1 && <span>→</span>}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Step-by-Step Decision Cards */}
          <div className="space-y-3 pt-2">
            <span className="font-semibold text-foreground">Step Breakdown:</span>
            {results.length === 0 ? (
              <p className="text-muted-foreground italic">No steps recorded yet.</p>
            ) : (
              results.map((step, idx) => (
                <Card key={step.nodeId} className="border-border shadow-xs">
                  <CardHeader className="py-2.5 px-3 flex flex-row items-center justify-between border-b bg-muted/20">
                    <CardTitle className="text-xs font-semibold flex items-center gap-1.5">
                      <span className="text-muted-foreground font-mono">#{idx + 1}</span>
                      {step.nodeTitle}
                    </CardTitle>
                    <Badge
                      variant={step.decision === "YES" ? "default" : "destructive"}
                      className="text-[10px] font-bold"
                    >
                      {step.decision}
                    </Badge>
                  </CardHeader>
                  <CardContent className="p-3 space-y-1.5 text-[11px]">
                    <div>
                      <span className="text-muted-foreground font-medium">Prompt: </span>
                      <span className="text-foreground">{step.prompt}</span>
                    </div>
                    {step.reasoning && (
                      <div>
                        <span className="text-muted-foreground font-medium">Note: </span>
                        <span className="italic text-amber-600 dark:text-amber-400">
                          {step.reasoning}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground pt-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(step.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}