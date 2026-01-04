import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  UploadCloud,
  LogOut,
  Database,
  BarChart3,
  User as UserIcon,
} from "lucide-react";
import { useStore } from "../store/useStore";
import { clsx } from "clsx";

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useStore();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const navItems = [
    { name: "Carga de Datos", path: "/ingestion", icon: UploadCloud },
    { name: "Análisis", path: "/analysis", icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Database className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            PortAda
          </h1>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                location.pathname === item.path
                  ? "bg-blue-600/10 text-blue-400 border border-blue-600/20"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              )}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            {user?.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="w-8 h-8 rounded-full"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-slate-400" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.name || "Usuario"}
              </p>
              <p className="text-xs text-slate-500 truncate">
                {user?.email || "usuario@ejemplo.com"}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-red-900/10 hover:text-red-400 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm flex items-center justify-between px-8">
          <h2 className="text-lg font-semibold text-white">
            {navItems.find((i) => i.path === location.pathname)?.name ||
              "Dashboard"}
          </h2>
          <div className="flex items-center gap-4">
            <div className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded border border-slate-700">
              v1.0.0-beta
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-8">{children}</div>
      </main>
    </div>
  );
};

export default MainLayout;
