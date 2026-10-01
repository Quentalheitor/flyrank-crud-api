import { NextResponse } from "next/server";
import { executionStore } from "@/lib/execution-store";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const workflowId = searchParams.get("workflowId");

  if (!workflowId) {
    return NextResponse.json({ error: "Missing workflowId parameter" }, { status: 400 });
  }

  const run = executionStore.get(workflowId);
  if (!run) {
    return NextResponse.json({ status: "pending" }, { status: 200 });
  }

  return NextResponse.json(run);
}