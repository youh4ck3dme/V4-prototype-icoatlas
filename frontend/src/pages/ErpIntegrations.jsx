import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const ErpIntegrations = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedErp, setSelectedErp] = useState('pohoda');
  const [formData, setFormData] = useState({
    api_key: '',
    company_id: '',
    base_url: '',
    username: '',
    password: '',
    server_url: '',
    company_db: ''
  });
  const [syncLogs, setSyncLogs] = useState({});
  const [syncing, setSyncing] = useState({});

  useEffect(() => {
    if (user?.tier !== 'enterprise') {
      return;
    }
    loadConnections();
  }, [user]);

  const loadConnections = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/enterprise/erp/connections', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
      }
    } catch (error) {
      console.error('Error loading connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddConnection = async (e) => {
    e.preventDefault();
    
    const connectionData = {};
    if (selectedErp === 'pohoda' || selectedErp === 'money_s3') {
      connectionData.api_key = formData.api_key;
      connectionData.company_id = formData.company_id;
      connectionData.base_url = formData.base_url || (selectedErp === 'pohoda' ? 'https://api.pohoda.sk' : 'https://api.moneys3.cz');
    } else if (selectedErp === 'sap') {
      connectionData.server_url = formData.server_url;
      connectionData.username = formData.username;
      connectionData.password = formData.password;
      connectionData.company_db = formData.company_db;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/enterprise/erp/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          erp_type: selectedErp,
          connection_data: connectionData,
          sync_frequency: 'daily'
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowAddModal(false);
          setFormData({
            api_key: '',
            company_id: '',
            base_url: '',
            username: '',
            password: '',
            server_url: '',
            company_db: ''
          });
          loadConnections();
        } else {
          alert('Failed to create connection: ' + (data.message || 'Unknown error'));
        }
      } else {
        const error = await response.json();
        alert('Error: ' + (error.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error creating connection:', error);
      alert('Error creating connection');
    }
  };

  const handleActivate = async (connectionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/enterprise/erp/${connectionId}/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        loadConnections();
      } else {
        const error = await response.json();
        alert('Error: ' + (error.detail || 'Failed to activate'));
      }
    } catch (error) {
      console.error('Error activating connection:', error);
      alert('Error activating connection');
    }
  };

  const handleDeactivate = async (connectionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/enterprise/erp/${connectionId}/deactivate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        loadConnections();
      } else {
        const error = await response.json();
        alert('Error: ' + (error.detail || 'Failed to deactivate'));
      }
    } catch (error) {
      console.error('Error deactivating connection:', error);
      alert('Error deactivating connection');
    }
  };

  const handleSync = async (connectionId) => {
    setSyncing({ ...syncing, [connectionId]: true });
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/enterprise/erp/${connectionId}/sync?sync_type=incremental`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Sync completed! Records synced: ${data.records_synced || 0}`);
        loadConnections();
        loadSyncLogs(connectionId);
      } else {
        const error = await response.json();
        alert('Error: ' + (error.detail || 'Sync failed'));
      }
    } catch (error) {
      console.error('Error syncing:', error);
      alert('Error syncing data');
    } finally {
      setSyncing({ ...syncing, [connectionId]: false });
    }
  };

  const loadSyncLogs = async (connectionId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/enterprise/erp/${connectionId}/logs?limit=10`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSyncLogs({ ...syncLogs, [connectionId]: data.logs || [] });
      }
    } catch (error) {
      console.error('Error loading sync logs:', error);
    }
  };

  if (user?.tier !== 'enterprise') {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white border border-slate-200 shadow-md rounded-xl p-8 max-w-md w-full text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Vyžaduje sa Enterprise úroveň</h1>
          <p className="text-slate-650 mb-6">ERP integrácie sú dostupné len pre predplatiteľov balíka Enterprise.</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg transition-colors shadow-sm"
          >
            Späť na Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-600 text-xl font-medium">Načítavam...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 pt-20 p-8">
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

      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">ERP Integrácie</h1>
          <p className="text-slate-555">Pripojte svoj ERP systém pre pokročilú analýzu rizík priamo vo vašom účtovníctve</p>
        </div>

        <div className="mb-6">
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg transition-colors shadow-sm font-semibold"
          >
            + Pridať ERP pripojenie
          </button>
        </div>

        <div className="grid gap-6">
          {connections.length === 0 ? (
            <div className="bg-white border border-slate-200 shadow-md rounded-xl p-12 text-center">
              <p className="text-slate-600 text-lg mb-4">Zatiaľ nie sú nastavené žiadne ERP pripojenia</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg transition-colors font-semibold"
              >
                Pridať prvé pripojenie
              </button>
            </div>
          ) : (
            connections.map((conn) => (
              <div key={conn.id} className="bg-white border border-slate-200 shadow-md rounded-xl p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900 mb-2">
                      {conn.erp_type.toUpperCase()}
                    </h3>
                    <p className="text-slate-600">
                      Stav: <span className={`font-bold ${conn.status === 'active' ? 'text-green-600' : 'text-red-650'}`}>
                        {conn.status === 'active' ? 'AKTÍVNE' : 'NEAKTÍVNE'}
                      </span>
                    </p>
                    {conn.company_name && (
                      <p className="text-slate-600">Firma: {conn.company_name}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {conn.status === 'active' ? (
                      <>
                        <button
                          onClick={() => handleSync(conn.id)}
                          disabled={syncing[conn.id]}
                          className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 font-semibold"
                        >
                          {syncing[conn.id] ? 'Synchronizujem...' : 'Sync Teraz'}
                        </button>
                        <button
                          onClick={() => handleDeactivate(conn.id)}
                          className="bg-[#EE1C25] hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors font-semibold"
                        >
                          Deaktivovať
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleActivate(conn.id)}
                        className="bg-[#0B4EA2] hover:bg-blue-800 text-white px-4 py-2 rounded-lg transition-colors font-semibold"
                      >
                        Aktivovať
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-4 text-sm text-slate-550 border-t border-slate-100 pt-3">
                  <p>Posledná synchronizácia: {conn.last_sync_at ? new Date(conn.last_sync_at).toLocaleString() : 'Nikdy'}</p>
                  <p>Nasledujúca synchronizácia: {conn.next_sync_at ? new Date(conn.next_sync_at).toLocaleString() : 'Nenaplánovaná'}</p>
                  <p>Frekvencia synchronizácie: {conn.sync_frequency}</p>
                </div>

                {conn.status === 'active' && (
                  <button
                    onClick={() => {
                      if (!syncLogs[conn.id]) {
                        loadSyncLogs(conn.id);
                      }
                    }}
                    className="mt-4 text-[#0B4EA2] hover:text-blue-800 text-sm font-semibold"
                  >
                    {syncLogs[conn.id] ? 'Skryť' : 'Zobraziť'} logy synchronizácie
                  </button>
                )}

                {syncLogs[conn.id] && (
                  <div className="mt-4 bg-slate-50 border border-slate-200 rounded-lg p-4">
                    <h4 className="text-slate-900 font-bold mb-2">Nedávne synchronizácie</h4>
                    {syncLogs[conn.id].length === 0 ? (
                      <p className="text-slate-500 text-sm italic">Žiadne záznamy</p>
                    ) : (
                      <div className="space-y-2">
                        {syncLogs[conn.id].slice(0, 5).map((log) => (
                          <div key={log.id} className="text-sm text-slate-700">
                            <span className={`font-semibold ${log.status === 'success' ? 'text-green-600' : 'text-red-650'}`}>
                              {log.status.toUpperCase()}
                            </span>
                            {' '}
                            - {log.records_synced} záznamov synchronizovaných
                            {' '}
                            - {new Date(log.started_at).toLocaleString()}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {showAddModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full border border-slate-200">
              <h2 className="text-2xl font-bold text-slate-900 mb-4 border-b border-slate-100 pb-2">Pridať ERP pripojenie</h2>
              
              <form onSubmit={handleAddConnection}>
                <div className="mb-4">
                  <label className="block text-slate-700 mb-2 font-medium">ERP Systém</label>
                  <select
                    value={selectedErp}
                    onChange={(e) => setSelectedErp(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                  >
                    <option value="pohoda">Pohoda (SK)</option>
                    <option value="money_s3">Money S3 (CZ)</option>
                    <option value="sap">SAP</option>
                  </select>
                </div>

                {selectedErp === 'pohoda' || selectedErp === 'money_s3' ? (
                  <>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">API Kľúč</label>
                      <input
                        type="text"
                        value={formData.api_key}
                        onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">ID Spoločnosti</label>
                      <input
                        type="text"
                        value={formData.company_id}
                        onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">Základná URL (voliteľné)</label>
                      <input
                        type="text"
                        value={formData.base_url}
                        onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        placeholder={selectedErp === 'pohoda' ? 'https://api.pohoda.sk' : 'https://api.moneys3.cz'}
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">URL Servera</label>
                      <input
                        type="text"
                        value={formData.server_url}
                        onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">Používateľské meno</label>
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">Heslo</label>
                      <input
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label className="block text-slate-700 mb-2 font-medium">Databáza Spoločnosti</label>
                      <input
                        type="text"
                        value={formData.company_db}
                        onChange={(e) => setFormData({ ...formData, company_db: e.target.value })}
                        className="w-full bg-slate-50 border border-slate-300 text-slate-900 px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-[#0B4EA2]"
                        required
                      />
                    </div>
                  </>
                )}

                <div className="flex gap-4 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-[#0B4EA2] hover:bg-blue-800 text-white px-6 py-3 rounded-lg transition-colors font-semibold shadow-sm"
                  >
                    Pripojiť
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 px-6 py-3 rounded-lg transition-colors font-semibold border border-slate-200"
                  >
                    Zrušiť
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ErpIntegrations;

