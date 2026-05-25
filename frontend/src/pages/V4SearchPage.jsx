import React from 'react';
import V4Search from '../components/V4Search';
import IcoAtlasLogo from '../components/IcoAtlasLogo';
import { useAuth } from '../contexts/AuthContext';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Search, LogOut, User } from 'lucide-react';

const V4SearchPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Sidebar / Top Nav Hybrid */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <IcoAtlasLogo />
              <div className="hidden md:flex items-center gap-4">
                <NavLink 
                  to="/dashboard" 
                  className={({isActive}) => `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-bold transition-all ${isActive ? 'bg-blue-50 text-[#0B4EA2]' : 'text-slate-500 hover:bg-slate-50'}`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </NavLink>
                <NavLink 
                  to="/v4" 
                  className={({isActive}) => `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-bold transition-all ${isActive ? 'bg-blue-50 text-[#0B4EA2]' : 'text-slate-500 hover:bg-slate-50'}`}
                >
                  <Search className="w-4 h-4" />
                  V4 Intelligence
                </NavLink>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex flex-col text-right mr-2">
                <span className="text-sm font-bold text-slate-900">{user?.full_name || 'Používateľ'}</span>
                <span className="text-xs text-slate-500 uppercase tracking-widest">Program {user?.tier === 'pro' ? 'Pro' : user?.tier === 'enterprise' ? 'Enterprise' : 'Bezplatný'}</span>
              </div>
              <button 
                onClick={() => navigate('/profile')}
                className="p-2 bg-slate-100 rounded-full text-slate-600 hover:bg-blue-50 hover:text-[#0B4EA2] transition-all"
              >
                <User className="w-5 h-5" />
              </button>
              <button 
                onClick={logout}
                className="p-2 bg-red-50 rounded-full text-red-500 hover:bg-red-100 transition-all"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 py-8">
        <V4Search />
      </main>

      <footer className="py-8 bg-white border-t border-slate-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-slate-400 text-sm italic">
            &copy; 2026 ICOAtlas Identifier Intelligence V4. Poháňané technológiou Identity Graph Engine.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default V4SearchPage;
