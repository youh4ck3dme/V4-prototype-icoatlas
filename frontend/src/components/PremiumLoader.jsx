import React, { useState, useEffect } from "react";
import { Search, Shield, Database, Activity, Loader2 } from "lucide-react";

/**
 * Premium Fullscreen Loader for "Deep Analysis" feel
 */
const PremiumLoader = () => {
  const [statusIndex, setStatusIndex] = useState(0);
  const statuses = [
    {
      text: "Inicializácia hĺbkovej analýzy...",
      icon: <Search className="text-blue-500" />,
    },
    {
      text: "Krížová kontrola registrov V4...",
      icon: <Database className="text-blue-500" />,
    },
    {
      text: "Sťahovanie dát z live SCRAPER-a...",
      icon: <Activity className="text-blue-500" />,
    },
    {
      text: "Výpočet rizikového profilu (Risk Score)...",
      icon: <Shield className="text-blue-500" />,
    },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setStatusIndex((prev) => (prev + 1) % statuses.length);
    }, 800); // Change text every 800ms to fit into 3s window
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center p-6 backdrop-blur-md bg-white/70 overflow-hidden">
      {/* Background Pulse Effect */}
      <div className="absolute inset-0 z-[-1] opacity-20">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-400 rounded-full blur-[100px] animate-pulse"></div>
      </div>

      {/* Main Loader Container */}
      <div className="max-w-md w-full text-center space-y-8 animate-in fade-in zoom-in duration-500">
        {/* Animated Scanner Hexagon */}
        <div className="relative mx-auto w-24 h-24 flex items-center justify-center">
          <div className="absolute inset-0 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
          <div className="absolute inset-4 border-2 border-slate-100 border-b-blue-400 rounded-full animate-spin-slow"></div>
          <div className="z-10 bg-white p-4 rounded-full shadow-lg border border-slate-50">
            {statuses[statusIndex].icon}
          </div>
        </div>

        {/* Text Area */}
        <div className="space-y-3">
          <h2 className="text-2xl font-heading font-bold text-slate-900 tracking-tight">
            Prebieha hĺbková analýza
          </h2>
          <div className="flex flex-col items-center gap-2">
            {/* Progress Bar */}
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden max-w-[240px]">
              <div
                className="h-full bg-blue-600 transition-all duration-300 ease-out"
                style={{ width: `${(statusIndex + 1) * 25}%` }}
              ></div>
            </div>

            <p className="text-slate-500 text-sm font-medium animate-pulse">
              {statuses[statusIndex].text}
            </p>
          </div>
        </div>

        {/* Tip / Footer */}
        <p className="text-xs text-slate-400 max-w-[240px] mx-auto italic">
          Nájdené údaje sú overované v reálnom čase z registrovaných zdrojov SR.
        </p>
      </div>

      <style jsx="true">{`
        @keyframes spin-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(-360deg);
          }
        }
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default PremiumLoader;
