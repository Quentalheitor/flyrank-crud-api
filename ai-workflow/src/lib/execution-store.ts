import type { NodeExecutionResult } from "@/types/workflow";

export type ExecutionState = {
  workflowId: string;
  status: "idle" | "running" | "completed" | "failed";
  inputContext: string;
  executionPath: string[];
  stepResults: Record<string, NodeExecutionResult>;
  error?: string;
};

// TypeScript pattern: preserve global across hot reloads in Next.js development
declare global {
  // eslint-disable-next-line no-var
  var __workflow_runs__: Map<string, ExecutionState> | undefined;
}

export const executionStore: Map<string, ExecutionState> =
  globalThis.__workflow_runs__ ?? (globalThis.__workflow_runs__ = new Map());