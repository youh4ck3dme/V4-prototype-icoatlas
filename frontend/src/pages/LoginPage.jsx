import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Link, useNavigate } from "react-router-dom";
import { FaFingerprint, FaLock } from "react-icons/fa";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/profile");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pt-20 flex items-center justify-center p-4">
      <div className="glass-card max-w-md w-full p-8 relative overflow-hidden">
        {/* Decorative Grid */}
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <FaFingerprint size={100} className="text-white" />
        </div>

        <h2 className="text-3xl font-bold mb-6 text-white text-center tracking-tight">
          Vstup do systému
        </h2>

        {error && (
          <div className="bg-red-500/20 border border-red-500/50 text-red-200 p-3 rounded mb-4 text-sm backdrop-blur-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-1">
              Email
            </label>
            <input
              type="email"
              required
              className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all outline-none"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-slate-300 text-sm font-medium mb-1">
              Heslo
            </label>
            <input
              type="password"
              required
              className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all outline-none"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-sky-600 to-blue-700 hover:from-sky-500 hover:to-blue-600 text-white font-medium py-3 rounded-lg transition-all shadow-lg hover:shadow-sky-500/25 flex items-center justify-center gap-2 group"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <FaLock className="group-hover:scale-110 transition-transform" />
                Prihlásiť sa
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-slate-400 text-sm">
          Nemáte účet?{" "}
          <Link
            to="/register"
            className="text-sky-400 hover:text-sky-300 hover:underline"
          >
            Vytvorte si ho zadarmo
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
