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
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-slate-50 pt-20 flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 shadow-lg rounded-2xl max-w-md w-full p-8 relative overflow-hidden">
        {/* Decorative Grid */}
        <div className="absolute top-0 right-0 p-4 opacity-5">
          <FaFingerprint size={100} className="text-slate-900" />
        </div>

        <h2 className="text-3xl font-bold mb-6 text-slate-900 text-center tracking-tight">
          Vstup do systému
        </h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-slate-700 text-sm font-medium mb-1">
              Email
            </label>
            <input
              type="email"
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-450 focus:ring-2 focus:ring-[#0B4EA2] focus:border-transparent transition-all outline-none"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-slate-700 text-sm font-medium mb-1">
              Heslo
            </label>
            <input
              type="password"
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-450 focus:ring-2 focus:ring-[#0B4EA2] focus:border-transparent transition-all outline-none"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#0B4EA2] hover:bg-blue-800 text-white font-medium py-3 rounded-lg transition-all shadow-sm flex items-center justify-center gap-2 group"
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

        <div className="mt-6 text-center text-slate-500 text-sm">
          Nemáte účet?{" "}
          <Link
            to="/register"
            className="text-[#0B4EA2] hover:text-blue-800 hover:underline font-semibold"
          >
            Vytvorte si ho zadarmo
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
