import { NextResponse } from "next/server";
import { inngest } from "@/inngest/client";
import { executionStore } from "@/lib/execution-store";
import type { WorkflowExecutionPayload } from "@/types/workflow";

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as WorkflowExecutionPayload;

    if (!body.nodes || body.nodes.length === 0) {
      return NextResponse.json({ error: "Graph has no nodes" }, { status: 400 });
    }

    // Pre-populate store so the first poll has data immediately
    executionStore.set(body.workflowId, {
      workflowId: body.workflowId,
      status: "running",
      inputContext: body.inputContext,
      executionPath: [],
      stepResults: {},
    });

    const { ids } = await inngest.send({
      name: "workflow/execute",
      data: body,
    });

    return NextResponse.json({
      success: true,
      eventId: ids[0],
      message: "Workflow triggered successfully",
    });
  } catch (error: any) {
    console.error("Workflow trigger error:", error);

    const isConnRefused =
      error?.code === "ECONNREFUSED" ||
      error?.message?.includes("fetch failed") ||
      error?.cause?.code === "ECONNREFUSED";

    const message = isConnRefused
      ? "Inngest Dev Server is not running. Please run `npx inngest-cli@latest dev` in a separate terminal."
      : error?.message || "Failed to trigger workflow execution";

    return NextResponse.json({ error: message }, { status: 500 });
  }
}