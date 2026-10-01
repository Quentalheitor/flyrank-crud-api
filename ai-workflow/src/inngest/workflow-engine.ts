import { inngest } from "./client";
import OpenAI from "openai";
import { executionStore } from "@/lib/execution-store";
import type {
  WorkflowExecutionPayload,
  WorkflowExecutionReport,
  NodeExecutionResult,
} from "@/types/workflow";

// Gemini OpenAI-compatible client
const gemini = new OpenAI({
  apiKey: process.env.LLM_API_KEY || "dummy-key",
  baseURL: "https://generativelanguage.googleapis.com/v1beta/openai/",
});

export const executeWorkflow = (inngest.createFunction as any)(
  {
    id: "execute-ai-workflow",
    name: "Execute AI Workflow",
    triggers: [
      { event: "workflow/execute" },
    ],
  },
  async ({
    event,
    step,
  }: {
    event: { data: WorkflowExecutionPayload };
    step: any;
  }) => {
    const payload = event.data;
    const { workflowId, inputContext, nodes, edges } = payload;

    executionStore.set(workflowId, {
      workflowId,
      status: "running",
      inputContext,
      executionPath: [],
      stepResults: {},
    });

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    let currentNodeId: string | undefined = payload.startNodeId;
    if (!currentNodeId) {
      const targetNodeIds = new Set(edges.map((e) => e.target));
      const rootNode = nodes.find((n) => !targetNodeIds.has(n.id));
      currentNodeId = rootNode?.id ?? nodes[0]?.id;
    }

    const executionPath: string[] = [];
    const stepResults: Record<string, NodeExecutionResult> = {};

    while (currentNodeId) {
      const node = nodeMap.get(currentNodeId);
      if (!node) break;

      executionPath.push(currentNodeId);
      const activeNodeId: string = currentNodeId;

      const decisionResult: NodeExecutionResult = await step.run(
        `evaluate-node-${activeNodeId}`,
        async (): Promise<NodeExecutionResult> => {
          const criteria = node.data.evaluationCriteria;

          if (!process.env.LLM_API_KEY || process.env.LLM_API_KEY === "dummy-key") {
            const mockDecision: "YES" | "NO" = Math.random() > 0.5 ? "YES" : "NO";
            return {
              nodeId: activeNodeId,
              nodeTitle: node.data.title || "Decision Step",
              prompt: criteria,
              decision: mockDecision,
              reasoning: "[DEV MOCK] Simulated decision because LLM_API_KEY is not set.",
              timestamp: new Date().toISOString(),
            };
          }

          const response = await gemini.chat.completions.create({
            model: process.env.LLM_MODEL || "gemini-2.5-flash-lite",
            temperature: 0,
            messages: [
              {
                role: "system",
                content:
                  'You are an evaluation engine. You must evaluate the given context against the criteria and answer ONLY with "YES" or "NO". Do not output explanations or punctuation.',
              },
              {
                role: "user",
                content: `Context: "${inputContext}"\n\nQuestion/Criteria: "${criteria}"\n\nAnswer (YES or NO):`,
              },
            ],
            max_tokens: 5,
          });

          const rawAnswer = response.choices[0]?.message?.content?.trim().toUpperCase() || "";
          const cleanDecision: "YES" | "NO" = rawAnswer.includes("YES") ? "YES" : "NO";

          return {
            nodeId: activeNodeId,
            nodeTitle: node.data.title || "Decision Step",
            prompt: criteria,
            decision: cleanDecision,
            timestamp: new Date().toISOString(),
          };
        }
      );

      stepResults[activeNodeId] = decisionResult;

      executionStore.set(workflowId, {
        workflowId,
        status: "running",
        inputContext,
        executionPath: [...executionPath],
        stepResults: { ...stepResults },
      });

      const matchingEdge = edges.find(
        (edge) =>
          edge.source === activeNodeId &&
          (edge.data?.branch === decisionResult.decision ||
            edge.sourceHandle?.toLowerCase() === decisionResult.decision.toLowerCase())
      );

      currentNodeId = matchingEdge ? matchingEdge.target : undefined;
    }

    const report: WorkflowExecutionReport = {
      workflowId,
      status: "completed",
      executionPath,
      stepResults,
    };

    executionStore.set(workflowId, {
      workflowId,
      status: "completed",
      inputContext,
      executionPath,
      stepResults,
    });

    return report;
  }
);