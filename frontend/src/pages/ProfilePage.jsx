import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  FaKey,
  FaTrash,
  FaCopy,
  FaCreditCard,
  FaCrown,
  FaCheck,
} from "react-icons/fa";

const ProfilePage = () => {
  const { user, token } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState(null);
  const [loadingKeys, setLoadingKeys] = useState(false);

  // Initialize API URL from env
  const API_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  useEffect(() => {
    if (user && user.tier === "enterprise") {
      fetchApiKeys();
    }
  }, [user]);

  const fetchApiKeys = async () => {
    setLoadingKeys(true);
    try {
      const response = await fetch(`${API_URL}/api/api-keys?token=${token}`);
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data);
      }
    } catch (error) {
      console.error("Failed to fetch API keys", error);
    } finally {
      setLoadingKeys(false);
    }
  };

  const createApiKey = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/api/api-keys?token=${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newKeyName }),
      });

      if (response.ok) {
        const data = await response.json();
        setCreatedKey(data);
        setNewKeyName("");
        fetchApiKeys(); // Refresh list
      }
    } catch (error) {
      console.error("Failed to create key", error);
    }
  };

  const revokeApiKey = async (id) => {
    if (!confirm("Naozaj chcete zrušiť tento API kľúč?")) return;
    try {
      const response = await fetch(
        `${API_URL}/api/api-keys/${id}?token=${token}`,
        {
          method: "DELETE",
        }
      );
      if (response.ok) {
        fetchApiKeys();
      }
    } catch (error) {
      console.error("Failed to revoke key", error);
    }
  };

  const handleUpgrade = async (tier) => {
    try {
      const response = await fetch(
        `${API_URL}/api/payment/checkout?tier=${tier}`,
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

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50 pt-24 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Môj Profil</h1>
        <p className="text-slate-500 mb-8">Správa účtu a predplatného</p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* User Info Card */}
          <div className="bg-white border border-slate-200 shadow-sm rounded-xl p-6 h-fit">
            <div className="flex items-center gap-4 mb-6">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold text-white
                              ${
                                user.tier === "enterprise"
                                  ? "bg-gradient-to-r from-purple-600 to-pink-600"
                                  : "bg-slate-600"
                              }`}
              >
                {user.full_name ? user.full_name[0] : user.email[0]}
              </div>
              <div>
                <h3 className="font-bold text-lg text-slate-900">
                  {user.full_name || "Používateľ"}
                </h3>
                <p className="text-sm text-slate-500">{user.email}</p>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-slate-500">Aktuálny plán:</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-bold uppercase
                                  ${
                                    user.tier === "enterprise"
                                      ? "bg-purple-50 text-purple-700 border border-purple-200"
                                      : user.tier === "pro"
                                      ? "bg-blue-50 text-blue-700 border border-blue-200"
                                      : "bg-slate-100 text-slate-700 border border-slate-200"
                                  }`}
                >
                  {user.tier === "free" ? "Zadarmo" : user.tier === "pro" ? "PRO" : user.tier === "enterprise" ? "Enterprise" : user.tier}
                </span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500">Členom od:</span>
                <span className="text-slate-800 font-medium">
                  {new Date(user.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Subscription Management */}
          <div className="bg-white border border-slate-200 shadow-sm rounded-xl p-6 lg:col-span-2">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <FaCreditCard className="text-[#0B4EA2]" /> Predplatné
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* PRO Plan */}
              <div
                className={`border rounded-lg p-4 transition-all ${
                  user.tier === "pro"
                    ? "border-[#0B4EA2] bg-blue-50/50"
                    : "border-slate-200 hover:border-slate-350"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-bold text-slate-900">PRO</h3>
                  {user.tier === "pro" && <FaCheck className="text-[#0B4EA2]" />}
                </div>
                <p className="text-2xl font-bold text-slate-900 mb-4">
                  19.99€{" "}
                  <span className="text-sm font-normal text-slate-500">/mes</span>
                </p>
                <ul className="text-sm text-slate-650 space-y-2 mb-6">
                  <li>✓ Vyššie limity vyhľadávania</li>
                  <li>✓ Detailné exporty</li>
                  <li>✓ Prioritná podpora</li>
                </ul>
                {user.tier !== "pro" && user.tier !== "enterprise" && (
                  <button
                    onClick={() => handleUpgrade("pro")}
                    className="w-full py-2 bg-[#0B4EA2] hover:bg-blue-800 text-white rounded font-medium transition-colors"
                  >
                    Upgrade na PRO
                  </button>
                )}
              </div>

              {/* ENTERPRISE Plan */}
              <div
                className={`border rounded-lg p-4 transition-all ${
                  user.tier === "enterprise"
                    ? "border-purple-500 bg-purple-50/30"
                    : "border-slate-200 hover:border-slate-350"
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    ENTERPRISE <FaCrown className="text-yellow-500 text-sm" />
                  </h3>
                  {user.tier === "enterprise" && (
                    <FaCheck className="text-purple-650" />
                  )}
                </div>
                <p className="text-2xl font-bold text-slate-900 mb-4">
                  99.99€{" "}
                  <span className="text-sm font-normal text-slate-500">/mes</span>
                </p>
                <ul className="text-sm text-slate-650 space-y-2 mb-6">
                  <li>✓ Neobmedzené vyhľadávanie</li>
                  <li>✓ API Prístup</li>
                  <li>✓ Nexus Intelligence</li>
                </ul>
                {user.tier !== "enterprise" && (
                  <button
                    onClick={() => handleUpgrade("enterprise")}
                    className="w-full py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white rounded font-medium transition-colors"
                  >
                    Upgrade na ENTERPRISE
                  </button>
                )}
              </div>
            </div>

            {/* Payment Instructions */}
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-slate-700">
                <strong className="text-[#0B4EA2]">ℹ️ Po úhrade:</strong>{" "}
                Kontaktujte nás na{" "}
                <a
                  href="mailto:support@icoatlas.sk"
                  className="text-[#0B4EA2] hover:underline font-semibold"
                >
                  support@icoatlas.sk
                </a>{" "}
                s potvrdením platby pre aktiváciu vášho predplatného.
              </p>
            </div>
          </div>

          {/* API Keys Section - Only for Enterprise */}
          {user.tier === "enterprise" && (
            <div className="bg-white border border-slate-200 shadow-sm rounded-xl p-6 lg:col-span-3">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
                <FaKey className="text-yellow-600" /> API Kľúče
              </h2>

              {/* Key Creation */}
              <form onSubmit={createApiKey} className="flex gap-4 mb-6">
                <input
                  type="text"
                  placeholder="Názov kľúča (napr. Produkcia)"
                  className="flex-1 bg-slate-50 border border-slate-350 rounded p-2 text-slate-900 outline-none focus:ring-2 focus:ring-[#0B4EA2] focus:border-transparent"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                />
                <button
                  type="submit"
                  className="bg-[#0B4EA2] hover:bg-blue-800 px-4 py-2 rounded text-white font-medium transition-colors"
                >
                  Vygenerovať
                </button>
              </form>

              {/* New Key Display Modal/Alert */}
              {createdKey && (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-250 rounded-lg">
                  <h4 className="text-yellow-800 font-bold mb-2">
                    Nový API kľúč vygenerovaný
                  </h4>
                  <p className="text-sm text-slate-650 mb-2">
                    Toto je jediný raz, čo vidíte tento kľúč. Bezpečne si ho
                    uložte.
                  </p>
                  <div className="flex items-center gap-2 bg-slate-100 border border-slate-200 p-2 rounded">
                    <code className="text-slate-800 flex-1 font-mono break-all">
                      {createdKey.key}
                    </code>
                    <button
                      className="text-slate-500 hover:text-slate-800 p-1"
                      onClick={() =>
                        navigator.clipboard.writeText(createdKey.key)
                      }
                      title="Kopírovať"
                    >
                      <FaCopy />
                    </button>
                  </div>
                </div>
              )}

              {/* Keys List */}
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="text-slate-500 text-sm border-b border-slate-200">
                      <th className="p-3">Názov</th>
                      <th className="p-3">Prefix</th>
                      <th className="p-3">Vytvorený</th>
                      <th className="p-3">Stav</th>
                      <th className="p-3 text-right">Akcie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiKeys.map((key) => (
                      <tr
                        key={key.id}
                        className="border-b border-slate-100 text-slate-700 hover:bg-slate-50"
                      >
                        <td className="p-3 font-medium">{key.name}</td>
                        <td className="p-3">
                          <span className="font-mono text-xs bg-slate-100 rounded px-2 py-1 border border-slate-200 text-slate-800">
                            {key.prefix}••••
                          </span>
                        </td>
                        <td className="p-3 text-sm">
                          {new Date(key.created_at).toLocaleDateString()}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              key.is_active
                                ? "bg-green-50 text-green-700 border border-green-200"
                                : "bg-red-50 text-red-700 border border-red-200"
                            }`}
                          >
                            {key.is_active ? "Aktívny" : "Zrušený"}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          {key.is_active && (
                            <button
                              onClick={() => revokeApiKey(key.id)}
                              className="text-[#EE1C25] hover:text-red-700 p-2 transition-colors"
                              title="Zrušiť kľúč"
                            >
                              <FaTrash />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {apiKeys.length === 0 && (
                      <tr>
                        <td
                          colSpan="5"
                          className="p-6 text-center text-slate-400 italic"
                        >
                          Žiadne aktívne API kľúče
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
