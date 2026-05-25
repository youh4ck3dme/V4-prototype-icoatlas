import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import IcoAtlasLogo from "../components/IcoAtlasLogo";
import { exportBatchToExcel } from "../utils/export";
import { Download } from "lucide-react";
import { ENDPOINTS } from "../config/api";

const Dashboard = () => {
  const { user, token: authContextToken, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchHistory, setSearchHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [tierLimits, setTierLimits] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const token = authContextToken || localStorage.getItem("token");

      // Načítať tier limits
      const limitsResponse = await fetch(
        ENDPOINTS.AUTH.LIMITS,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (limitsResponse.ok) {
        const limits = await limitsResponse.json();
        setTierLimits(limits);
      }

      // Načítať search history
      const historyResponse = await fetch(
        ENDPOINTS.USER.HISTORY,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (historyResponse.ok) {
        const history = await historyResponse.json();
        setSearchHistory(history.slice(0, 10)); // Posledných 10
      }

      // Načítať favorites
      const favoritesResponse = await fetch(
        ENDPOINTS.USER.FAVORITES,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (favoritesResponse.ok) {
        const favoritesData = await favoritesResponse.json();
        setFavorites(favoritesData.favorites || []);
      }
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (tier) => {
    try {
      const token = authContextToken || localStorage.getItem("token");
      const response = await fetch(
        `${ENDPOINTS.API_URL}/api/payment/checkout?tier=${tier}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.url) {
          window.location.href = data.url; // Redirect to SumUp Payment
        }
      }
    } catch (error) {
      console.error("Error creating checkout:", error);
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case "free":
        return "bg-gray-500";
      case "pro":
        return "bg-blue-500";
      case "enterprise":
        return "bg-purple-500";
      default:
        return "bg-gray-500";
    }
  };

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0B4EA2]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-[100dvh] bg-slate-50 pt-20">
      <nav className="bg-white border-b border-slate-200 shadow-sm fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
              <IcoAtlasLogo size={32} />
              <span className="text-xl font-bold tracking-tight text-slate-800">
                iCO<span className="text-[#0B4EA2] font-semibold">Atlas</span>
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-slate-700 font-medium">{user?.email}</span>
              <button
                onClick={logout}
                className="bg-[#EE1C25] hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors font-medium text-sm"
              >
                Odhlásiť sa
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* User Profile Card */}
        <div className="bg-white border border-slate-200 shadow-sm rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">
                {user?.full_name || "Používateľ"}
              </h2>
              <p className="text-slate-555">{user?.email}</p>
            </div>
            <div className="text-right">
              <div
                className={`inline-block px-4 py-2 rounded-lg text-white font-semibold uppercase ${getTierColor(
                  user?.tier
                )}`}
              >
                {user?.tier === "free" ? "Zadarmo" : user?.tier === "pro" ? "PRO" : user?.tier === "enterprise" ? "Enterprise" : "Zadarmo"}
              </div>
              {user?.tier === "free" && (
                <button
                  onClick={() => handleUpgrade("pro")}
                  className="mt-2 block w-full bg-[#0B4EA2] hover:bg-blue-800 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  Upgrade na PRO
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Usage Statistics */}
          <div className="bg-white border border-slate-200 shadow-sm rounded-xl p-6">
            <h3 className="text-xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">
              Štatistiky používania
            </h3>
            {tierLimits ? (
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-slate-700 mb-2">
                    <span>Počet vyhľadávaní na deň</span>
                    <span className="font-semibold text-slate-900">
                      {tierLimits.searches_per_day === -1
                        ? "Neobmedzene"
                        : tierLimits.searches_per_day}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-slate-700 mb-2">
                    <span>Max uzlov v grafe</span>
                    <span className="font-semibold text-slate-900">
                      {tierLimits.max_graph_nodes === -1
                        ? "Neobmedzene"
                        : tierLimits.max_graph_nodes}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-slate-700 mb-2">
                    <span>PDF Export</span>
                    <span className="font-semibold text-slate-900">
                      {tierLimits.can_export_pdf ? "✅ Povolené" : "❌ Nepovolené"}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-slate-500">Načítavam limity...</p>
            )}
          </div>

          {/* Search History */}
          <div className="bg-white border border-slate-200 shadow-sm rounded-xl p-6">
            <h3 className="text-xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">
              Nedávne vyhľadávania
            </h3>
            {searchHistory.length > 0 ? (
              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                {searchHistory.map((search, index) => (
                  <div
                    key={index}
                    className="bg-slate-50 hover:bg-slate-100 border border-slate-200/60 rounded-lg p-3 text-slate-800 transition-colors cursor-pointer"
                    onClick={() => navigate(`/?q=${search.query}`)}
                  >
                    <div className="font-semibold">{search.query}</div>
                    <div className="text-xs text-slate-500">
                      {new Date(search.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 italic">Žiadna história vyhľadávania</p>
            )}
          </div>
        </div>

        {/* Favorite Companies */}
        <div className="mt-6 bg-white border border-slate-200 shadow-sm rounded-xl p-6">
          <h3 className="text-xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">
            Obľúbené firmy
          </h3>
          {favorites.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {favorites.map((favorite) => (
                <div
                  key={favorite.id}
                  className="bg-slate-50 border border-slate-200/80 rounded-lg p-4 text-slate-800 hover:bg-slate-100 hover:border-slate-300 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="font-semibold text-base text-slate-900 line-clamp-1">
                        {favorite.company_name}
                      </div>
                      <div className="text-sm text-slate-500">
                        IČO: {favorite.company_identifier} • {favorite.country}
                      </div>
                    </div>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        if (!confirm("Naozaj odobrať z obľúbených?")) return;
                        try {
                          const token = authContextToken || localStorage.getItem("token");
                          const response = await fetch(
                            `${ENDPOINTS.USER.FAVORITES}/${favorite.id}`,
                            {
                              method: "DELETE",
                              headers: {
                                Authorization: `Bearer ${token}`,
                              },
                            }
                          );
                          if (response.ok) {
                            setFavorites(
                              favorites.filter((f) => f.id !== favorite.id)
                            );
                          }
                        } catch (error) {
                          console.error("Error removing favorite:", error);
                        }
                      }}
                      className="text-red-500 hover:text-red-700 ml-2 text-lg font-bold"
                      title="Odobrať z obľúbených"
                    >
                      ✕
                    </button>
                  </div>
                  {favorite.risk_score !== null && (
                    <div className="mt-3 space-y-2">
                      <div
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold text-white shadow-sm ${
                          favorite.risk_score >= 8
                            ? "bg-gradient-to-r from-red-600 to-rose-500"
                            : favorite.risk_score >= 5
                            ? "bg-gradient-to-r from-amber-500 to-orange-400"
                            : "bg-gradient-to-r from-emerald-500 to-teal-400"
                        }`}
                      >
                        Rizikový index: {favorite.risk_score.toFixed(1)}
                      </div>

                      {favorite.risk_factors &&
                        favorite.risk_factors.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {favorite.risk_factors
                              .slice(0, 3)
                              .map((factor, i) => (
                                <span
                                  key={i}
                                  className="text-[10px] bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-650"
                                >
                                  • {factor}
                                </span>
                              ))}
                          </div>
                        )}
                    </div>
                  )}
                  {favorite.notes && (
                    <div className="mt-2 text-sm text-slate-600 italic">
                      "{favorite.notes}"
                    </div>
                  )}
                  <button
                    onClick={() =>
                      navigate(`/?q=${favorite.company_identifier}`)
                    }
                    className="mt-3 w-full bg-[#0B4EA2] hover:bg-blue-800 text-white px-4 py-2 rounded-lg transition-colors text-sm font-semibold"
                  >
                    Zobraziť detail
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 italic">
              Žiadne obľúbené firmy. Pridajte si firmy do obľúbených priamo z výsledkov vyhľadávania.
            </p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-6 bg-white border border-slate-200 shadow-sm rounded-xl p-6">
          <h3 className="text-xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">Rýchle akcie</h3>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => navigate("/")}
              className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Nové vyhľadávanie
            </button>
            {user?.tier === "enterprise" && (
              <>
                <button
                  onClick={() => navigate("/api-keys")}
                  className="bg-purple-700 hover:bg-purple-800 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  API kľúče
                </button>
                 <button
                  onClick={() => navigate("/webhooks")}
                  className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Webhooky
                </button>
                <button
                  onClick={() => navigate("/erp-integrations")}
                  className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  ERP Integrácie
                </button>
                <button
                  onClick={() => navigate("/analytics")}
                  className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Analytika
                </button>
              </>
            )}
            {user?.tier === "free" && (
              <button
                onClick={() => handleUpgrade("pro")}
                className="bg-[#EE1C25] hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors shadow-sm"
              >
                Upgrade na PRO
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
