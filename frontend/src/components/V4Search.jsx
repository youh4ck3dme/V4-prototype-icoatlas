import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ForceGraph2D from 'react-force-graph-2d';
import { Search, User, MapPin, Building2, Share2, Info, ChevronRight, AlertCircle, Loader2 } from 'lucide-react';
import { ENDPOINTS } from '../config/api';

const V4Search = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('info'); // info | graph
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const graphRef = useRef();

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${ENDPOINTS.SEARCH.V4}/${encodeURIComponent(query)}`, {
        params: { graph: 1 }
      });
      
      setResult(response.data);
      
      // Transform graph data for react-force-graph
      if (response.data.graph && response.data.graph.nodes) {
        const nodes = response.data.graph.nodes.map(n => ({
          id: n.id,
          label: n.label,
          type: n.type,
          country: n.country,
          color: getNodeColor(n.type),
          val: getNodeSize(n.type)
        }));
        
        const links = response.data.graph.edges.map(e => ({
          source: e.from_id,
          target: e.to_id,
          type: e.type,
          label: e.type
        }));
        
        setGraphData({ nodes, links });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Chyba pri hľadaní. Skontrolujte formát IČO.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (type) => {
    switch (type) {
      case 'COMPANY': return '#3B82F6'; // Blue-500
      case 'PERSON': return '#10B981';  // Emerald-500
      case 'ADDRESS': return '#F59E0B'; // Amber-500
      default: return '#94A3B8';       // Slate-400
    }
  };

  const getNodeSize = (type) => {
    switch (type) {
      case 'COMPANY': return 10;
      case 'PERSON': return 6;
      case 'ADDRESS': return 4;
      default: return 5;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 space-y-6">
      {/* Search Header */}
      <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100 overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-50 rounded-full -mr-32 -mt-32 opacity-50 blur-3xl"></div>
        
        <h1 className="text-3xl font-bold text-slate-900 mb-2 relative z-10">V4 Identifier Intelligence</h1>
        <p className="text-slate-500 mb-8 relative z-10">Automaticky rozpoznáva SK, CZ, PL a HU identifikátory s grafom vzťahov.</p>
        
        <form onSubmit={handleSearch} className="flex gap-2 relative z-10">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Zadajte IČO, NIP, KRS, DIČ..."
              className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-emerald-500 text-lg transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-emerald-200"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Analyzovať'}
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-100 p-4 rounded-xl flex items-center gap-3 text-red-700 shadow-sm animate-in fade-in slide-in-from-top-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Content Column */}
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
              <div className="flex border-b">
                <button
                  onClick={() => setActiveTab('info')}
                  className={`flex-1 py-4 font-bold text-sm uppercase tracking-wider transition-all border-b-2 ${activeTab === 'info' ? 'border-emerald-500 text-emerald-600 bg-emerald-50/30' : 'border-transparent text-slate-400 hover:bg-slate-50'}`}
                >
                  Detail firmy
                </button>
                <button
                  onClick={() => setActiveTab('graph')}
                  className={`flex-1 py-4 font-bold text-sm uppercase tracking-wider transition-all border-b-2 ${activeTab === 'graph' ? 'border-emerald-500 text-emerald-600 bg-emerald-50/30' : 'border-transparent text-slate-400 hover:bg-slate-50'}`}
                >
                  Graf vzťahov
                </button>
              </div>

              <div className="p-6">
                {activeTab === 'info' ? (
                  <div className="space-y-8 animate-in fade-in zoom-in-95 duration-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <h2 className="text-2xl font-bold text-slate-900">{result.company.legal_name}</h2>
                        <div className="flex items-center gap-2 mt-2 text-slate-500">
                          <MapPin className="w-4 h-4" />
                          <span>{result.company.street}, {result.company.city}</span>
                        </div>
                      </div>
                      <div className="bg-emerald-100 text-emerald-700 px-4 py-1.5 rounded-full text-sm font-bold shadow-sm">
                        {result.company.status}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="block text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">ID Typ</span>
                        <span className="text-slate-700 font-medium">{result.classification.id_type}</span>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="block text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">Krajina</span>
                        <span className="text-slate-700 font-medium">{result.company.country}</span>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="block text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">IČO / ID</span>
                        <span className="text-slate-700 font-mediumHighlight">{result.company.atlas_id}</span>
                      </div>
                      <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="block text-xs font-bold text-slate-400 uppercase tracking-tighter mb-1">Source</span>
                        <span className="text-slate-700 font-medium">{result.company.source_api}</span>
                      </div>
                    </div>

                    {/* Executives & Owners (SK specialized) */}
                    {(result.company.executives?.length > 0 || result.company.owners?.length > 0) && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Executives */}
                        <div className="space-y-4">
                          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                            <User className="w-5 h-5 text-emerald-500" />
                            Štatutárny orgán
                          </h3>
                          <div className="space-y-3">
                            {result.company.executives.map((p, i) => (
                              <div key={i} className="p-3 border border-slate-100 rounded-lg hover:border-emerald-200 transition-all bg-white shadow-sm">
                                <div className="font-bold text-slate-800">{p.name}</div>
                                <div className="text-sm text-slate-500 italic">{p.role}</div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Owners */}
                        <div className="space-y-4">
                          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                            <Share2 className="w-5 h-5 text-emerald-500" />
                            Vlastníci / Spoločníci
                          </h3>
                          <div className="space-y-3">
                            {result.company.owners.map((p, i) => (
                              <div key={i} className="p-3 border border-slate-100 rounded-lg hover:border-emerald-200 transition-all bg-white shadow-sm">
                                <div className="font-bold text-slate-800">{p.name}</div>
                                {p.share && <div className="text-sm text-emerald-600 font-medium">Podiel: {p.share}</div>}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-[500px] relative animate-in fade-in slide-in-from-bottom-4 duration-300">
                    <ForceGraph2D
                      ref={graphRef}
                      graphData={graphData}
                      nodeLabel="label"
                      nodeColor={n => n.color}
                      nodeVal={n => n.val}
                      linkColor={() => '#E2E8F0'}
                      linkDirectionalParticles={1}
                      linkDirectionalParticleSpeed={0.01}
                      width={700}
                      height={500}
                    />
                    
                    {/* Graph Legend Overlay */}
                    <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur p-3 rounded-lg border shadow-sm text-xs space-y-2">
                       <div className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                         <span className="font-bold">Firma</span>
                       </div>
                       <div className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                         <span className="font-bold">Osoba</span>
                       </div>
                       <div className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                         <span className="font-bold">Adresa</span>
                       </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar / Sidebar Info */}
          <div className="lg:col-span-4 space-y-6">
             <div className="bg-white border border-slate-200 text-slate-800 rounded-2xl shadow-sm p-6 overflow-hidden relative">
               <div className="absolute top-0 left-0 w-32 h-32 bg-emerald-50 rounded-full blur-3xl -ml-16 -mt-16"></div>
               
               <h3 className="text-xl font-bold mb-4 flex items-center gap-2 relative z-10 text-slate-900">
                 <Info className="w-6 h-6 text-emerald-600" />
                 Graph Intelligence
               </h3>
               
               <div className="space-y-4 relative z-10">
                 <div className="flex items-center justify-between text-sm border-b border-slate-100 pb-2">
                   <span className="text-slate-500">Celkom uzlov</span>
                   <span className="font-mono text-emerald-700 font-bold">{result.graph?.summary?.node_count || 0}</span>
                 </div>
                 <div className="flex items-center justify-between text-sm border-b border-slate-100 pb-2">
                   <span className="text-slate-500">Detegované vzťahy</span>
                   <span className="font-mono text-emerald-700 font-bold">{result.graph?.summary?.edge_count || 0}</span>
                 </div>
                 
                 <div className="mt-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
                   <p className="text-xs text-slate-600 leading-relaxed">
                     Systém automaticky prepája firmy cez spoločných majiteľov a adresy vo všetkých V4 krajinách. 
                     Hrany typu <strong>SAME_PERSON_AS</strong> sú generované na základe algoritmu zhody osôb.
                   </p>
                 </div>
               </div>
             </div>

             {result.company.orsr_vypis_url && (
               <a 
                 href={result.company.orsr_vypis_url} 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="flex items-center justify-between p-4 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition-all shadow-sm group"
               >
                 <div className="flex items-center gap-3">
                   <Building2 className="w-6 h-6 text-slate-400" />
                   <div className="text-left">
                     <div className="text-sm font-bold text-slate-800">Oficiálny výpis (ORSR)</div>
                     <div className="text-xs text-slate-500">Otvoriť v novom okne</div>
                   </div>
                 </div>
                 <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-emerald-500 transition-all" />
               </a>
             )}
          </div>
        </div>
      )}

      {/* Hero / Welcome if no results */}
      {!result && !loading && (
        <div className="text-center py-20 px-4 bg-slate-50 rounded-3xl border border-dashed border-slate-200">
          <Share2 className="w-16 h-16 text-slate-200 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-800 mb-2">Pripravený na hlbokú analýzu</h2>
          <p className="text-slate-500 max-w-md mx-auto">
            Zadajte IČO slovenskej, českej, poľskej alebo maďarskej firmy pre získanie 360° pohľadu na vzťahy.
          </p>
          <div className="mt-8 flex justify-center gap-4 text-xs font-bold text-slate-400 uppercase tracking-widest">
            <span className="px-3 py-1 bg-white border rounded">SK RÚZ/ORSR</span>
            <span className="px-3 py-1 bg-white border rounded">CZ ARES</span>
            <span className="px-3 py-1 bg-white border rounded">PL REGON/KRS</span>
            <span className="px-3 py-1 bg-white border rounded">HU NAV</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default V4Search;
