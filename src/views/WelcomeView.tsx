import React from "react";
import { useNavigate } from "react-router-dom";
import { Database, ShieldCheck, Zap, BarChart3 } from "lucide-react";
import { useStore } from "../store/useStore";

const WelcomeView: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthStatus, setUser } = useStore();

  const handleLogin = () => {
    // Simulación de login con Google
    setAuthStatus("loading");
    setTimeout(() => {
      setUser({
        name: "Admin PortAda",
        email: "admin@portada.ai",
        picture: "",
      });
      setAuthStatus("authenticated");
      navigate("/ingestion");
    }, 1000);
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
            La plataforma definitiva para la ingesta, validación y análisis de
            entidades en flujos de datos complejos.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 backdrop-blur-sm">
            <Database className="w-10 h-10 text-blue-500 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Ingesta Flexible
            </h3>
            <p className="text-slate-400 text-sm">
              Soporte nativo para JSON y YAML con validación estructural
              inmediata.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 backdrop-blur-sm">
            <ShieldCheck className="w-10 h-10 text-indigo-500 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Validación Zod
            </h3>
            <p className="text-slate-400 text-sm">
              Esquemas estrictos que garantizan la integridad de tus datos antes
              del procesamiento.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 backdrop-blur-sm">
            <BarChart3 className="w-10 h-10 text-blue-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Análisis Proactivo
            </h3>
            <p className="text-slate-400 text-sm">
              Detección automática de gaps temporales y vinculación de entidades
              conocidas.
            </p>
          </div>
        </div>

        <div className="pt-8">
          <button
            onClick={handleLogin}
            className="group relative inline-flex items-center gap-3 px-8 py-4 bg-white text-slate-950 font-bold rounded-xl hover:bg-blue-50 transition-all transform hover:scale-105 active:scale-95 shadow-xl shadow-blue-500/10"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 12-4.53z"
              />
            </svg>
            <span>Iniciar sesión con Google</span>
          </button>
          <p className="mt-6 text-slate-500 text-sm">
            Acceso seguro mediante OAuth 2.0. No almacenamos tus credenciales.
          </p>
        </div>
      </div>
    </div>
  );
};

export default WelcomeView;
