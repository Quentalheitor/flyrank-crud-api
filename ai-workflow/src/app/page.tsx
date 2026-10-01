"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import ExecutionLogsSheet from "@/components/flow/execution-logs-sheet";
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
import {
  Plus,
  RotateCcw,
  Play,
  Loader2,
  Download,
  Upload,
  FileText,
} from "lucide-react";
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

  // Run modal & status state
  const [isRunDialogOpen, setIsRunDialogOpen] = useState(false);
  const [isLogsSheetOpen, setIsLogsSheetOpen] = useState(false);
  const [inputContext, setInputContext] = useState(
    "Customer message: Our entire production database is down and users cannot log in!"
  );
  const [isRunning, setIsRunning] = useState(false);
  const [currentExecution, setCurrentExecution] = useState<ExecutionState | null>(null);

  // Hidden file input reference for JSON import
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Load from localStorage
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

  // Persist to localStorage
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

  /*
    PHASE 4: ANIMATED ACTIVE EDGES
    Determines if an edge was traversed during execution.
    If yes, marks it animated: true with a prominent stroke.
  */
  const displayEdges = useMemo(() => {
    if (!currentExecution || currentExecution.executionPath.length < 2) {
      return edges;
    }

    const path = currentExecution.executionPath;
    const activeEdgePairs = new Set<string>();

    for (let i = 0; i < path.length - 1; i++) {
      activeEdgePairs.add(`${path[i]}->${path[i + 1]}`);
    }

    return edges.map((edge) => {
      const isTraversed = activeEdgePairs.has(`${edge.source}->${edge.target}`);
      if (isTraversed) {
        return {
          ...edge,
          animated: true,
          style: {
            ...edge.style,
            strokeWidth: 3.5,
            filter: "drop-shadow(0 0 6px rgba(16, 185, 129, 0.4))",
          },
        };
      }
      return edge;
    });
  }, [edges, currentExecution]);

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

  /*
    PHASE 4: JSON EXPORT
  */
  const handleExportJSON = () => {
    const dataStr = JSON.stringify({ nodes, edges }, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `ai-workflow-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  /*
    PHASE 4: JSON IMPORT
  */
  const handleImportJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (Array.isArray(parsed.nodes) && Array.isArray(parsed.edges)) {
          setNodes(parsed.nodes);
          setEdges(parsed.edges);
          setCurrentExecution(null);
          alert("Workflow imported successfully!");
        } else {
          alert("Invalid workflow file format.");
        }
      } catch (err) {
        alert("Failed to parse JSON file.");
      }
    };
    reader.readAsText(file);
    // Reset file input so the same file can be uploaded again if needed
    e.target.value = "";
  };

  // Execute workflow
  const handleExecuteWorkflow = async () => {
    if (!inputContext.trim()) return;
    setIsRunning(true);
    setIsRunDialogOpen(false);

    // Set nodes to running / clear past results
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
      const maxAttempts = 30;

      const interval = setInterval(async () => {
        pollAttempts++;

        try {
          const statusRes = await fetch(`/api/workflow/status?workflowId=${workflowId}`);
          if (!statusRes.ok) {
            if (pollAttempts >= maxAttempts) {
              clearInterval(interval);
              setIsRunning(false);
            }
            return;
          }

          const data: ExecutionState = await statusRes.json();
          setCurrentExecution(data);

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

          if (
            data.status === "completed" ||
            data.status === "failed" ||
            pollAttempts >= maxAttempts
          ) {
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
          <span className="text-xs text-muted-foreground ml-2">Phase 4: Polish</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Hidden File Input for JSON Import */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImportJSON}
            accept=".json"
            className="hidden"
          />

          <Button
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            className="gap-1.5 text-xs"
          >
            <Upload className="w-3.5 h-3.5" />
            Import JSON
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJSON}
            className="gap-1.5 text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Export JSON
          </Button>

          {currentExecution && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsLogsSheetOpen(true)}
              className="gap-1.5 text-xs"
            >
              <FileText className="w-3.5 h-3.5" />
              View Logs
            </Button>
          )}

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

      {/* Main Flow Canvas */}
      <main className="flex-1 w-full h-full relative">
        <ReactFlow
          nodes={nodes}
          edges={displayEdges}
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

          {/* Quick Execution Status Badge */}
          {currentExecution && (
            <Panel
              position="top-right"
              className="bg-card/95 border p-3 rounded-lg shadow-lg text-xs space-y-2 max-w-xs cursor-pointer hover:border-primary transition-colors"
              onClick={() => setIsLogsSheetOpen(true)}
            >
              <div className="font-semibold flex items-center justify-between">
                <span>Execution Status</span>
                <span
                  className={`font-mono uppercase text-[10px] px-1.5 py-0.5 rounded ${
                    currentExecution.status === "completed"
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                      : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
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
              <div className="text-[10px] text-muted-foreground underline pt-0.5">
                Click to open detailed logs →
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
            <Button onClick={handleExecuteWorkflow} className="bg-emerald-600 hover:bg-emerald-700 text-white">
              Run
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Execution Logs Drawer */}
      <ExecutionLogsSheet
        open={isLogsSheetOpen}
        onOpenChange={setIsLogsSheetOpen}
        execution={currentExecution}
      />
    </div>
  );
}