import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import IcoAtlasLogo from '../components/IcoAtlasLogo';

const PaymentSuccess = () => {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    // Refresh user data to get updated tier
    refreshUser();

    // Redirect to dashboard after 3 seconds
    const timer = setTimeout(() => {
      navigate('/dashboard');
    }, 3000);

    return () => clearTimeout(timer);
  }, [refreshUser, navigate]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white border border-slate-200 shadow-md rounded-xl p-8 text-center animate-fade-in">
        <IcoAtlasLogo className="mx-auto mb-6" />
        <div className="mb-6">
          <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Platba úspešná!</h1>
          <p className="text-slate-650">Vaše predplatné bolo úspešne aktivované.</p>
        </div>
        {sessionId && (
          <p className="text-xs font-mono text-slate-500 bg-slate-100 p-2 rounded border border-slate-200 mb-6 break-all">ID Relácie: {sessionId}</p>
        )}
        <p className="text-slate-500 text-sm animate-pulse">Presmerovávam vás na dashboard...</p>
      </div>
    </div>
  );
};

export default PaymentSuccess;

