import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Link, useNavigate } from "react-router-dom";
import { FaUserPlus, FaShieldAlt } from "react-icons/fa";

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      return setError("Heslá sa nezhodujú");
    }

    if (formData.password.length < 8) {
      return setError("Heslo musí mať aspoň 8 znakov");
    }

    setLoading(true);
    try {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
      });
      // Auto-login the user immediately after successful registration
      await login(formData.email, formData.password);
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
        <div className="absolute top-0 left-0 p-4 opacity-5">
          <FaShieldAlt size={100} className="text-slate-900 transform -rotate-12" />
        </div>

        <h2 className="text-3xl font-bold mb-2 text-slate-900 text-center tracking-tight">
          Registrácia
        </h2>
        <p className="text-center text-slate-500 mb-6 text-sm">
          Získajte prístup k pokročilej analýze firiem
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-slate-700 text-sm font-medium mb-1">
              Meno a Priezvisko (Voliteľné)
            </label>
            <input
              type="text"
              name="full_name"
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-450 focus:ring-2 focus:ring-[#EE1C25] focus:border-transparent transition-all outline-none"
              placeholder="Ján Novák"
              value={formData.full_name}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="block text-slate-700 text-sm font-medium mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-450 focus:ring-2 focus:ring-[#EE1C25] focus:border-transparent transition-all outline-none"
              placeholder="name@company.com"
              value={formData.email}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="block text-slate-700 text-sm font-medium mb-1">
              Heslo
            </label>
            <input
              type="password"
              name="password"
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-450 focus:ring-2 focus:ring-[#EE1C25] focus:border-transparent transition-all outline-none"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="block text-slate-700 text-sm font-medium mb-1">
              Potvrdenie hesla
            </label>
            <input
              type="password"
              name="confirmPassword"
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-450 focus:ring-2 focus:ring-[#EE1C25] focus:border-transparent transition-all outline-none"
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={handleChange}
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#EE1C25] hover:bg-red-700 text-white font-medium py-3 rounded-lg transition-all shadow-sm flex items-center justify-center gap-2 group"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <FaUserPlus className="group-hover:scale-110 transition-transform" />
                  Vytvoriť účet
                </>
              )}
            </button>
          </div>
        </form>

        <div className="mt-6 text-center text-slate-500 text-sm">
          Už máte účet?{" "}
          <Link
            to="/login"
            className="text-[#EE1C25] hover:text-red-700 hover:underline font-semibold"
          >
            Prihláste sa
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
