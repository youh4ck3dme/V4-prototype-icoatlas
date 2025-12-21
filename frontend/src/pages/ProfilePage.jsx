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
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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

  const handlePaymentLink = (tier) => {
    // SumUp payment links - replace with your actual SumUp links
    const paymentLinks = {
      pro: "https://sumup.com/payment/YOUR_PRO_LINK", // Replace with actual SumUp link
      enterprise: "https://sumup.com/payment/YOUR_ENTERPRISE_LINK", // Replace with actual SumUp link
    };

    window.open(paymentLinks[tier], "_blank");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen pt-24 p-6 container mx-auto">
      <h1 className="text-3xl font-bold text-white mb-2">Môj Profil</h1>
      <p className="text-slate-400 mb-8">Správa účtu a predplatného</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* User Info Card */}
        <div className="glass-card p-6 h-fit">
          <div className="flex items-center gap-4 mb-6">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold 
                            ${
                              user.tier === "enterprise"
                                ? "bg-gradient-to-r from-purple-500 to-pink-500"
                                : "bg-slate-700"
                            }`}
            >
              {user.full_name ? user.full_name[0] : user.email[0]}
            </div>
            <div>
              <h3 className="font-bold text-lg text-white">
                {user.full_name || "Používateľ"}
              </h3>
              <p className="text-sm text-slate-400">{user.email}</p>
            </div>
          </div>

          <div className="border-t border-slate-700/50 pt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-slate-400">Aktuálny plán:</span>
              <span
                className={`px-2 py-1 rounded text-xs font-bold uppercase
                                ${
                                  user.tier === "enterprise"
                                    ? "bg-purple-500/20 text-purple-300"
                                    : user.tier === "pro"
                                    ? "bg-sky-500/20 text-sky-300"
                                    : "bg-slate-700 text-slate-300"
                                }`}
              >
                {user.tier}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Členom od:</span>
              <span className="text-white">
                {new Date(user.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        {/* Subscription Management */}
        <div className="glass-card p-6 lg:col-span-2">
          <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <FaCreditCard className="text-sky-400" /> Predplatné
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* PRO Plan */}
            <div
              className={`border rounded-lg p-4 transition-all ${
                user.tier === "pro"
                  ? "border-sky-500 bg-sky-900/10"
                  : "border-slate-700 hover:border-slate-600"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold text-white">PRO</h3>
                {user.tier === "pro" && <FaCheck className="text-sky-400" />}
              </div>
              <p className="text-2xl font-bold text-white mb-4">
                19.99€{" "}
                <span className="text-sm font-normal text-slate-400">/mes</span>
              </p>
              <ul className="text-sm text-slate-300 space-y-2 mb-6">
                <li>✓ Vyššie limity vyhľadávania</li>
                <li>✓ Detailné exporty</li>
                <li>✓ Prioritná podpora</li>
              </ul>
              {user.tier !== "pro" && user.tier !== "enterprise" && (
                <button
                  onClick={() => handlePaymentLink("pro")}
                  className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium transition-colors"
                >
                  Upgrade na PRO
                </button>
              )}
            </div>

            {/* ENTERPRISE Plan */}
            <div
              className={`border rounded-lg p-4 transition-all ${
                user.tier === "enterprise"
                  ? "border-purple-500 bg-purple-900/10"
                  : "border-slate-700 hover:border-slate-600"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  ENTERPRISE <FaCrown className="text-yellow-400 text-sm" />
                </h3>
                {user.tier === "enterprise" && (
                  <FaCheck className="text-purple-400" />
                )}
              </div>
              <p className="text-2xl font-bold text-white mb-4">
                99.99€{" "}
                <span className="text-sm font-normal text-slate-400">/mes</span>
              </p>
              <ul className="text-sm text-slate-300 space-y-2 mb-6">
                <li>✓ Neobmedzené vyhľadávanie</li>
                <li>✓ API Prístup</li>
                <li>✓ Nexus Intelligence</li>
              </ul>
              {user.tier !== "enterprise" && (
                <button
                  onClick={() => handlePaymentLink("enterprise")}
                  className="w-full py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white rounded font-medium transition-colors"
                >
                  Upgrade na ENTERPRISE
                </button>
              )}
            </div>
          </div>

          {/* Payment Instructions */}
          <div className="mt-4 p-4 bg-sky-900/20 border border-sky-700/50 rounded-lg">
            <p className="text-sm text-slate-300">
              <strong className="text-sky-400">ℹ️ Po úhrade:</strong>{" "}
              Kontaktujte nás na{" "}
              <a
                href="mailto:support@icoatlas.sk"
                className="text-sky-400 hover:underline"
              >
                support@icoatlas.sk
              </a>{" "}
              s potvrdením platby pre aktiváciu vášho predplatného.
            </p>
          </div>
        </div>

        {/* API Keys Section - Only for Enterprise */}
        {user.tier === "enterprise" && (
          <div className="glass-card p-6 lg:col-span-3">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <FaKey className="text-yellow-400" /> API Kľúče
            </h2>

            {/* Key Creation */}
            <form onSubmit={createApiKey} className="flex gap-4 mb-6">
              <input
                type="text"
                placeholder="Názov kľúča (napr. Produkcia)"
                className="flex-1 bg-slate-900/50 border border-slate-700 rounded p-2 text-white outline-none focus:border-sky-500"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                required
              />
              <button
                type="submit"
                className="bg-sky-600 hover:bg-sky-500 px-4 py-2 rounded text-white font-medium"
              >
                Vygenerovať
              </button>
            </form>

            {/* New Key Display Modal/Alert */}
            {createdKey && (
              <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
                <h4 className="text-yellow-400 font-bold mb-2">
                  Nový API kľúč vygenerovaný
                </h4>
                <p className="text-sm text-slate-300 mb-2">
                  Toto je jediný raz, čo vidíte tento kľúč. Bezpečne si ho
                  uložte.
                </p>
                <div className="flex items-center gap-2 bg-black/30 p-2 rounded">
                  <code className="text-white flex-1 font-mono">
                    {createdKey.key}
                  </code>
                  <button
                    className="text-slate-400 hover:text-white"
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
                  <tr className="text-slate-400 text-sm border-b border-slate-700">
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
                      className="border-b border-slate-700/30 text-slate-300 hover:bg-white/5"
                    >
                      <td className="p-3">{key.name}</td>
                      <td className="p-3 font-mono text-xs bg-black/20 rounded w-fit px-2 py-1">
                        {key.prefix}••••
                      </td>
                      <td className="p-3 text-sm">
                        {new Date(key.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            key.is_active
                              ? "bg-emerald-500/20 text-emerald-300"
                              : "bg-red-500/20 text-red-300"
                          }`}
                        >
                          {key.is_active ? "Aktívny" : "Zrušený"}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        {key.is_active && (
                          <button
                            onClick={() => revokeApiKey(key.id)}
                            className="text-red-400 hover:text-red-300 p-2"
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
                        className="p-6 text-center text-slate-500 italic"
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
  );
};

export default ProfilePage;
