import React from "react";
import { Sparkles, Globe, Share, Info } from "lucide-react";

const IntelligenceBrief = ({ story, metadata }) => {
  if (!story) return null;

  return (
    <div
      className="bg-white border border-slate-200 flex flex-col h-full rounded-2xl border-l-4 shadow-sm"
      style={{
        borderLeftColor: metadata?.is_cross_border ? "#0B4EA2" : "#94a3b8",
      }}
    >
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-slate-800 uppercase tracking-wider text-[11px]">
          <Sparkles className="w-4 h-4 text-[#0B4EA2]" />
          <span>Intelligence Brief</span>
        </div>
        {metadata?.is_cross_border && (
          <span className="flex items-center gap-1 text-[9px] bg-blue-50 text-[#0B4EA2] px-2 py-0.5 rounded-full font-bold uppercase tracking-widest border border-blue-200">
            <Globe className="w-3 h-3" />
            Cross-Border
          </span>
        )}
      </div>

      <div className="p-5 flex-grow overflow-y-auto">
        <p className="text-sm text-slate-700 leading-relaxed font-medium mb-6">
          {story}
        </p>

        {metadata && (
          <div className="grid grid-cols-2 gap-4 pt-5 border-t border-slate-100">
            <div className="flex flex-col gap-1">
              <span className="text-[9px] text-slate-500 uppercase font-bold tracking-widest">
                Network Nodes
              </span>
              <span className="text-sm font-bold text-slate-800">
                {metadata.node_count}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[9px] text-slate-500 uppercase font-bold tracking-widest">
                Relationships
              </span>
              <span className="text-sm font-bold text-slate-800">
                {metadata.edge_count}
              </span>
            </div>
            <div className="flex flex-col col-span-2 gap-2 mt-2">
              <span className="text-[9px] text-slate-500 uppercase font-bold tracking-widest">
                Involved Jurisdictions
              </span>
              <div className="flex flex-wrap gap-2 mt-1">
                {metadata.involved_countries?.map((c) => (
                  <span
                    key={c}
                    className="text-[10px] bg-blue-50 text-[#0B4EA2] px-2 py-1 rounded border border-blue-100 font-bold"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-slate-50 px-5 py-3 flex items-center gap-2 text-[10px] text-slate-500 font-bold border-t border-slate-100 uppercase tracking-widest">
        <Share className="w-3.5 h-3.5 text-[#0B4EA2]" />
        <span>iCOAtlas Analytics Engine v5.0</span>
      </div>
    </div>
  );
};

export default IntelligenceBrief;
