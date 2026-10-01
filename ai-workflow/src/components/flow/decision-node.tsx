"use client";

import React, { useCallback } from "react";
import {
  Handle,
  Position,
  type NodeProps,
  type Node,
  useReactFlow,
} from "@xyflow/react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

export type DecisionNodeData = {
  title?: string;
  evaluationCriteria: string;
  status?: "idle" | "running" | "completed" | "failed";
  lastResult?: "YES" | "NO";
};

export type DecisionNodeType = Node<DecisionNodeData, "decisionNode">;

export default function DecisionNode({ id, data }: NodeProps<DecisionNodeType>) {
  const { setNodes } = useReactFlow();

  const handleCriteriaChange = useCallback(
    (evt: React.ChangeEvent<HTMLTextAreaElement>) => {
      const nextValue = evt.target.value;
      setNodes((nodes) =>
        nodes.map((node) => {
          if (node.id === id) {
            return {
              ...node,
              data: {
                ...node.data,
                evaluationCriteria: nextValue,
              },
            };
          }
          return node;
        })
      );
    },
    [id, setNodes]
  );

  // Dynamic styling based on execution status
  const getCardBorderClass = () => {
    switch (data.status) {
      case "running":
        return "ring-2 ring-amber-500 shadow-amber-500/20 shadow-lg animate-pulse";
      case "completed":
        return "ring-2 ring-primary/80 shadow-md";
      case "failed":
        return "ring-2 ring-destructive shadow-destructive/20 shadow-md";
      default:
        return "border-border shadow-md";
    }
  };

  return (
    <Card
      className={`w-80 bg-card text-card-foreground overflow-visible relative transition-all duration-300 ${getCardBorderClass()}`}
    >
      {/* Target Handle (Top) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-4 !h-4 !bg-slate-400 !border-2 !border-background hover:!bg-primary transition-transform hover:scale-125 !cursor-crosshair shadow-sm"
        style={{ top: -8 }}
      />

      <CardHeader className="py-3 px-4 flex flex-row items-center justify-between border-b">
        <div className="flex items-center gap-2">
          {data.status === "running" && (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500" />
          )}
          <CardTitle className="text-sm font-semibold tracking-wide">
            {data.title || "Decision Step"}
          </CardTitle>
        </div>

        {data.lastResult && (
          <Badge
            variant={data.lastResult === "YES" ? "default" : "destructive"}
            className="text-[10px] uppercase font-bold"
          >
            {data.lastResult}
          </Badge>
        )}
      </CardHeader>

      <CardContent className="p-4 space-y-2">
        <label
          htmlFor={`criteria-${id}`}
          className="text-xs font-medium text-muted-foreground block"
        >
          Evaluation Prompt (LLM evaluates to YES / NO):
        </label>
        <Textarea
          id={`criteria-${id}`}
          value={data.evaluationCriteria ?? ""}
          onChange={handleCriteriaChange}
          placeholder="e.g. Is this request asking for technical support?"
          className="text-xs resize-none nodrag nowheel min-h-[72px]"
        />
      </CardContent>

      {/* YES / NO Footers */}
      <div className="grid grid-cols-2 border-t bg-muted/20 py-2.5 px-4 text-xs font-bold select-none">
        <div className="text-center text-emerald-600 dark:text-emerald-400">
          YES
        </div>
        <div className="text-center text-rose-600 dark:text-rose-400">
          NO
        </div>
      </div>

      {/* Bottom Source Handles */}
      <Handle
        id="yes"
        type="source"
        position={Position.Bottom}
        style={{ left: "25%", bottom: -8 }}
        className="!w-4 !h-4 !bg-emerald-500 !border-2 !border-background shadow-md hover:scale-125 transition-transform !cursor-crosshair before:absolute before:-inset-2 before:content-['']"
      />

      <Handle
        id="no"
        type="source"
        position={Position.Bottom}
        style={{ left: "75%", bottom: -8 }}
        className="!w-4 !h-4 !bg-rose-500 !border-2 !border-background shadow-md hover:scale-125 transition-transform !cursor-crosshair before:absolute before:-inset-2 before:content-['']"
      />
    </Card>
  );
}