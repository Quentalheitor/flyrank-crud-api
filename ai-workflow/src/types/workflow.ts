import type { DecisionNodeType } from "@/components/flow/decision-node";
import type { DecisionEdgeType } from "@/components/flow/decision-edge";

export type WorkflowExecutionPayload = {
  workflowId: string;
  inputContext: string; 
  nodes: DecisionNodeType[];
  edges: DecisionEdgeType[];
  startNodeId?: string;
};

export type NodeExecutionResult = {
  nodeId: string;
  nodeTitle: string;
  prompt: string;
  decision: "YES" | "NO";
  reasoning?: string;
  timestamp: string;
};

export type WorkflowExecutionReport = {
  workflowId: string;
  status: "completed" | "failed";
  executionPath: string[];
  stepResults: Record<string, NodeExecutionResult>;
  error?: string;
};