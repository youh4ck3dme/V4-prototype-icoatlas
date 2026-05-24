import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';
import IcoAtlasLogo from '../components/IcoAtlasLogo';
import { Copy, Trash2, Plus, Key, Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react';

const ApiKeys = () => {
  const { user, token } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [copiedKeyId, setCopiedKeyId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    expires_days: '',
    permissions: ['read'],
    ip_whitelist: ''
  });

  useEffect(() => {
    if (user?.tier === 'enterprise') {
      loadApiKeys();
    }
  }, [user]);

  const loadApiKeys = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/enterprise/keys', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.keys || []);
      }
    } catch (error) {
      console.error('Error loading API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    
    try {
      const payload = {
        name: formData.name,
        permissions: formData.permissions,
      };

      if (formData.expires_days) {
        payload.expires_days = parseInt(formData.expires_days);
      }

      if (formData.ip_whitelist) {
        payload.ip_whitelist = formData.ip_whitelist.split(',').map(ip => ip.trim()).filter(ip => ip);
      }

      const response = await fetch('http://localhost:8000/api/enterprise/keys', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setNewKey(data.data);
        setShowCreateForm(false);
        setFormData({
          name: '',
          expires_days: '',
          permissions: ['read'],
          ip_whitelist: ''
        });
        loadApiKeys();
      }
    } catch (error) {
      console.error('Error creating API key:', error);
    }
  };

  const handleRevokeKey = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API key?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/enterprise/keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        loadApiKeys();
      }
    } catch (error) {
      console.error('Error revoking API key:', error);
    }
  };

  const copyToClipboard = (text, keyId) => {
    navigator.clipboard.writeText(text);
    setCopiedKeyId(keyId);
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  if (user?.tier !== 'enterprise') {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white border border-slate-200 shadow-md rounded-xl p-8 text-center animate-fade-in">
            <IcoAtlasLogo className="mx-auto mb-6" />
            <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Vyžaduje sa Enterprise úroveň</h1>
            <p className="text-slate-650 mb-6">API kľúče sú dostupné len pre predplatiteľov balíka Enterprise.</p>
            <a
              href="/dashboard"
              className="inline-block bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors shadow-sm"
            >
              Späť na Dashboard
            </a>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-50 pt-20">
        <nav className="bg-white border-b border-slate-200 shadow-sm fixed top-0 left-0 right-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
                <IcoAtlasLogo size={32} />
                <span className="text-xl font-bold tracking-tight text-slate-800">
                  iCO<span className="text-[#0B4EA2] font-semibold">Atlas</span>
                </span>
              </div>
              <a href="/dashboard" className="text-[#0B4EA2] hover:text-blue-800 font-semibold text-sm">
                Späť na Dashboard
              </a>
            </div>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2">API Kľúče</h1>
              <p className="text-slate-500">Spravujte API kľúče pre programový prístup k údajom</p>
            </div>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2 shadow-sm"
            >
              <Plus size={20} />
              Vytvoriť API kľúč
            </button>
          </div>

          {/* New Key Display */}
          {newKey && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="text-green-600" size={24} />
                  <h3 className="text-xl font-bold text-green-800">API kľúč bol úspešne vytvorený!</h3>
                </div>
                <button
                  onClick={() => setNewKey(null)}
                  className="text-slate-400 hover:text-slate-600 font-bold text-lg"
                >
                  ×
                </button>
              </div>
              <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <code className="text-slate-800 font-mono text-sm break-all">{newKey.key}</code>
                  <button
                    onClick={() => copyToClipboard(newKey.key, 'new')}
                    className="ml-4 text-[#0B4EA2] hover:text-blue-800"
                    title="Kopírovať"
                  >
                    {copiedKeyId === 'new' ? <CheckCircle size={20} /> : <Copy size={20} />}
                  </button>
                </div>
              </div>
              <p className="text-yellow-800 text-sm font-semibold">
                ⚠️ Pozor! Tento kľúč sa už znova nezobrazí. Dobre si ho uložte na bezpečné miesto.
              </p>
            </div>
          )}

          {/* Create Form */}
          {showCreateForm && (
            <div className="bg-white border border-slate-200 shadow-md rounded-xl p-6 mb-6">
              <h2 className="text-xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">Vytvoriť nový API kľúč</h2>
              <form onSubmit={handleCreateKey} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Názov kľúča</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-355 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="napr. Produkčný API kľúč"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Platnosť (v dňoch)</label>
                  <input
                    type="number"
                    value={formData.expires_days}
                    onChange={(e) => setFormData({ ...formData, expires_days: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-355 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Ponechajte prázdne pre neobmedzenú platnosť"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Oprávnenia</label>
                  <div className="space-y-2">
                    <label className="flex items-center text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.permissions.includes('read')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({ ...formData, permissions: [...formData.permissions, 'read'] });
                          } else {
                            setFormData({ ...formData, permissions: formData.permissions.filter(p => p !== 'read') });
                          }
                        }}
                        className="mr-2 rounded border-slate-300 text-[#0B4EA2] focus:ring-blue-500"
                      />
                      Čítanie (Read)
                    </label>
                    <label className="flex items-center text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.permissions.includes('write')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({ ...formData, permissions: [...formData.permissions, 'write'] });
                          } else {
                            setFormData({ ...formData, permissions: formData.permissions.filter(p => p !== 'write') });
                          }
                        }}
                        className="mr-2 rounded border-slate-300 text-[#0B4EA2] focus:ring-blue-500"
                      />
                      Zápis (Write)
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Povolené IP adresy (oddelené čiarkou)</label>
                  <input
                    type="text"
                    value={formData.ip_whitelist}
                    onChange={(e) => setFormData({ ...formData, ip_whitelist: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-355 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="napr. 192.168.1.1, 10.0.0.1"
                  />
                </div>

                <div className="flex gap-4 pt-2">
                  <button
                    type="submit"
                    className="bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-2 rounded-lg transition-colors shadow-sm"
                  >
                    Vytvoriť kľúč
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-6 py-2 rounded-lg transition-colors border border-slate-200"
                  >
                    Zrušiť
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* API Keys List */}
          {loading ? (
            <div className="text-center text-slate-500 py-12">Načítavam...</div>
          ) : apiKeys.length === 0 ? (
            <div className="bg-white border border-slate-200 shadow-md rounded-xl p-12 text-center">
              <Key className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-slate-900 mb-2">Žiadne API kľúče</h3>
              <p className="text-slate-500 mb-6">Na začiatok programového prístupu si vytvorte svoj prvý API kľúč.</p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors shadow-sm"
              >
                Vytvoriť API kľúč
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className={`bg-white border rounded-xl p-6 shadow-sm ${
                    key.is_active ? 'border-slate-200' : 'border-red-200 bg-red-50/10'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-bold text-slate-900">{key.name}</h3>
                        {key.is_active ? (
                          <span className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 text-xs rounded font-semibold">Aktívny</span>
                        ) : (
                          <span className="px-2 py-1 bg-red-50 text-red-700 border border-red-200 text-xs rounded font-semibold">Zrušený</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <code className="text-slate-800 font-mono text-sm bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">{key.prefix}****</code>
                        <button
                          onClick={() => copyToClipboard(key.prefix + '****', key.id)}
                          className="text-[#0B4EA2] hover:text-blue-800 p-1 rounded hover:bg-slate-100 transition-colors"
                          title="Kopírovať prefix"
                        >
                          {copiedKeyId === key.id ? <CheckCircle size={16} /> : <Copy size={16} />}
                        </button>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-600">
                        <div>
                          <span className="font-semibold text-slate-800">Vytvorený:</span> {formatDate(key.created_at)}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-800">Expiruje:</span> {formatDate(key.expires_at) || 'Nikdy'}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-800">Naposledy použitý:</span> {formatDate(key.last_used_at)}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-800">Počet volaní:</span> {key.usage_count}
                        </div>
                      </div>
                      <div className="mt-3 flex gap-2">
                        {key.permissions.map((perm) => (
                          <span key={perm} className="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 text-xs rounded font-medium capitalize">
                            {perm}
                          </span>
                        ))}
                      </div>
                    </div>
                    {key.is_active && (
                      <button
                        onClick={() => handleRevokeKey(key.id)}
                        className="text-[#EE1C25] hover:text-red-700 p-2 transition-colors hover:bg-red-50 rounded"
                        title="Zrušiť kľúč"
                      >
                        <Trash2 size={20} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
};

export default ApiKeys;

