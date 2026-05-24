import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Lock,
  Menu,
  X,
  Globe,
  FileCheck,
  ChevronRight,
  Building2,
  Users,
  AlertTriangle,
  Loader2,
  Download,
  FileText,
  Moon,
  Sun,
  Star,
  Heart,
  Filter,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Share,
} from "lucide-react";
import IluminatiLogo from "../components/IluminatiLogo";
import ForceGraph from "../components/ForceGraph";
import IntelligenceBrief from "../components/IntelligenceBrief";
import Disclaimer from "../components/Disclaimer";
import LoadingSkeleton from "../components/LoadingSkeleton";
import PremiumLoader from "../components/PremiumLoader";
import axios from "axios";
import {
  exportToCSV,
  exportToPDF,
  exportToJSON,
  exportToExcel,
} from "../utils/export";
import { useTheme } from "../hooks/useTheme";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useOffline } from "../hooks/useOffline";
import RateLimitIndicator from "../components/RateLimitIndicator";
import { useAuth } from "../contexts/AuthContext";
import SEOHead from "../components/SEOHead";
import { API_URL, ENDPOINTS } from "../config/api";

/**
 * ILUMINATI SYSTEM v5.0 - SLOVAK ENTERPRISE EDITION
 * Theme: Corporate / Government / Official
 * Colors: White, Slovak Blue (#0B4EA2), Slovak Red (#EE1C25)
 */

