"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type NodeTypes,
  type EdgeTypes,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import DecisionNode, { type DecisionNodeType } from "@/components/flow/decision-node";
import DecisionEdge, { type DecisionEdgeType } from "@/components/flow/decision-edge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, RotateCcw, Play, Loader2 } from "lucide-react";
import type { ExecutionState } from "@/lib/execution-store";

const STORAGE_KEY = "ai-workflow-graph-v1";

const nodeTypes: NodeTypes = {
  decisionNode: DecisionNode,
};

const edgeTypes: EdgeTypes = {
  decisionEdge: DecisionEdge,
};

const BASE_CANVAS = {
  minX: -200,
  minY: -200,
  maxX: 1400,
  maxY: 1000,
  padding: 300,
};

const initialNodes: DecisionNodeType[] = [
  {
    id: "node-1",
    type: "decisionNode",
    position: { x: 380, y: 80 },
    data: {
      title: "Inquiry Classifier",
      evaluationCriteria: "Is this request asking for technical support?",
    },
  },
  {
    id: "node-2",
    type: "decisionNode",
    position: { x: 100, y: 380 },
    data: {
      title: "Urgency Check",
      evaluationCriteria: "Is this a critical system outage?",
    },
  },
  {
    id: "node-3",
    type: "decisionNode",
    position: { x: 660, y: 380 },
    data: {
      title: "Sales Triage",
      evaluationCriteria: "Is this an enterprise lead with > 50 seats?",
    },
  },
];

const initialEdges: DecisionEdgeType[] = [
  {
    id: "edge-1-2",
    source: "node-1",
    sourceHandle: "yes",
    target: "node-2",
    type: "decisionEdge",
    data: { branch: "YES" },
  },
  {
    id: "edge-1-3",
    source: "node-1",
    sourceHandle: "no",
    target: "node-3",
    type: "decisionEdge",
    data: { branch: "NO" },
  },
];

