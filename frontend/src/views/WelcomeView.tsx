import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Database, ShieldCheck, Zap, BarChart3, User, LogIn } from "lucide-react";
import { useStore } from "../store/useStore";

const WelcomeView: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthStatus, setUser } = useStore();
  const [username, setUsername] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (username.trim()) {
      setUser({
        name: username.trim(),
        email: `${username.trim()}@portada.local`,
        picture: null,
      });

      setAuthStatus("authenticated");
      navigate("/ingestion");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px]"></div>
      </div>

      <div className="max-w-4xl w-full text-center space-y-12">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-4">
            <Zap className="w-4 h-4" />
            <span>Curación de Datos Inteligente</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight">
            Proyecto{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">
              PortAda
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Plataforma para la ingesta, validación y análisis de entidades en
            flujos de datos complejos.
          </p>
        </div>

        {/* Simple Username Login */}
        <div className="pt-8 flex flex-col items-center justify-center">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 w-full max-w-md">
            <div className="flex items-center justify-center mb-6">
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <User className="w-8 h-8 text-blue-400" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-white mb-2">Identificación</h2>
            <p className="text-slate-400 text-sm mb-6">
              Ingresa tu nombre de usuario para continuar
            </p>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                  Nombre de Usuario
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Ej: juan.perez"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  required
                  autoFocus
                />
              </div>

              <button
                type="submit"
                disabled={!username.trim()}
                className="w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-medium transition-all bg-blue-600 text-white hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed"
              >
                <LogIn className="w-5 h-5" />
                Ingresar
              </button>
            </form>
          </div>

          <p className="mt-8 text-slate-500 text-sm">
            Sistema de identificación simple para registro de actividades
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <Database className="w-10 h-10 text-blue-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Ingesta Robusta
            </h3>
            <p className="text-slate-400 text-sm">
              Procesamiento asíncrono de datos con validación automática
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <ShieldCheck className="w-10 h-10 text-indigo-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Validación Inteligente
            </h3>
            <p className="text-slate-400 text-sm">
              Detección de duplicados y análisis de calidad de datos
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <BarChart3 className="w-10 h-10 text-purple-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Análisis Avanzado
            </h3>
            <p className="text-slate-400 text-sm">
              Metadatos, linaje de datos y trazabilidad completa
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeView;