export default function HomePageNew() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated, user, token } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const searchInputRef = useRef(null);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState({
    country: "",
    minRiskScore: "",
    maxRiskScore: "",
  });

  // Load Google Fonts
  useEffect(() => {
    const link = document.createElement("link");
    link.href =
      "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap";
    link.rel = "stylesheet";
    document.head.appendChild(link);
  }, []);

  // Autocomplete fetcher
  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timer = setTimeout(async () => {
      setSuggestionLoading(true);
      try {
        const res = await fetch(`${ENDPOINTS.SEARCH.AUTOCOMPLETE}?q=${encodeURIComponent(query)}`);
        if (res.ok) {
          const fetchedSuggestions = await res.json();
          setSuggestions(fetchedSuggestions);
          setShowSuggestions(fetchedSuggestions.length > 0);
        }
      } catch (err) {
        console.error("Autocomplete error:", err);
      } finally {
        setSuggestionLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    "Ctrl+K": (e) => {
      e.preventDefault();
      searchInputRef.current?.focus();
    },
    "/": (e) => {
      // Len ak nie je focus v inpute
      if (
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    },
    Escape: () => {
      if (showResults) {
        setShowResults(false);
        setData(null);
        setQuery("");
        window.scrollTo(0, 0);
      }
      if (menuOpen) {
        setMenuOpen(false);
      }
    },
    "Ctrl+Shift+T": (e) => {
      e.preventDefault();
      toggleTheme();
    },
    "Ctrl+E": (e) => {
      if (data && showResults) {
        e.preventDefault();
        exportToCSV(data);
      }
    },
  });

  const handleSearch = useCallback(
    async (e) => {
      e.preventDefault();
      if (!query.trim()) return;

      setLoading(true);
      setError(null);
      setData(null);
      setShowResults(false);

      try {
        // V4 Logic: Use unified search endpoint with graph=1
        const countryParam = filters.country || "";
        const searchUrl = `${ENDPOINTS.SEARCH.V4}/${encodeURIComponent(query)}?country=${countryParam}&graph=1`;

        // Fetch and 3s delay in parallel for premium feel
        const [response] = await Promise.all([
          fetch(searchUrl),
          new Promise((resolve) => setTimeout(resolve, 2000)),
        ]);

        if (!response.ok) {
           if (response.status === 404) {
             throw new Error("Subjekt s týmto identifikátorom sa nenašiel.");
           }
           throw new Error(`Chyba pri vyhľadávaní: ${response.status}`);
        }

        const searchData = await response.json();
        console.log("V4 Backend Response:", searchData);
        
        const companyData = searchData.company;
        const graphData = searchData.graph;

        let result;
        if (graphData && graphData.nodes) {
          result = {
            nodes: graphData.nodes.map(n => {
              const lowerType = (n.type || "").toLowerCase();
              const isMainCompany = lowerType === "company" && (n.data?.atlas_id === companyData.atlas_id || n.id === companyData.atlas_id);
              if (isMainCompany) {
                return {
                  ...n,
                  ...companyData,
                  type: "company",
                  label: companyData.legal_name || companyData.name || n.label,
                  risk_score: companyData.risk_score || 0,
                  risk_factors: companyData.risk_factors || [],
                };
              }
              return { 
                ...n, 
                type: lowerType,
                risk_score: 0, 
                risk_factors: [] 
              };
            }),
            edges: graphData.links || [],
            nexus_story: `Intelligence report for ${companyData.legal_name || companyData.name} (${companyData.atlas_id}). The entity is currently ${companyData.status} in the ${companyData.country} business registry. No high-risk relationship patterns detected in the initial scan.`,
            nexus_metadata: {
              node_count: graphData.nodes.length,
              edge_count: (graphData.links || []).length,
              involved_countries: [companyData.country],
              is_cross_border: false
            }
          };
        } else {
          result = {
            nodes: [
              {
                id: `company_${companyData.atlas_id}`,
                label: companyData.legal_name || companyData.name,
                type: "company",
                ico: companyData.atlas_id,
                country: companyData.country,
                status: companyData.status,
                street: companyData.street || companyData.address,
                risk_score: companyData.risk_score || 0,
                risk_factors: companyData.risk_factors || [],
                legal_form: companyData.legal_form || "N/A",
                founded: companyData.raw_data?.registration_date || "N/A",
                capital: companyData.capital || "N/A",
                city: companyData.city || companyData.address?.split(",").pop().trim() || "N/A",
                raw_data: companyData.raw_data,
                executives: companyData.executives || [],
                owners: companyData.owners || [],
                activities: companyData.activities || [],
              }
            ],
            edges: [],
            nexus_story: `Intelligence report for ${companyData.legal_name || companyData.name} (${companyData.atlas_id}). The entity is currently ${companyData.status} in the ${companyData.country} business registry. No high-risk relationship patterns detected in the initial scan.`,
            nexus_metadata: {
              node_count: 1,
              edge_count: 0,
              involved_countries: [companyData.country],
              is_cross_border: false
            }
          };
        }

        console.log("Transformed Graph Data:", result);
        setData(result);
        setShowResults(true);
        // Scroll to results
        setTimeout(() => {
          document
            .getElementById("results-section")
            ?.scrollIntoView({ behavior: "smooth" });
        }, 100);
      } catch (err) {
        setError(err.message || "Nastala chyba pri vyhľadávaní.");
      } finally {
        setLoading(false);
      }
    },
    [query, filters]
  );

  // Helper: Get risk score from node
  const getRiskScore = (nodes) => {
    const companyNodes = nodes.filter((n) => n.type === "company");
    if (companyNodes.length === 0) return 0;
    return Math.max(...companyNodes.map((n) => n.risk_score || 0));
  };

  // Helper: Get risk status
  const getRiskStatus = (score) => {
    if (score >= 7) return { text: "KRITICKÉ RIZIKO", color: "red" };
    if (score >= 5) return { text: "VYSOKÉ RIZIKO", color: "red" };
    if (score >= 3) return { text: "STREDNÉ RIZIKO", color: "orange" };
    return { text: "NÍZKE RIZIKO", color: "blue" };
  };

  // Helper: Get main company node
  const getMainCompany = () => {
    if (!data) return null;
    return data.nodes.find((n) => n.type === "company") || data.nodes[0];
  };

  const mainCompany = getMainCompany();
  const riskScore = data ? getRiskScore(data.nodes) : 0;
  const riskStatus = getRiskStatus(riskScore);

  // Check if company is favorite
  useEffect(() => {
    if (data && isAuthenticated && mainCompany && token) {
      const checkFavorite = async () => {
        try {
          const companyId =
            mainCompany.ico || mainCompany.id?.split("_")[1] || query;
          const country = mainCompany.country || "SK";
          const response = await fetch(
            `${API_URL}/api/user/favorites/check/${companyId}/${country}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );
          if (response.ok) {
            const result = await response.json();
            setIsFavorite(result.is_favorite);
          }
        } catch (error) {
          console.error("Error checking favorite:", error);
        }
      };
      checkFavorite();
    } else {
      setIsFavorite(false);
    }
  }, [data, isAuthenticated, mainCompany, query, token]);

  return (
    <div className="min-h-screen bg-[#020617] font-sans text-slate-100 overflow-x-hidden relative">
      <div className="aether-bg"></div>
      <SEOHead
        title={
          showResults && data
            ? `Analýza: ${query} | ILUMINATI SYSTEM`
            : "ILUMINATI SYSTEM - Transparentnosť pre slovenské podnikanie"
        }
        description={
          showResults && data
            ? `Komplexná analýza obchodných vzťahov pre ${query}. Risk score: ${riskScore}/10.`
            : "Komplexná hĺbková analýza obchodných partnerov, vlastníckych štruktúr a finančného zdravia firiem v regióne strednej Európy (SK, CZ, PL, HU)."
        }
      />
      {loading && !showResults && <PremiumLoader />}
      <style>{`
        .font-heading { font-family: 'Playfair Display', serif; }
        .font-sans { font-family: 'Inter', sans-serif; }
        .slovak-blue-bg { background-color: #0B4EA2; }
        .slovak-blue-text { color: #0B4EA2; }
        .slovak-red-bg { background-color: #EE1C25; }
        .slovak-red-text { color: #EE1C25; }
        .shadow-corp { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
      `}</style>

      {/* --- NAVBAR --- */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-effect border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div
            className="flex items-center gap-3 group cursor-pointer"
            onClick={() => {
              setShowResults(false);
              setData(null);
              window.scrollTo(0, 0);
            }}
          >
            <div className="bg-gradient-to-br from-blue-500 to-blue-700 p-2 rounded-lg shadow-lg group-hover:shadow-blue-500/20 transition-all">
              <IluminatiLogo size={28} />
            </div>
            <span className="text-xl font-bold tracking-tight text-white font-heading">
              ILUMINATI <span className="text-blue-400 font-light">SYSTEM</span>
            </span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            <NavBtn
              label="Monitoring"
              active={!showResults}
              onClick={() => {
                setShowResults(false);
                setData(null);
                window.scrollTo(0, 0);
              }}
            />
            <NavBtn
              label="Legislatíva & Compliance"
              onClick={() => navigate("/vop")}
            />
            <button
              onClick={toggleTheme}
              className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              title={
                theme === "dark"
                  ? "Prepnúť na svetlý režim"
                  : "Prepnúť na tmavý režim"
              }
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            {isAuthenticated ? (
              <button
                className="px-6 py-2.5 slovak-blue-bg text-white hover:bg-blue-800 transition-colors font-medium text-sm rounded-md shadow-sm flex items-center gap-2"
                onClick={() => navigate("/dashboard")}
              >
                <Lock size={14} />
                Dashboard
              </button>
            ) : (
              <button
                className="px-6 py-2.5 slovak-blue-bg text-white hover:bg-blue-800 transition-colors font-medium text-sm rounded-md shadow-sm flex items-center gap-2"
                onClick={() => navigate("/login")}
              >
                <Lock size={14} />
                Prihlásiť sa
              </button>
            )}
          </div>

          <button
            className="md:hidden text-slate-700"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {menuOpen && (
        <div className="fixed top-20 left-0 right-0 bg-white border-b border-slate-200 shadow-lg z-40 md:hidden">
          <div className="px-6 py-4 space-y-3">
            <button
              className="w-full text-left px-4 py-2 rounded hover:bg-slate-50"
              onClick={() => {
                setShowResults(false);
                setMenuOpen(false);
              }}
            >
              Monitoring
            </button>
            <button
              className="w-full text-left px-4 py-2 rounded hover:bg-slate-50"
              onClick={() => {
                navigate("/vop");
                setMenuOpen(false);
              }}
            >
              Legislatíva
            </button>
            <button
              className="w-full text-left px-4 py-2 rounded hover:bg-slate-50 slovak-blue-text font-medium"
              onClick={() => {
                navigate("/vop");
                setMenuOpen(false);
              }}
            >
              Klientska zóna
            </button>
          </div>
        </div>
      )}

      {/* --- MAIN CONTENT --- */}
      <main className="pt-20 min-h-screen relative z-10">
        {!showResults ? (
          <div className="w-full">
            {/* Hero Section */}
            <div className="relative pt-32 pb-20 md:pt-40 md:pb-32 px-6">
              <div className="max-w-4xl mx-auto text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold uppercase tracking-wider mb-6 animate-pulse-slow">
                  <Sparkles size={12} />
                  <span>Next-Gen Corporate Intelligence</span>
                </div>

                <h1 className="text-5xl md:text-7xl font-bold text-white mb-8 leading-[1.1] font-heading tracking-tight">
                  Nexus{" "}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-200">
                    Visual Intelligence
                  </span>
                </h1>

                <p className="text-lg md:text-xl text-slate-300 mb-12 max-w-2xl mx-auto leading-relaxed">
                  Analyze cross-border relationships, detect high-risk patterns,
                  and reveal hidden ownership structures in the V4 region.
                </p>

                <div className="glass-card p-2 md:p-3 max-w-3xl mx-auto shadow-2xl shadow-blue-500/10">
                  <form
                    onSubmit={handleSearch}
                    className="flex flex-col md:flex-row gap-2"
                  >
                    <div className="md:w-32">
                        <select
                          className="w-full h-full bg-white/5 border border-white/10 rounded-xl py-4 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none cursor-pointer font-bold text-center"
                          value={filters.country}
                          onChange={(e) => setFilters({...filters, country: e.target.value})}
                        >
                          <option value="CZ">🇨🇿 CZ</option>
                          <option value="SK">🇸🇰 SK</option>
                          <option value="PL">🇵🇱 PL</option>
                          <option value="HU">🇭🇺 HU</option>
                        </select>
                      </div>
                    <div className="flex-grow relative group">
                      <Search
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-400 transition-colors"
                        size={20}
                      />
                      <input
                        type="text"
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all font-medium text-lg"
                        placeholder="Insert IČO, ID or Company Name..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                        onFocus={() => { if(suggestions.length > 0) setShowSuggestions(true); }}
                        ref={searchInputRef}
                      />
                      {suggestionLoading && (
                        <div className="absolute right-4 top-1/2 -translate-y-1/2">
                          <Loader2 className="animate-spin text-slate-400" size={16} />
                        </div>
                      )}
                      {showSuggestions && suggestions.length > 0 && (
                        <div className="absolute z-50 w-full mt-2 bg-[#0f172a] border border-white/10 rounded-xl shadow-2xl max-h-80 overflow-y-auto text-left">
                          {suggestions.map((sug, idx) => (
                            <div 
                              key={idx} 
                              className="px-4 py-3 hover:bg-white/5 cursor-pointer border-b border-white/5 last:border-0"
                              onClick={() => {
                                setQuery(sug.id);
                                setShowSuggestions(false);
                              }}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-bold text-white">{sug.name}</span>
                                <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{sug.id}</span>
                              </div>
                              <div className="text-sm text-slate-400 mt-1">{sug.address}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-lg shadow-blue-600/20 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2 min-w-[160px]"
                    >
                      {loading ? (
                        <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      ) : (
                        <>Analyze</>
                      )}
                    </button>
                  </form>
                </div>

                {isAuthenticated && (
                  <div className="mt-6">
                    <RateLimitIndicator />
                  </div>
                )}

                {/* Advanced Filters Trigger */}
                <div className="mt-8 flex flex-col items-center">
                  <button
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    <Filter size={16} />
                    <span>Advanced Search Filters</span>
                    {showAdvancedFilters ? (
                      <ChevronUp size={16} />
                    ) : (
                      <ChevronDown size={16} />
                    )}
                  </button>

                  {showAdvancedFilters && (
                    <div className="mt-6 w-full max-w-3xl glass-card p-6 animate-fade-in text-left">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                            Country
                          </label>
                          <select
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all"
                            value={filters.country}
                            onChange={(e) =>
                              setFilters({
                                ...filters,
                                country: e.target.value,
                              })
                            }
                          >
                            <option value="">All Countries</option>
                            <option value="SK">Slovakia (SK)</option>
                            <option value="CZ">Czech Rep. (CZ)</option>
                            <option value="PL">Poland (PL)</option>
                            <option value="HU">Hungary (HU)</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                            Min Risk
                          </label>
                          <input
                            type="number"
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                            value={filters.minRiskScore}
                            onChange={(e) =>
                              setFilters({
                                ...filters,
                                minRiskScore: e.target.value,
                              })
                            }
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                            Max Risk
                          </label>
                          <input
                            type="number"
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                            value={filters.maxRiskScore}
                            onChange={(e) =>
                              setFilters({
                                ...filters,
                                maxRiskScore: e.target.value,
                              })
                            }
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Features Section */}
            <div className="max-w-7xl mx-auto px-6 py-20">
              <div className="grid md:grid-cols-3 gap-8">
                <FeatureCard
                  icon={<Globe className="text-blue-400" />}
                  title="Cross-Border Nexus"
                  desc="Trace ownership across Slovak, Czech, Polish and Hungarian registries instantly."
                />
                <FeatureCard
                  icon={<ShieldAlert className="text-rose-400" />}
                  title="Risk Intelligence"
                  desc="Detect tax debtors, liquidity issues, and high-risk executive patterns."
                />
                <FeatureCard
                  icon={<FileCheck className="text-emerald-400" />}
                  title="Aether Analysis"
                  desc="Pixel-perfect relationship visualization with intelligent story generation."
                />
              </div>
            </div>
          </div>
        ) : (
          /* VIEW 2: RESULTS DASHBOARD */
          <div
            id="results-section"
            className="w-full max-w-7xl mx-auto px-6 pb-20 animate-fade-in"
          >
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-8 pt-6">
              <span
                className="cursor-pointer hover:text-blue-400 transition-colors"
                onClick={() => setShowResults(false)}
              >
                Home
              </span>
              <ChevronRight size={14} />
              <span className="text-white font-medium">
                Entity Intelligence
              </span>
            </div>

            <div className="grid lg:grid-cols-12 gap-8">
              {/* Information Panel */}
              <div className="lg:col-span-4 flex flex-col gap-6">
                {/* Entity Stats Card */}
                <div
                  className="glass-card p-8 border-t-4"
                  style={{
                    borderTopColor:
                      riskStatus.color === "red"
                        ? "#ef4444"
                        : riskStatus.color === "orange"
                        ? "#f59e0b"
                        : "#3b82f6",
                  }}
                >
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-2 ${
                          riskStatus.color === "red"
                            ? "bg-red-500/20 text-red-400"
                            : riskStatus.color === "orange"
                            ? "bg-orange-500/20 text-orange-400"
                            : "bg-blue-500/20 text-blue-400"
                        }`}
                      >
                        {riskStatus.text} Risk
                      </span>
                      <h2 className="text-2xl font-bold text-white tracking-tight">
                        {mainCompany?.label || "Unknown Entity"}
                      </h2>
                      {mainCompany?.ico && (
                        <p className="text-sm text-slate-400 mt-1">
                          ICO: {mainCompany.ico}
                        </p>
                      )}
                    </div>
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center border-2 font-bold text-lg ${
                        riskStatus.color === "red"
                          ? "border-red-500/40 text-red-500 bg-red-500/10"
                          : riskStatus.color === "orange"
                          ? "border-orange-500/40 text-orange-500 bg-orange-500/10"
                          : "border-blue-500/40 text-blue-500 bg-blue-500/10"
                      }`}
                    >
                      {riskScore}
                    </div>
                  </div>

                  <div className="space-y-4 py-6 border-y border-white/5 text-sm">
                    <DataRow
                      label="Country"
                      value={mainCompany?.country || "N/A"}
                    />
                    <DataRow
                      label="Legal Form"
                      value={mainCompany?.legal_form || "N/A"}
                    />
                    <DataRow
                      label="Founded"
                      value={mainCompany?.founded || "N/A"}
                    />
                    <DataRow
                      label="Capital"
                      value={mainCompany?.capital || "N/A"}
                    />
                    <DataRow label="DIC" value={mainCompany?.dic || "N/A"} />
                    <DataRow
                      label="Street"
                      value={mainCompany?.street || "N/A"}
                    />
                    <DataRow label="City" value={mainCompany?.city || "N/A"} />
                    {mainCompany?.city_part && (
                      <DataRow
                        label="City Part"
                        value={mainCompany.city_part}
                      />
                    )}
                    {mainCompany?.raw_data?.region && (
                      <DataRow
                        label="Region"
                        value={mainCompany.raw_data.region}
                      />
                    )}
                    {mainCompany?.raw_data?.district && (
                      <DataRow
                        label="District"
                        value={mainCompany.raw_data.district}
                      />
                    )}
                  </div>

                  {mainCompany?.risk_factors?.length > 0 && (
                    <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                      <h4 className="text-xs font-bold text-red-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <ShieldAlert size={14} /> Critical Risk Factors
                      </h4>
                      <ul className="space-y-2">
                        {mainCompany.risk_factors.map((factor, idx) => (
                          <li
                            key={idx}
                            className="text-xs text-slate-300 flex items-start gap-2"
                          >
                            <span className="w-1 h-1 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Debts Section */}
                  {mainCompany?.raw_data?.debts && mainCompany.raw_data.debts.length > 0 && (
                    <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                      <h4 className="text-xs font-bold text-red-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <AlertTriangle size={14} /> Záväzky voči štátu
                      </h4>
                      <div className="space-y-3">
                        {mainCompany.raw_data.debts.map((debt, idx) => (
                          <div key={idx} className="flex justify-between items-center text-sm border-b border-red-500/10 pb-2 last:border-0 last:pb-0">
                            <div className="flex flex-col">
                              <span className="text-slate-200 font-medium">{debt.institution}</span>
                              <span className="text-slate-400 text-xs">Evidované k: {debt.published_on}</span>
                            </div>
                            <span className="text-red-400 font-bold text-lg">{Number(debt.amount).toFixed(2)} €</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Štatutárny orgán (Executives) */}
                  {mainCompany?.executives && mainCompany.executives.length > 0 && (
                    <div className="mt-6 p-5 rounded-xl bg-blue-500/5 border border-blue-500/10 shadow-lg">
                      <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Users size={16} /> Štatutárny orgán
                      </h4>
                      <div className="space-y-4">
                        {mainCompany.executives.map((exec, idx) => (
                          <div key={idx} className="border-b border-white/5 pb-3 last:border-0 last:pb-0">
                            <div className="flex justify-between items-start">
                              <span className="font-semibold text-white text-sm">{exec.name}</span>
                              {exec.role && (
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                  {exec.role}
                                </span>
                              )}
                            </div>
                            {exec.address && (
                              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                                {exec.address}
                              </p>
                            )}
                            {exec.since && (
                              <p className="text-[10px] text-slate-500 mt-1 font-mono">
                                Vznik funkcie: {exec.since}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Spoločníci / Vlastníci (Owners) */}
                  {mainCompany?.owners && mainCompany.owners.length > 0 && (
                    <div className="mt-6 p-5 rounded-xl bg-indigo-500/5 border border-indigo-500/10 shadow-lg">
                      <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Building2 size={16} /> Spoločníci a vlastné imanie
                      </h4>
                      <div className="space-y-4">
                        {mainCompany.owners.map((owner, idx) => (
                          <div key={idx} className="border-b border-white/5 pb-3 last:border-0 last:pb-0">
                            <div className="flex flex-col gap-1">
                              <span className="font-semibold text-white text-sm">{owner.name}</span>
                              {owner.share && (
                                <span className="text-xs font-semibold text-emerald-400">
                                  {owner.share}
                                </span>
                              )}
                            </div>
                            {owner.address && (
                              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                                {owner.address}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Predmety podnikania (Activities) */}
                  {mainCompany?.activities && mainCompany.activities.length > 0 && (
                    <div className="mt-6 p-5 rounded-xl bg-slate-800/20 border border-white/5 shadow-lg">
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Activity size={16} /> Predmety podnikania
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {mainCompany.activities.map((act, idx) => (
                          <span 
                            key={idx} 
                            className="bg-white/5 hover:bg-white/10 border border-white/10 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 transition-all cursor-default leading-normal"
                          >
                            {act}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Financials Section (Phase 17) */}
                  {mainCompany?.raw_data?.financials && (
                    <div className="mt-6 p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                      <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <Activity size={14} /> Financial Data (
                        {mainCompany.raw_data.financials.year || "Latest"})
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Revenue</span>
                          <span className="text-slate-200 font-medium">
                            {mainCompany.raw_data.financials.revenue || "N/A"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Profit</span>
                          <span
                            className={`font-medium ${
                              (
                                mainCompany.raw_data.financials.profit || ""
                              ).startsWith("-")
                                ? "text-red-400"
                                : "text-emerald-400"
                            }`}
                          >
                            {mainCompany.raw_data.financials.profit || "N/A"}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {isAuthenticated && (
                    <button
                      onClick={async () => {
                        setFavoriteLoading(true);
                        try {
                          const companyId =
                            mainCompany.ico ||
                            mainCompany.id?.split("_")[1] ||
                            query;
                          const country = mainCompany.country || "SK";
                          if (isFavorite) {
                            const favoritesResponse = await fetch(
                              `${API_URL}/api/user/favorites`,
                              { headers: { Authorization: `Bearer ${token}` } }
                            );
                            if (favoritesResponse.ok) {
                              const { favorites } =
                                await favoritesResponse.json();
                              const fav = favorites.find(
                                (f) =>
                                  f.company_identifier === companyId &&
                                  f.country === country
                              );
                              if (fav) {
                                await fetch(
                                  `${API_URL}/api/user/favorites/${fav.id}`,
                                  {
                                    method: "DELETE",
                                    headers: {
                                      Authorization: `Bearer ${token}`,
                                    },
                                  }
                                );
                                setIsFavorite(false);
                              }
                            }
                          } else {
                            await fetch(`${API_URL}/api/user/favorites`, {
                              method: "POST",
                              headers: {
                                Authorization: `Bearer ${token}`,
                                "Content-Type": "application/json",
                              },
                              body: JSON.stringify({
                                company_identifier: companyId,
                                company_name: mainCompany.label || "Unknown",
                                country: country,
                                company_data: mainCompany,
                                risk_score: riskScore,
                                risk_factors: mainCompany.risk_factors || [],
                              }),
                            });
                            setIsFavorite(true);
                          }
                        } catch (e) {
                          console.error(e);
                        } finally {
                          setFavoriteLoading(false);
                        }
                      }}
                      disabled={favoriteLoading}
                      className={`mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-bold transition-all ${
                        isFavorite
                          ? "bg-yellow-500/10 text-yellow-500 border border-yellow-500/30"
                          : "bg-white/5 text-white border border-white/10 hover:bg-white/10"
                      }`}
                    >
                      {favoriteLoading ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : isFavorite ? (
                        <>
                          <Star size={18} className="fill-yellow-500" /> Saved
                          to Nexus
                        </>
                      ) : (
                        <>
                          <Star size={18} /> Add to Nexus
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Summary Card */}
                {mainCompany?.details && (
                  <div className="glass-card p-6 bg-blue-500/5 border-blue-500/10">
                    <h4 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3">
                      Aether Summary
                    </h4>
                    <p className="text-sm text-slate-300 leading-relaxed">
                      {mainCompany.details}
                    </p>
                  </div>
                )}
              </div>

              {/* Graph Panel */}
              <div className="lg:col-span-8 flex flex-col gap-6">
                <div className="glass-card flex-grow overflow-hidden relative flex flex-col">
                  <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-2 font-bold text-white uppercase tracking-wider text-xs">
                      <Share size={16} className="text-blue-400" />{" "}
                      Relationship Visualization
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => exportToCSV(data)}
                        className="text-[10px] uppercase font-bold bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg text-slate-400 hover:text-white transition-all"
                      >
                        CSV
                      </button>
                      <button
                        onClick={() => {
                          /* PNG logic handled in watermarking block below */
                        }}
                        className="text-[10px] uppercase font-bold bg-blue-600 border border-blue-500 px-3 py-1.5 rounded-lg text-white hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/20"
                      >
                        Export PNG
                      </button>
                    </div>
                  </div>
                  <div className="flex-grow bg-black/20 p-4 relative flex flex-col md:flex-row gap-4">
                    <div className="flex-grow relative">
                      <ForceGraph data={data} />
                    </div>
                    {data?.nexus_story && (
                      <div className="md:w-80 flex-shrink-0">
                        <IntelligenceBrief
                          story={data.nexus_story}
                          metadata={data.nexus_metadata}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* --- FOOTER --- */}
      <footer className="bg-slate-900 text-slate-400 py-12 text-sm border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 text-white font-bold mb-4 font-heading">
              <IluminatiLogo size={24} /> ILUMINATI
            </div>
            <p className="mb-4">
              Profesionálny nástroj pre overovanie obchodných partnerov.
            </p>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Produkt</h4>
            <ul className="space-y-2">
              <li className="hover:text-white cursor-pointer">Funkcie</li>
              <li className="hover:text-white cursor-pointer">
                API Integrácia
              </li>
              <li className="hover:text-white cursor-pointer">Cenník</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Spoločnosť</h4>
            <ul className="space-y-2">
              <li className="hover:text-white cursor-pointer">O nás</li>
              <li className="hover:text-white cursor-pointer">Kariéra</li>
              <li className="hover:text-white cursor-pointer">Kontakt</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-4">Legislatíva</h4>
            <ul className="space-y-2">
              <li
                className="hover:text-white cursor-pointer"
                onClick={() => navigate("/vop")}
              >
                VOP
              </li>
              <li
                className="hover:text-white cursor-pointer"
                onClick={() => navigate("/privacy")}
              >
                Ochrana údajov
              </li>
              <li
                className="hover:text-white cursor-pointer"
                onClick={() => navigate("/disclaimer")}
              >
                Disclaimer
              </li>
              <li
                className="hover:text-white cursor-pointer"
                onClick={() => navigate("/cookies")}
              >
                Cookies
              </li>
            </ul>
          </div>
        </div>

        {/* Disclaimer s zdrojmi dát */}
        <div className="border-t border-slate-700 mt-8 pt-6">
          <div className="bg-slate-800/50 rounded-lg p-4 border-l-4 border-amber-500">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <svg
                  className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div className="flex-1">
                  <p className="text-amber-400 font-semibold text-sm mb-2">
                    Dôležité upozornenie
                  </p>
                  <p className="text-slate-300 text-xs leading-relaxed">
                    Dáta majú len informatívny charakter. Poskytovateľ
                    negarantuje správnosť dát. Pre oficiálne informácie použite
                    pôvodné zdroje.
                  </p>
                </div>
              </div>
              <div className="pl-8">
                <p className="text-amber-400 font-semibold text-xs mb-2">
                  Zdroj dát:
                </p>
                <ul className="space-y-1 text-xs text-slate-400">
                  <li>
                    <a
                      href="https://www.orsr.sk"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-amber-400 transition-colors"
                    >
                      Obchodný register SR (ORSR)
                    </a>
                  </li>
                  <li>
                    <a
                      href="https://www.zrsr.sk"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-amber-400 transition-colors"
                    >
                      Živnostenský register SR (ZRSR)
                    </a>
                  </li>
                  <li>
                    <a
                      href="https://www.registeruz.sk"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-amber-400 transition-colors"
                    >
                      Register účtovných závierok (RUZ)
                    </a>
                  </li>
                  <li>
                    <a
                      href="https://wwwinfo.mfcr.cz"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-amber-400 transition-colors"
                    >
                      ARES (ČR)
                    </a>
                  </li>
                  <li>
                    <a
                      href="https://www.financnasprava.sk"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-amber-400 transition-colors"
                    >
                      Finančná správa SR
                    </a>
                  </li>
                </ul>
              </div>
              <div className="mt-3 pl-8">
                <button
                  onClick={() => navigate("/disclaimer")}
                  className="text-amber-400 hover:text-amber-300 text-xs font-semibold underline"
                >
                  Viac informácií o vylúčení zodpovednosti
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// --- SUBCOMPONENTS ---

function NavBtn({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`text-sm font-medium transition-colors ${
        active ? "slovak-blue-text" : "text-slate-600 hover:text-slate-900"
      }`}
    >
      {label}
    </button>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-corp border border-slate-100 hover:border-blue-200 transition-colors">
      <div className="mb-4 bg-slate-50 w-12 h-12 rounded flex items-center justify-center">
        {React.cloneElement(icon, { size: 24 })}
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-2 font-heading">
        {title}
      </h3>
      <p className="text-slate-600 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}

function DataRow({ label, value, valueClass = "text-white font-medium text-right" }) {
  return (
    <div className="flex justify-between items-start py-2 border-b border-white/5 last:border-0 gap-4">
      <span className="text-slate-400 text-xs uppercase tracking-wider whitespace-nowrap pt-0.5">{label}</span>
      <span className={valueClass}>{value}</span>
    </div>
  );
}
