import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import IcoAtlasLogo from '../components/IcoAtlasLogo';
import { API_URL } from '../config/api';

const PaymentSuccess = () => {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [sessionData, setSessionData] = useState(null);

  useEffect(() => {
    // Refresh user data to get updated tier
    refreshUser?.();

    // Verify session
    if (sessionId) {
      fetch(`${API_URL}/api/payment/verify-session/${sessionId}`)
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data) setSessionData(data);
        })
        .catch(console.error);
    }

    // Redirect to dashboard after 5 seconds
    const timer = setTimeout(() => {
      navigate('/dashboard');
    }, 5000);

    return () => clearTimeout(timer);
  }, [refreshUser, navigate, sessionId]);

  return (
    <div className="min-h-[100dvh] bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white border border-slate-200 shadow-md rounded-2xl p-8 text-center animate-fade-in">
        <IcoAtlasLogo className="mx-auto mb-6" />
        <div className="mb-6">
          <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm text-white">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Platba úspešná!</h1>
          <p className="text-slate-600 text-sm">Vaše predplatné bolo úspešne aktivované cez Stripe.</p>
        </div>

        {sessionData && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-left">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-slate-500 uppercase font-bold tracking-wider">Aktivovaný plán</span>
              <span className="px-2 py-0.5 rounded text-xs font-bold uppercase bg-blue-100 text-[#0B4EA2]">
                {sessionData.tier || 'PRO'}
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-600 font-medium">Uhradená suma:</span>
              <span className="font-bold text-slate-900">{sessionData.amount_total} {sessionData.currency}</span>
            </div>
          </div>
        )}

        {sessionId && (
          <p className="text-[11px] font-mono text-slate-400 bg-slate-100 p-2 rounded-lg border border-slate-200 mb-6 break-all">
            ID Relácie: {sessionId}
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex-1 py-2.5 px-4 bg-[#0B4EA2] hover:bg-blue-800 text-white rounded-xl font-bold text-sm transition-all"
          >
            Prejsť na Dashboard
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-sm transition-all"
          >
            Vyhľadávať firmy
          </button>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccess;