export default function WorkflowPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<DecisionNodeType>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<DecisionEdgeType>(initialEdges);
  const [isLoaded, setIsLoaded] = useState(false);

  // Run modal state
  const [isRunDialogOpen, setIsRunDialogOpen] = useState(false);
  const [inputContext, setInputContext] = useState(
    "Customer message: Our entire production database is down and users cannot log in!"
  );
  const [isRunning, setIsRunning] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<ExecutionState | null>(null);

  // Load graph from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const { nodes: savedNodes, edges: savedEdges } = JSON.parse(saved);
        if (Array.isArray(savedNodes) && Array.isArray(savedEdges)) {
          setNodes(savedNodes);
          setEdges(savedEdges);
        }
      } catch (err) {
        console.error("Failed to parse saved graph:", err);
      }
    }
    setIsLoaded(true);
  }, [setNodes, setEdges]);

  // Persist graph to localStorage
  useEffect(() => {
    if (!isLoaded) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ nodes, edges }));
  }, [nodes, edges, isLoaded]);

  // Dynamic canvas boundary
  const dynamicTranslateExtent = useMemo<[[number, number], [number, number]]>(() => {
    let minX = BASE_CANVAS.minX;
    let minY = BASE_CANVAS.minY;
    let maxX = BASE_CANVAS.maxX;
    let maxY = BASE_CANVAS.maxY;

    nodes.forEach((node) => {
      const nodeRight = node.position.x + 320;
      const nodeBottom = node.position.y + 260;
      if (node.position.x < minX) minX = node.position.x - BASE_CANVAS.padding;
      if (node.position.y < minY) minY = node.position.y - BASE_CANVAS.padding;
      if (nodeRight > maxX) maxX = nodeRight + BASE_CANVAS.padding;
      if (nodeBottom > maxY) maxY = nodeBottom + BASE_CANVAS.padding;
    });

    return [
      [minX, minY],
      [maxX, maxY],
    ];
  }, [nodes]);

  const onConnect = useCallback(
    (connection: Connection) => {
      const branch: "YES" | "NO" = connection.sourceHandle === "no" ? "NO" : "YES";
      const newEdge: DecisionEdgeType = {
        ...connection,
        id: `edge-${connection.source}-${connection.sourceHandle}-${connection.target}`,
        type: "decisionEdge",
        data: { branch },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  const handleAddNode = useCallback(() => {
    const newNodeId = `node-${Date.now()}`;
    const newNode: DecisionNodeType = {
      id: newNodeId,
      type: "decisionNode",
      position: {
        x: 350 + (Math.random() * 80 - 40),
        y: 250 + (Math.random() * 80 - 40),
      },
      data: {
        title: `Decision Step ${nodes.length + 1}`,
        evaluationCriteria: "",
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, setNodes]);

  const handleReset = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setNodes(initialNodes);
    setEdges(initialEdges);
    setCurrentExecution(null);
  }, [setNodes, setEdges]);

  // Execute workflow & poll status
  const handleExecuteWorkflow = async () => {
    if (!inputContext.trim()) return;
    setIsRunning(true);
    setIsRunDialogOpen(false);

    // Reset previous run status on canvas nodes
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, lastResult: undefined, status: "idle" },
      }))
    );

    const workflowId = `wf_${Date.now()}`;

    try {
      const res = await fetch("/api/workflow/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflowId,
          inputContext,
          nodes,
          edges,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Server responded with ${res.status}`);
      }

      let pollAttempts = 0;
      const maxAttempts = 30; // 30 * 700ms = 21 seconds maximum timeout

      const interval = setInterval(async () => {
        pollAttempts++;

        try {
          const statusRes = await fetch(`/api/workflow/status?workflowId=${workflowId}`);
          
          if (!statusRes.ok) {
            if (pollAttempts >= maxAttempts) {
              clearInterval(interval);
              setIsRunning(false);
              alert("Workflow execution timed out while checking status.");
            }
            return;
          }

          const data: ExecutionState = await statusRes.json();
          setCurrentExecution(data);

          // Update nodes with live YES / NO badges
          if (data.stepResults) {
            setNodes((nds) =>
              nds.map((n) => {
                const stepResult = data.stepResults[n.id];
                if (stepResult) {
                  return {
                    ...n,
                    data: {
                      ...n.data,
                      lastResult: stepResult.decision,
                      status: "completed",
                    },
                  };
                }
                return n;
              })
            );
          }

          // Stop polling once finished or if reached maximum attempts
          if (data.status === "completed" || data.status === "failed" || pollAttempts >= maxAttempts) {
            clearInterval(interval);
            setIsRunning(false);
          }
        } catch (pollErr) {
          console.error("Polling error:", pollErr);
          if (pollAttempts >= maxAttempts) {
            clearInterval(interval);
            setIsRunning(false);
          }
        }
      }, 700);
    } catch (err: any) {
      alert(err.message || "Failed to start workflow");
      setIsRunning(false);
    }
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-background">
      {/* Top Navbar */}
      <header className="h-14 border-b px-6 flex items-center justify-between z-10 bg-background/95 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div
            className={`h-3 w-3 rounded-full ${
              isRunning ? "bg-amber-500 animate-ping" : "bg-emerald-500"
            }`}
          />
          <h1 className="font-semibold text-sm">AI Workflow Engine</h1>
          <span className="text-xs text-muted-foreground ml-2">Phase 3: Execution</span>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5 text-xs">
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Flow
          </Button>

          <Button variant="outline" size="sm" onClick={handleAddNode} className="gap-1.5 text-xs">
            <Plus className="w-3.5 h-3.5" />
            Add Decision Node
          </Button>

          <Button
            size="sm"
            onClick={() => setIsRunDialogOpen(true)}
            disabled={isRunning}
            className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Evaluating...
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                Run Workflow
              </>
            )}
          </Button>
        </div>
      </header>

      {/* Main Canvas */}
      <main className="flex-1 w-full h-full relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          translateExtent={dynamicTranslateExtent}
          minZoom={0.4}
          maxZoom={1.5}
          fitView
          fitViewOptions={{ padding: 0.3 }}
        >
          <Background gap={16} size={1} />
          <Controls showInteractive={false} />
          <MiniMap
            zoomable={false}
            pannable={false}
            className="!bg-background border rounded-lg overflow-hidden shadow-sm"
          />

          {currentExecution && (
            <Panel
              position="top-right"
              className="bg-card/95 border p-3 rounded-lg shadow-lg text-xs space-y-2 max-w-xs"
            >
              <div className="font-semibold flex items-center justify-between">
                <span>Execution Status</span>
                <span
                  className={`font-mono uppercase text-[10px] px-1.5 py-0.5 rounded ${
                    currentExecution.status === "completed"
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {currentExecution.status}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Path taken: </span>
                <span className="font-mono text-foreground font-medium">
                  {currentExecution.executionPath.join(" → ")}
                </span>
              </div>
            </Panel>
          )}
        </ReactFlow>
      </main>

      {/* Run Input Modal */}
      <Dialog open={isRunDialogOpen} onOpenChange={setIsRunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Run AI Workflow</DialogTitle>
            <DialogDescription>
              Enter the context (email, message, ticket) that the AI nodes will evaluate.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-2 py-2">
            <Textarea
              rows={4}
              value={inputContext}
              onChange={(e) => setInputContext(e.target.value)}
              placeholder="Enter customer message or input context..."
              className="text-xs"
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRunDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleExecuteWorkflow} className="bg-emerald-600 hover:bg-emerald-700">
              Run
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}