"use client";

import React from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
  type Edge,
} from "@xyflow/react";

export type DecisionEdgeData = {
  branch?: "YES" | "NO";
};

export type DecisionEdgeType = Edge<DecisionEdgeData, "decisionEdge">;

export default function DecisionEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
  style,
}: EdgeProps<DecisionEdgeType>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const isYes = data?.branch === "YES";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          strokeWidth: 2,
          stroke: isYes ? "#10b981" : "#f43f5e",
          ...style,
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
          }}
          className={`pointer-events-all nodrag absolute rounded px-1.5 py-0.5 text-[10px] font-bold shadow-xs transition-colors ${
            isYes
              ? "bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-rose-100 text-rose-800 border border-rose-300 dark:bg-rose-950 dark:text-rose-300"
          }`}
        >
          {data?.branch ?? "BRANCH"}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}