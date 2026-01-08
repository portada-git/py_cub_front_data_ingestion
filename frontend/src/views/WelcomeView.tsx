import React from "react";
import { useNavigate } from "react-router-dom";
import { Database, ShieldCheck, Zap, BarChart3, Loader2 } from "lucide-react";
import { useStore } from "../store/useStore";
import { GoogleLogin } from "@react-oauth/google";
import { jwtDecode } from "jwt-decode";

const WelcomeView: React.FC = () => {
  const navigate = useNavigate();
  const { setAuthStatus, setUser, authStatus } = useStore();

  const handleSuccess = (credentialResponse: any) => {
    setAuthStatus("loading");
    try {
      const decoded: any = jwtDecode(credentialResponse.credential);

      setUser({
        name: decoded.name,
        email: decoded.email,
        picture: decoded.picture,
      });

      setAuthStatus("authenticated");
      navigate("/ingestion");
    } catch (error) {
      console.error("Error decoding Google token:", error);
      setAuthStatus("unauthenticated");
    }
  };

  const handleError = () => {
    console.error("Login Failed");
    setAuthStatus("unauthenticated");
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

        <div className="pt-8 flex flex-col items-center justify-center">
          {authStatus === "loading" ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
              <p className="text-slate-400 animate-pulse">Autenticando...</p>
            </div>
          ) : (
            <div className="scale-110">
              <GoogleLogin
                onSuccess={handleSuccess}
                onError={handleError}
                useOneTap
                theme="filled_blue"
                shape="pill"
              />
            </div>
          )}
          <p className="mt-8 text-slate-500 text-sm">
            Acceso seguro mediante OAuth 2.0. No almacenamos tus credenciales.
          </p>
        </div>
      </div>
    </div>
  );
};

export default WelcomeView;
