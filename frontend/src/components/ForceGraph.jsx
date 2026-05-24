import React, { useRef, useState, useCallback, useEffect, memo } from "react";
import ForceGraph2D from "react-force-graph-2d";
import {
  Building2,
  User,
  MapPin,
  AlertTriangle,
  X,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Crown,
} from "lucide-react";

const ForceGraph = ({ data }) => {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!data || !data.nodes || data.nodes.length === 0) return null;

  // Transformovať edges na links (react-force-graph-2d očakáva 'links' namiesto 'edges')
  const graphData = {
    nodes: data.nodes || [],
    links: (data.edges || []).map((edge) => ({
      source: edge.source,
      target: edge.target,
      type: edge.type || "RELATED",
    })),
  };

  // Farba uzla podľa typu
  const getNodeColor = (node) => {
    if (!node || !node.type) return "#D4AF37";
    const type = node.type.toLowerCase();
    switch (type) {
      case "company":
        if (node.nace_category) {
          switch (node.nace_category.toLowerCase()) {
            case "it": return "#22d3ee"; // Cyan
            case "stavebníctvo": return "#b45309"; // Brown
            case "poľnohospodárstvo": return "#22c55e"; // Green
            case "obchod": return "#a855f7"; // Purple
            case "financie": return "#eab308"; // Gold/Yellow
            case "preprava": return "#3b82f6"; // Blue
            default: break;
          }
        }
        return (node.risk_score || 0) > 5 ? "#ef4444" : "#94a3b8";
      case "person":
        return "#60a5fa";
      case "ubo":
        return "#fbbf24"; // Bright gold for UBO
      case "address":
        return "#34d399";
      case "debt":
        return "#f87171";
      default:
        return "#D4AF37";
    }
  };

  // Veľkosť uzla podľa typu
  const getNodeSize = (node) => {
    if (!node || !node.type) return 8;
    const type = node.type.toLowerCase();
    switch (type) {
      case "company":
        return 14;
      case "person":
        return 10;
      case "ubo":
        return 12; // UBO node size
      case "address":
        return 8;
      case "debt":
        return 12;
      default:
        return 10;
    }
  };

  // Ikona uzla
  const getNodeIcon = (node) => {
    if (!node || !node.type) return Building2;
    const type = node.type.toLowerCase();
    switch (type) {
      case "company":
        return Building2;
      case "person":
        return User;
      case "ubo":
        return Crown;
      case "address":
        return MapPin;
      case "debt":
        return AlertTriangle;
      default:
        return Building2;
    }
  };

  // Farba hrany podľa typu
  const getLinkColor = (link) => {
    if (!link) return "#b45309";
    const linkType = link.type || "RELATED";
    switch (linkType) {
      case "OWNED_BY":
        return "#d97706";
      case "UBO_OF":
      case "SKUTOČNÝ_MAJITEĽ":
        return "#b45309";
      case "MANAGED_BY":
        return "#2563eb";
      case "LOCATED_AT":
        return "#10b981";
      case "HAS_DEBT":
        return "#dc2626";
      default:
        return "#64748b";
    }
  };

  // Kliknutie na uzol
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
    setIsModalOpen(true);
  }, []);

  // ESC key handling
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape" && isModalOpen) {
        setIsModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [isModalOpen]);

  // Export do PNG
  const handleExportPNG = () => {
    if (!fgRef.current) return;
    try {
      // react-force-graph-2d poskytuje canvas cez ref
      const canvas = fgRef.current.getGraphCanvas
        ? fgRef.current.getGraphCanvas()
        : document.querySelector("canvas");
      if (canvas) {
        const url = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.download = "icoatlas-graph.png";
        link.href = url;
        link.click();
      } else {
        // Fallback: screenshot celého grafu pomocou window.print alebo canvas
        const graphContainer = document.querySelector(".force-graph-container");
        if (graphContainer) {
          // Jednoduchý fallback - otvoriť print dialog
          window.print();
        } else {
          alert(
            "Canvas sa nenašiel. Použite Print Screen (Cmd+Shift+4 / Win+Shift+S)."
          );
        }
      }
    } catch (error) {
      console.error("Export error:", error);
      alert("Export sa nepodaril. Použite Print Screen alebo Developer Tools.");
    }
  };

  // Zoom funkcie
  const handleZoomIn = () => {
    if (fgRef.current) {
      fgRef.current.zoom(1.5, 200);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      fgRef.current.zoom(0.75, 200);
    }
  };

  const handleReset = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
  };

  return (
    <>
      <div className="relative bg-white border border-slate-200 rounded-2xl overflow-hidden force-graph-container h-full">
        {/* Toolbar */}
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 transition-all shadow-sm"
            title="Priblížiť"
          >
            <ZoomIn size={18} />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 transition-all shadow-sm"
            title="Oddialiť"
          >
            <ZoomOut size={18} />
          </button>
          <button
            onClick={handleReset}
            className="p-2 bg-white border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 transition-all shadow-sm"
            title="Resetovať"
          >
            <RotateCcw size={18} />
          </button>
          <button
            onClick={handleExportPNG}
            className="p-2 bg-[#0B4EA2] border border-[#0B4EA2] rounded-lg text-white hover:bg-blue-800 transition-all shadow-sm"
            title="Exportovať do PNG"
          >
            <Download size={18} />
          </button>
        </div>

        {/* Graph */}
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node) =>
            `${node.label || node.id}\n${node.type || "unknown"}`
          }
          onNodeClick={handleNodeClick}
          onNodeHover={(node) => {
            if (node) {
              document.body.style.cursor = "pointer";
            } else {
              document.body.style.cursor = "default";
            }
          }}
          cooldownTicks={100}
          onEngineStop={() => {
            if (fgRef.current) {
              fgRef.current.zoomToFit(400);
            }
          }}
          backgroundColor="transparent"
          width={800}
          height={600}
          // --- CUSTOM RENDERING ---
          nodeCanvasObject={(node, ctx, globalScale) => {
            const size = getNodeSize(node);
            const color = getNodeColor(node);
            const label = node.label || node.id;
            const fontSize = 12 / globalScale;

            // 1. Draw Circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
            ctx.fillStyle = color;
            ctx.shadowBlur = 10 / globalScale;
            ctx.shadowColor = color;
            
            // Draw red pulsing border for restricted VAT
            if (node.type && node.type.toLowerCase() === "company" && node.vat_status === "restricted") {
              ctx.strokeStyle = "#ef4444";
              ctx.lineWidth = (3 + Math.sin(Date.now() / 200) * 1.5) / globalScale;
              ctx.stroke();
            }
            
            ctx.fill();
            ctx.shadowBlur = 0; // Reset shadow

            // Draw emoji symbols inside nodes for premium aesthetics
            let emoji = "";
            if (node.type && node.type.toLowerCase() === "company" && node.is_virtual_hq) {
              emoji = "📦";
            } else if (node.type && node.type.toLowerCase() === "person" && node.potential_nominee) {
              emoji = "🕵️";
            } else if (node.type && node.type.toLowerCase() === "ubo") {
              emoji = "👑";
            }

            if (emoji) {
              ctx.font = `${size * 1.1}px Sans-Serif`;
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "#ffffff";
              ctx.fillText(emoji, node.x, node.y);
            }

            // 2. Draw Label
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#1e293b"; // Dark slate text for white background
            ctx.fillText(label, node.x, node.y + size + fontSize);

            // 3. Draw Country Flag (Indicator)
            if (node.country) {
              const flagSize = 6 / globalScale;
              const flagX = node.x + size;
              const flagY = node.y - size;

              ctx.beginPath();
              ctx.arc(flagX, flagY, flagSize, 0, 2 * Math.PI, false);
              ctx.fillStyle =
                node.country === "SK"
                  ? "#1e40af" // Slovak Blue
                  : node.country === "CZ"
                  ? "#ef4444" // Czech Red
                  : node.country === "PL"
                  ? "#ffffff" // Polish White
                  : node.country === "HU"
                  ? "#15803d" // Hungarian Green
                  : "#334155";
              ctx.strokeStyle = "#D4AF37";
              ctx.lineWidth = 1 / globalScale;
              ctx.fill();
              ctx.stroke();

              // Small country text
              ctx.font = `bold ${4 / globalScale}px Sans-Serif`;
              ctx.fillStyle = node.country === "PL" ? "#000000" : "#ffffff";
              ctx.fillText(node.country, flagX, flagY);
            }
          }}
          linkCanvasObjectMode={() => "after"}
          linkCanvasObject={(link, ctx, globalScale) => {
            const MAX_FONT_SIZE = 4;
            const LABEL_NODE_MARGIN = getNodeSize(link.source) * 1.5;

            const start = link.source;
            const end = link.target;

            // ignore unbound links
            if (typeof start !== "object" || typeof end !== "object") return;

            // calculate label positioning
            const textPos = {
              x: start.x + (end.x - start.x) / 2,
              y: start.y + (end.y - start.y) / 2,
            };

            const relLink = { x: end.x - start.x, y: end.y - start.y };

            const maxTextLength =
              Math.sqrt(Math.pow(relLink.x, 2) + Math.pow(relLink.y, 2)) -
              LABEL_NODE_MARGIN * 2;

            let fontSize = Math.min(
              MAX_FONT_SIZE,
              maxTextLength / link.type.length
            );
            fontSize = fontSize / globalScale;

            // draw text label (with background rect)
            const label = link.type || "RELA";
            ctx.font = `${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(
              (n) => n + fontSize * 0.2
            ); // some padding

            ctx.save();
            ctx.translate(textPos.x, textPos.y);
            // ctx.rotate(Math.atan2(relLink.y, relLink.x));

            ctx.fillStyle = "rgba(255, 255, 255, 0.95)";
            ctx.fillRect(
              -bckgDimensions[0] / 2,
              -bckgDimensions[1] / 2,
              ...bckgDimensions
            );

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#475569"; // Dark slate label
            ctx.fillText(label, 0, 0);
            ctx.restore();
          }}
          linkColor={(link) => getLinkColor(link)}
          linkWidth={2}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.25}
        />
      </div>

      {/* Modal s detailom uzla */}
      {isModalOpen && selectedNode && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-fade-in"
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="bg-white p-8 max-w-lg w-full mx-4 shadow-2xl rounded-2xl relative border border-slate-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all"
            >
              <X size={20} />
            </button>

            {/* Header */}
            <div className="flex items-start gap-5 mb-6">
              <div
                className="p-4 rounded-2xl"
                style={{
                  backgroundColor: `${getNodeColor(selectedNode)}15`,
                  border: `1px solid ${getNodeColor(selectedNode)}30`,
                }}
              >
                {React.createElement(getNodeIcon(selectedNode), {
                  size: 32,
                  className: "text-slate-800",
                  style: {
                    filter: `drop-shadow(0 0 8px ${getNodeColor(
                      selectedNode
                    )})`,
                  },
                })}
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
                  {selectedNode.label}
                </h3>
                <div className="flex gap-2 items-center">
                  <span className="px-2 py-1 rounded bg-[#0B4EA2]/10 border border-[#0B4EA2]/25 text-[#0B4EA2] text-xs font-bold uppercase">
                    {selectedNode.type}
                  </span>
                  {selectedNode.country && (
                    <span className="px-2 py-1 rounded bg-slate-100 border border-slate-200 text-slate-700 text-xs font-bold">
                      {selectedNode.country}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-3">
              {selectedNode.details && (
                <div>
                  <p className="text-sm text-slate-500 mb-1">Detaily:</p>
                  <p className="text-slate-800">{selectedNode.details}</p>
                </div>
              )}

              {selectedNode.ico && (
                <div>
                  <p className="text-sm text-slate-500 mb-1">IČO:</p>
                  <p className="text-slate-800 font-mono">{selectedNode.ico}</p>
                </div>
              )}

              {selectedNode.risk_score !== undefined &&
                selectedNode.risk_score > 0 && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">
                      Rizikové skóre:
                    </p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-100 rounded-full h-2">
                        <div
                           className="h-2 rounded-full transition-all"
                          style={{
                            width: `${(selectedNode.risk_score / 10) * 100}%`,
                            backgroundColor:
                              selectedNode.risk_score > 5
                                ? "#dc2626"
                                : "#d97706",
                          }}
                        />
                      </div>
                      <span className="text-sm font-bold text-red-600">
                        {selectedNode.risk_score}/10
                      </span>
                    </div>
                  </div>
                )}

              {selectedNode.virtual_seat && (
                <div className="flex items-center gap-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                  <AlertTriangle size={16} className="text-amber-600" />
                  <span className="text-sm text-amber-800 font-medium">
                    Virtuálne sídlo
                  </span>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="mt-8 pt-5 border-t border-slate-100">
              <p className="text-[10px] text-slate-400 text-center uppercase font-bold tracking-widest">
                iCOAtlas Intelligence Modal • ESC to Close
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Memoize component pre performance
export default memo(ForceGraph, (prevProps, nextProps) => {
  // Custom comparison - re-render len ak sa zmenili dáta
  return (
    prevProps.data === nextProps.data &&
    prevProps.width === nextProps.width &&
    prevProps.height === nextProps.height
  );
});
