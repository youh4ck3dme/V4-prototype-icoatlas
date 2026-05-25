import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const RateLimitIndicator = () => {
  const { isAuthenticated, token } = useAuth();
  const [limits, setLimits] = useState(null);
  const [usage, setUsage] = useState({ searches_used: 0, searches_per_day: 10 });

  useEffect(() => {
    if (isAuthenticated && token) {
      loadLimits();
    }
  }, [isAuthenticated, token]);

  const loadLimits = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/tier/limits', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setLimits(data);
        // Simulácia usage (v produkcii by to bolo z backendu)
        setUsage({
          searches_used: 5, // Príklad
          searches_per_day: data.searches_per_day === -1 ? 999 : data.searches_per_day,
        });
      }
    } catch (error) {
      console.error('Error loading limits:', error);
    }
  };

  if (!isAuthenticated || !limits) {
    return null;
  }

  const percentage = limits.searches_per_day === -1 
    ? 0 
    : (usage.searches_used / limits.searches_per_day) * 100;
  const isWarning = percentage >= 80;
  const isError = percentage >= 100;

  return (
    <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-850">Denné vyhľadávania</span>
        <span className={`text-sm font-semibold ${
          isError ? 'text-red-650' : isWarning ? 'text-amber-650' : 'text-green-650'
        }`}>
          {limits.searches_per_day === -1 
            ? 'Neobmedzene' 
            : `${usage.searches_used} / ${limits.searches_per_day}`}
        </span>
      </div>
      {limits.searches_per_day !== -1 && (
        <>
          <div className="w-full bg-slate-100 rounded-full h-2 mb-2">
            <div
              className={`h-2 rounded-full transition-all ${
                isError ? 'bg-red-600' : isWarning ? 'bg-amber-500' : 'bg-green-600'
              }`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            ></div>
          </div>
          {isWarning && (
            <p className="text-xs text-amber-700 font-medium">
              {isError 
                ? 'Denný limit bol dosiahnutý. Pre pokračovanie prejdite na vyšší program.' 
                : 'Blížite sa k dennému limitu. Zvážte prechod na vyšší program.'}
            </p>
          )}
        </>
      )}
    </div>
  );
};

export default RateLimitIndicator;

