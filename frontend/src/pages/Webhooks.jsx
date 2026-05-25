import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';
import IcoAtlasLogo from '../components/IcoAtlasLogo';
import { Copy, Trash2, Plus, Webhook, CheckCircle, AlertCircle, Eye, EyeOff, Clock } from 'lucide-react';

const AVAILABLE_EVENTS = [
    'company.created',
    'company.updated',
    'risk_score.changed',
    'subscription.activated',
    'subscription.cancelled'
];

const Webhooks = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWebhook, setNewWebhook] = useState(null);
  const [selectedWebhook, setSelectedWebhook] = useState(null);
  const [logs, setLogs] = useState([]);
  const [copiedSecretId, setCopiedSecretId] = useState(null);
  const [formData, setFormData] = useState({
    url: '',
    events: [],
    secret: ''
  });

  useEffect(() => {
    if (user?.tier === 'enterprise') {
      loadWebhooks();
    }
  }, [user]);

  const loadWebhooks = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/enterprise/webhooks', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setWebhooks(data.webhooks || []);
      }
    } catch (error) {
      console.error('Error loading webhooks:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadWebhookLogs = async (webhookId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/enterprise/webhooks/${webhookId}/logs?limit=20`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Error loading webhook logs:', error);
    }
  };

  const handleCreateWebhook = async (e) => {
    e.preventDefault();
    
    if (formData.events.length === 0) {
      alert('Prosím, vyberte aspoň jeden typ udalosti');
      return;
    }

    try {
      const payload = {
        url: formData.url,
        events: formData.events,
      };

      if (formData.secret) {
        payload.secret = formData.secret;
      }

      const response = await fetch('http://localhost:8000/api/enterprise/webhooks', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setNewWebhook(data.data);
        setShowCreateForm(false);
        setFormData({
          url: '',
          events: [],
          secret: ''
        });
        loadWebhooks();
      }
    } catch (error) {
      console.error('Error creating webhook:', error);
    }
  };

  const handleDeleteWebhook = async (webhookId) => {
    if (!confirm('Naozaj chcete vymazať tento webhook?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/enterprise/webhooks/${webhookId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        loadWebhooks();
        if (selectedWebhook === webhookId) {
          setSelectedWebhook(null);
          setLogs([]);
        }
      }
    } catch (error) {
      console.error('Error deleting webhook:', error);
    }
  };

  const toggleEvent = (event) => {
    if (formData.events.includes(event)) {
      setFormData({ ...formData, events: formData.events.filter(e => e !== event) });
    } else {
      setFormData({ ...formData, events: [...formData.events, event] });
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedSecretId(id);
    setTimeout(() => setCopiedSecretId(null), 2000);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Nikdy';
    return new Date(dateString).toLocaleString();
  };

  if (user?.tier !== 'enterprise') {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white border border-slate-200 shadow-md rounded-xl p-8 text-center animate-fade-in">
            <IcoAtlasLogo className="mx-auto mb-6" />
            <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Vyžaduje sa Enterprise úroveň</h1>
            <p className="text-slate-650 mb-6">Webhooks sú dostupné len pre predplatiteľov balíka Enterprise.</p>
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
              <h1 className="text-3xl font-bold text-slate-900 mb-2">Webhooks</h1>
              <p className="text-slate-500">Spravujte notifikácie o udalostiach v reálnom čase</p>
            </div>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2 shadow-sm"
            >
              <Plus size={20} />
              Vytvoriť Webhook
            </button>
          </div>

          {/* New Webhook Display */}
          {newWebhook && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="text-green-600" size={24} />
                  <h3 className="text-xl font-bold text-green-800">Webhook bol úspešne vytvorený!</h3>
                </div>
                <button
                  onClick={() => setNewWebhook(null)}
                  className="text-slate-400 hover:text-slate-600 font-bold text-lg"
                >
                  ×
                </button>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Tajný kľúč (Secret Key)</label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-slate-100 border border-slate-200 rounded-lg p-3 text-slate-800 font-mono text-sm break-all">
                      {newWebhook.secret}
                    </code>
                    <button
                      onClick={() => copyToClipboard(newWebhook.secret, 'new')}
                      className="text-[#0B4EA2] hover:text-blue-800 p-1"
                    >
                      {copiedSecretId === 'new' ? <CheckCircle size={20} /> : <Copy size={20} />}
                    </button>
                  </div>
                </div>
                <p className="text-yellow-800 text-sm font-semibold">
                  ⚠️ Pozor! Dobre si uložte tento tajný kľúč. Zobrazí sa iba raz a slúži na verifikáciu podpisu webhookov.
                </p>
              </div>
            </div>
          )}

          {/* Create Form */}
          {showCreateForm && (
            <div className="bg-white border border-slate-200 shadow-md rounded-xl p-6 mb-6">
              <h2 className="text-xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">Vytvoriť nový Webhook</h2>
              <form onSubmit={handleCreateWebhook} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Webhook URL</label>
                  <input
                    type="url"
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    required
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-355 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="https://vasa-aplikacia.sk/webhooks/icoatlas"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Udalosti (Events)</label>
                  <div className="space-y-2 bg-slate-50 border border-slate-200 rounded-lg p-4">
                    {AVAILABLE_EVENTS.map((event) => (
                      <label key={event} className="flex items-center text-slate-700 cursor-pointer hover:bg-slate-100/50 p-2 rounded transition-colors">
                        <input
                          type="checkbox"
                          checked={formData.events.includes(event)}
                          onChange={() => toggleEvent(event)}
                          className="mr-3 rounded border-slate-300 text-[#0B4EA2] focus:ring-blue-500"
                        />
                        <code className="text-sm text-slate-800 font-mono font-semibold">{event}</code>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Tajný kľúč - Secret (voliteľné)</label>
                  <input
                    type="text"
                    value={formData.secret}
                    onChange={(e) => setFormData({ ...formData, secret: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-355 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Ponechajte prázdne pre automatické vygenerovanie"
                  />
                  <p className="text-xs text-slate-550 mt-1">Slúži na overenie pravosti HMAC podpisu.</p>
                </div>

                <div className="flex gap-4 pt-2">
                  <button
                    type="submit"
                    className="bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-2 rounded-lg transition-colors shadow-sm"
                  >
                    Vytvoriť Webhook
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

          {/* Webhooks List */}
          {loading ? (
            <div className="text-center text-slate-500 py-12">Načítavam...</div>
          ) : webhooks.length === 0 ? (
            <div className="bg-white border border-slate-200 shadow-md rounded-xl p-12 text-center">
              <Webhook className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-slate-900 mb-2">Žiadne Webhooky</h3>
              <p className="text-slate-500 mb-6">Vytvorte si svoj prvý webhook pre odosielanie notifikácií v reálnom čase.</p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-[#0B4EA2] hover:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors shadow-sm"
              >
                Vytvoriť Webhook
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Webhooks List */}
              <div className="lg:col-span-2 space-y-4">
                {webhooks.map((webhook) => (
                  <div
                    key={webhook.id}
                    className={`bg-white border rounded-xl p-6 shadow-sm ${
                      webhook.is_active ? 'border-slate-200' : 'border-red-200 bg-red-50/10'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                          <Webhook className="text-[#0B4EA2]" size={20} />
                          <code className="text-slate-800 font-mono text-sm break-all bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">{webhook.url}</code>
                          {webhook.is_active ? (
                            <span className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 text-xs rounded font-semibold">Aktívny</span>
                          ) : (
                            <span className="px-2 py-1 bg-red-50 text-red-700 border border-red-200 text-xs rounded font-semibold">Neaktívny</span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-3">
                          {webhook.events.map((event) => (
                            <span key={event} className="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 text-xs rounded font-medium">
                              {event}
                            </span>
                          ))}
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm text-slate-600">
                          <div>
                            <span className="font-semibold text-slate-800">Vytvorený:</span> {formatDate(webhook.created_at)}
                          </div>
                          <div>
                            <span className="font-semibold text-slate-800">Doručené:</span> {formatDate(webhook.last_delivered_at)}
                          </div>
                          <div>
                            <span className="font-semibold text-slate-800">Úspešné:</span> {webhook.success_count}
                          </div>
                          <div>
                            <span className="font-semibold text-slate-800">Neúspešné:</span> {webhook.failure_count}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedWebhook(webhook.id);
                            loadWebhookLogs(webhook.id);
                          }}
                          className="text-[#0B4EA2] hover:text-blue-800 p-2 hover:bg-slate-100 rounded transition-colors"
                          title="Zobraziť logy"
                        >
                          <Eye size={20} />
                        </button>
                        <button
                          onClick={() => handleDeleteWebhook(webhook.id)}
                          className="text-[#EE1C25] hover:text-red-700 p-2 hover:bg-red-50 rounded transition-colors"
                          title="Vymazať webhook"
                        >
                          <Trash2 size={20} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Logs Panel */}
              {selectedWebhook && (
                <div className="lg:col-span-1 bg-white border border-slate-200 shadow-sm rounded-xl p-6">
                  <div className="flex justify-between items-center mb-4 border-b border-slate-100 pb-2">
                    <h3 className="text-lg font-bold text-slate-900">Doručovacie logy</h3>
                    <button
                      onClick={() => setSelectedWebhook(null)}
                      className="text-slate-400 hover:text-slate-600 font-bold text-lg"
                    >
                      ×
                    </button>
                  </div>
                  <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                    {logs.length === 0 ? (
                      <p className="text-slate-500 italic text-sm">Žiadne pokusy o doručenie</p>
                    ) : (
                      logs.map((log) => (
                        <div
                          key={log.id}
                          className={`p-3 rounded-lg border text-sm ${
                            log.success ? 'bg-green-50/50 border-green-200' : 'bg-red-50/50 border-red-200'
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            {log.success ? (
                              <CheckCircle className="text-green-600" size={16} />
                            ) : (
                              <AlertCircle className="text-red-650" size={16} />
                            )}
                            <code className="text-slate-800 text-xs font-mono font-semibold">{log.event_type}</code>
                          </div>
                          <div className="text-slate-500 text-xs flex items-center gap-1">
                            <Clock size={12} />
                            {formatDate(log.delivery_time)}
                          </div>
                          {log.response_status && (
                            <div className="text-xs text-slate-700 mt-1 font-medium">
                              Odozva: status {log.response_status}
                            </div>
                          )}
                          {log.error_message && (
                            <div className="text-xs text-red-700 mt-1">
                              {log.error_message}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
};

export default Webhooks;

