import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Shield, 
  ShieldAlert,
  Cookie, 
  AlertCircle, 
  ExternalLink,
  Database,
  Lock,
  Globe2,
  Cpu,
  Layers,
  Sparkles,
  ArrowUpRight,
  ArrowUp,
  Clock,
  Radio
} from 'lucide-react';
import IcoAtlasLogo from './IcoAtlasLogo';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const registrySources = [
    {
      name: 'Obchodný register SR (ORSR)',
      url: 'https://www.orsr.sk',
      badge: 'SK',
      flag: '🇸🇰',
      desc: 'Obchodné spoločnosti a štatutári',
      syncTime: 'Dnes 04:00'
    },
    {
      name: 'Živnostenský register SR (ZRSR)',
      url: 'https://www.zrsr.sk',
      badge: 'SK',
      flag: '🇸🇰',
      desc: 'Fyzické osoby a živnostníci',
      syncTime: 'Dnes 04:00'
    },
    {
      name: 'Register účtovných závierok (RUZ)',
      url: 'https://www.registeruz.sk',
      badge: 'SK',
      flag: '🇸🇰',
      desc: 'Účtovné závierky a hospodárske výsledky',
      syncTime: 'Dnes 04:00'
    },
    {
      name: 'ARES (ČR)',
      url: 'https://wwwinfo.mfcr.cz',
      badge: 'CZ',
      flag: '🇨🇿',
      desc: 'Administrativní registr MF ČR',
      syncTime: 'Dnes 04:00'
    },
    {
      name: 'Finančná správa SR',
      url: 'https://www.financnasprava.sk',
      badge: 'SK',
      flag: '🇸🇰',
      desc: 'Zoznamy daňových a DPH dlžníkov',
      syncTime: 'Dnes 04:00'
    },
  ];

  return (
    <footer 
      role="contentinfo" 
      className="relative overflow-hidden bg-slate-950 text-slate-300 mt-20 border-t border-blue-500/25 shadow-[0_-20px_50px_rgba(11,78,162,0.2)] selection:bg-cyan-500/30 selection:text-white"
    >
      {/* --- LIQUID GLASS AMBIENT LIGHTING & GLOW MESH --- */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Top luminous neon cyan border line */}
        <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-80 shadow-[0_0_15px_#38bdf8]" />

        {/* Ambient translucent blue orbs */}
        <div className="absolute -top-32 left-1/4 w-[500px] h-[250px] bg-blue-600/20 rounded-full blur-[100px]" />
        <div className="absolute top-1/3 right-10 w-[450px] h-[300px] bg-cyan-600/15 rounded-full blur-[120px]" />
        <div className="absolute -bottom-20 left-10 w-[400px] h-[250px] bg-indigo-600/15 rounded-full blur-[100px]" />

        {/* Cyber grid glass pattern */}
        <div 
          className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,#ffffff_1px,transparent_1px),linear-gradient(to_bottom,#ffffff_1px,transparent_1px)] bg-[size:32px_32px]" 
        />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 pt-16 pb-12">
        {/* --- TOP GRID: 4 LIQUID GLASS SECTIONS --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          
          {/* Kolónka 1: O projekte & Brand */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-blue-950/35 to-slate-900/40 backdrop-blur-xl border border-blue-500/20 shadow-[0_8px_32px_0_rgba(11,78,162,0.2)] hover:border-cyan-400/35 transition-all duration-300 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-1.5 rounded-xl bg-blue-600/20 border border-blue-400/30 shadow-[0_0_15px_rgba(56,189,248,0.25)]">
                  <IcoAtlasLogo size={32} />
                </div>
                <div>
                  <span className="text-xl font-extrabold tracking-tight text-white leading-none">
                    iCO<span className="text-cyan-400">Atlas</span>
                  </span>
                  <span className="block text-[10px] text-cyan-300/80 font-mono tracking-widest uppercase mt-0.5">
                    Identifier Intelligence
                  </span>
                </div>
              </div>

              <p className="text-sm text-slate-300/90 leading-relaxed mb-4">
                Business Intelligence & Visualization pre V4 región. 
                Demokratizácia prístupu k dátam pre malé a stredné podniky.
              </p>
            </div>

            <div className="pt-4 border-t border-blue-500/15 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
              <span className="text-xs text-slate-300 font-medium">
                V4 Identity Graph v4.2 Live
              </span>
            </div>
          </div>

          {/* Kolónka 2: Právne dokumenty */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-blue-950/30 to-slate-900/40 backdrop-blur-xl border border-blue-500/20 shadow-[0_8px_32px_0_rgba(11,78,162,0.15)] hover:border-cyan-400/35 transition-all duration-300">
            <h4 className="text-white font-semibold mb-4 flex items-center gap-2 text-sm tracking-wide">
              <div className="p-1 rounded-lg bg-blue-500/20 text-cyan-400">
                <FileText size={16} />
              </div>
              Právne dokumenty
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/vop" className="hover:text-cyan-300 transition-colors text-slate-300 hover:translate-x-1 inline-block duration-150 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded">
                  Všeobecné obchodné podmienky
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="hover:text-cyan-300 transition-colors text-slate-300 hover:translate-x-1 inline-block duration-150 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded">
                  Zásady ochrany osobných údajov
                </Link>
              </li>
              <li>
                <Link to="/disclaimer" className="hover:text-cyan-300 transition-colors text-slate-300 hover:translate-x-1 inline-block duration-150 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded">
                  Vyhlásenie o odmietnutí zodpovednosti
                </Link>
              </li>
              <li>
                <Link to="/cookies" className="hover:text-cyan-300 transition-colors text-slate-300 hover:translate-x-1 inline-block duration-150 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded">
                  Zásady cookies
                </Link>
              </li>
              <li>
                <Link to="/dpa" className="hover:text-cyan-300 transition-colors text-slate-300 hover:translate-x-1 inline-block duration-150 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded">
                  Zmluva o spracovaní osobných údajov (B2B)
                </Link>
              </li>
              <li>
                <Link to="/license" className="hover:text-cyan-300 transition-colors text-slate-300 hover:translate-x-1 inline-block duration-150 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded">
                  Open-source licencia
                </Link>
              </li>
            </ul>
          </div>

          {/* Kolónka 3: Kontakt & Bezpečnosť */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-blue-950/30 to-slate-900/40 backdrop-blur-xl border border-blue-500/20 shadow-[0_8px_32px_0_rgba(11,78,162,0.15)] hover:border-cyan-400/35 transition-all duration-300">
            <h4 className="text-white font-semibold mb-4 flex items-center gap-2 text-sm tracking-wide">
              <div className="p-1 rounded-lg bg-blue-500/20 text-cyan-400">
                <Shield size={16} />
              </div>
              Kontakt
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a 
                  href="mailto:support@icoatlas.sk" 
                  className="hover:text-cyan-300 transition-colors text-slate-300 flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded"
                >
                  <span>support@icoatlas.sk</span>
                  <ArrowUpRight size={13} className="text-cyan-400/70" />
                </a>
              </li>
              <li>
                <a 
                  href="mailto:support@icoatlas.sk" 
                  className="hover:text-cyan-300 transition-colors text-slate-300 flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none rounded"
                >
                  <span>support@icoatlas.sk (GDPR)</span>
                  <ArrowUpRight size={13} className="text-cyan-400/70" />
                </a>
              </li>
              <li className="text-slate-400 text-xs pt-1 leading-relaxed">
                Pre otázky týkajúce sa GDPR a ochrany údajov
              </li>
              <li className="text-slate-300 text-xs pt-2 border-t border-blue-500/15">
                <span className="font-semibold text-white">iCOAtlas s.r.o.</span><br/>
                Bratislava, Slovensko
              </li>
            </ul>
          </div>

          {/* Kolónka 4: Informácie & Technológie */}
          <div className="p-6 rounded-2xl bg-gradient-to-b from-blue-950/30 to-slate-900/40 backdrop-blur-xl border border-blue-500/20 shadow-[0_8px_32px_0_rgba(11,78,162,0.15)] hover:border-cyan-400/35 transition-all duration-300">
            <h4 className="text-white font-semibold mb-4 flex items-center gap-2 text-sm tracking-wide">
              <div className="p-1 rounded-lg bg-blue-500/20 text-cyan-400">
                <AlertCircle size={16} />
              </div>
              Dôležité
            </h4>
            <p className="text-sm text-slate-300/90 mb-3 leading-relaxed">
              Dáta zobrazené na portáli sú agregované z verejných zdrojov. 
              Slúžia výhradne na podporu rozhodovania a nenahrádzajú oficiálne právne úkony.
            </p>
            <p className="text-xs text-cyan-300/80 italic bg-blue-950/50 p-2.5 rounded-xl border border-blue-500/20">
              Poskytovateľ negarantuje správnosť dát. Dáta majú len informatívny charakter.
            </p>
          </div>

        </div>

        {/* --- PREPRACOVANÝ LIQUID GLASS DISCLAIMER & REGISTRY HUD --- */}
        <div className="relative rounded-2xl p-6 sm:p-8 bg-gradient-to-r from-blue-950/60 via-slate-900/80 to-blue-900/40 backdrop-blur-2xl border border-blue-400/30 shadow-[0_12px_40px_0_rgba(11,78,162,0.35)] overflow-visible">
          {/* Subtle inner top glow */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent pointer-events-none" />
          
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-2xl bg-blue-500/20 border border-blue-400/40 text-cyan-400 shadow-[0_0_20px_rgba(56,189,248,0.35)] flex-shrink-0">
                <ShieldAlert size={24} className="animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-3 flex-wrap">
                  <h3 className="text-white font-bold text-base sm:text-lg tracking-wide">
                    Dôležité upozornenie
                  </h3>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-400/30">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                    OFICIÁLNE REGISTRE
                  </span>
                </div>
                <p className="text-slate-300 text-xs sm:text-sm mt-1.5 leading-relaxed max-w-3xl">
                  Dáta majú len informatívny charakter. Poskytovateľ negarantuje správnosť dát. Pre oficiálne informácie použite pôvodné zdroje.
                </p>
              </div>
            </div>

            <Link
              to="/disclaimer"
              className="self-start lg:self-center inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600/30 hover:bg-blue-500/40 border border-cyan-400/40 text-cyan-200 hover:text-white text-xs sm:text-sm font-semibold tracking-wide transition-all duration-300 shadow-[0_0_20px_rgba(56,189,248,0.25)] hover:shadow-[0_0_30px_rgba(56,189,248,0.45)] hover:-translate-y-0.5 whitespace-nowrap focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none"
            >
              <span>Viac informácií o vylúčení zodpovednosti</span>
              <ExternalLink size={14} />
            </Link>
          </div>

          {/* Primary Registry Sources Grid */}
          <div className="mt-6">
            <div className="flex items-center gap-2 mb-4">
              <Database size={15} className="text-cyan-400" />
              <p className="text-xs uppercase tracking-widest text-cyan-300 font-bold">
                Zdroj dát:
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
              {registrySources.map((source) => (
                <div key={source.name} className="relative group">
                  {/* Quick Win 2: Micro-Interaction Tooltip on Hover */}
                  <div className="absolute -top-10 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-200 transform group-hover:-translate-y-1 z-30 whitespace-nowrap bg-slate-900/95 text-cyan-300 text-[10px] font-mono px-3 py-1 rounded-lg border border-cyan-400/40 shadow-[0_0_20px_rgba(56,189,248,0.35)] backdrop-blur-md flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Posledná aktualizácia: {source.syncTime}</span>
                  </div>

                  {/* Quick Win 1: Focus Ring Glow (Klávesnica) */}
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="relative p-3.5 rounded-xl bg-blue-950/40 hover:bg-blue-600/25 border border-blue-400/20 hover:border-cyan-400/60 transition-all duration-300 shadow-sm hover:shadow-[0_0_25px_rgba(56,189,248,0.25)] hover:-translate-y-1 flex flex-col justify-between h-full focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
                  >
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-500/20 text-cyan-300 border border-blue-400/30 flex items-center gap-1.5">
                        <span>{source.flag}</span>
                        <span>{source.badge}</span>
                      </span>
                      <ExternalLink 
                        size={13} 
                        className="text-slate-400 group-hover:text-cyan-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-200" 
                      />
                    </div>

                    <div>
                      <p className="text-white text-xs font-semibold group-hover:text-cyan-200 transition-colors leading-snug">
                        {source.name}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-1 line-clamp-1 group-hover:text-slate-300 transition-colors">
                        {source.desc}
                      </p>
                    </div>

                    {/* Glanceable Micro Status Indicator */}
                    <div className="mt-2.5 pt-2 border-t border-blue-500/15 flex items-center justify-between text-[9px] text-cyan-300/80 font-mono">
                      <span className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Live Sync
                      </span>
                      <span>{source.syncTime}</span>
                    </div>
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* --- BOTTOM BAR: COPYRIGHT, V4 BADGES & BACK TO TOP PILL --- */}
        <div className="border-t border-blue-500/20 mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p className="text-center sm:text-left">
            &copy; {currentYear} <span className="text-slate-200 font-medium">iCOAtlas s.r.o.</span> • V4 Identifier Intelligence. Všetky práva vyhradené.
          </p>

          <div className="flex items-center gap-3 flex-wrap justify-center">
            <div className="flex items-center gap-1.5">
              <span className="px-2.5 py-1 rounded-md bg-blue-950/60 border border-blue-500/20 text-[11px] text-slate-300 font-mono">
                🇸🇰 SK
              </span>
              <span className="px-2.5 py-1 rounded-md bg-blue-950/60 border border-blue-500/20 text-[11px] text-slate-300 font-mono">
                🇨🇿 CZ
              </span>
              <span className="px-2.5 py-1 rounded-md bg-blue-950/60 border border-blue-500/20 text-[11px] text-slate-300 font-mono">
                🇵🇱 PL
              </span>
              <span className="px-2.5 py-1 rounded-md bg-blue-950/60 border border-blue-500/20 text-[11px] text-slate-300 font-mono">
                🇭🇺 HU
              </span>
            </div>

            <span className="text-slate-500 hidden md:inline">•</span>

            {/* Quick Win 3: Back to top pill */}
            <button
              type="button"
              onClick={scrollToTop}
              className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-blue-900/40 hover:bg-blue-600/30 border border-blue-400/30 hover:border-cyan-400/60 text-cyan-200 hover:text-white text-xs font-semibold tracking-wide transition-all duration-300 shadow-sm hover:shadow-[0_0_15px_rgba(56,189,248,0.3)] hover:-translate-y-0.5 active:scale-95 focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:outline-none cursor-pointer"
              aria-label="Prejsť späť hore na vyhľadávanie"
              title="Prejsť späť hore na vyhľadávanie"
            >
              <ArrowUp size={12} className="text-cyan-400 animate-bounce" />
              <span>↑ Hore</span>
            </button>
          </div>
        </div>

      </div>
    </footer>
  );
};

export default Footer;
