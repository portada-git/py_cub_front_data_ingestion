import React, { useState } from "react";
import {
  Settings,
  Search,
  AlertCircle,
  Loader2,
  Play,
  Clock,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { clsx } from "clsx";

interface ProcessRecord {
  logId: string;
  process: string;
  timestamp: string;
  duration: number;
  status: "success" | "error" | "running";
  recordsProcessed: number;
  stage: number;
  errorMessage?: string;
}

const ProcessMetadataView: React.FC = () => {
  const [processName, setProcessName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<ProcessRecord[]>([]);

  const processes = [
    { value: "data_extraction", label: "Data Extraction" },
    { value: "data_cleaning", label: "Data Cleaning" },
    { value: "data_transformation", label: "Data Transformation" },
    { value: "data_validation", label: "Data Validation" },
    { value: "entity_recognition", label: "Entity Recognition" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulación de llamada a la API
    setTimeout(() => {
      const mockResults: ProcessRecord[] = [
        {
          logId: "proc_001",
          process: processName || "data_extraction",
          timestamp: "2024-01-15T10:30:00Z",
          duration: 45.2,
          status: "success",
          recordsProcessed: 1250,
          stage: 0,
        },
        {
          logId: "proc_002",
          process: processName || "data_cleaning",
          timestamp: "2024-01-15T11:15:00Z",
          duration: 32.8,
          status: "success",
          recordsProcessed: 1248,
          stage: 0,
        },
        {
          logId: "proc_003",
          process: processName || "data_validation",
          timestamp: "2024-01-15T12:00:00Z",
          duration: 15.5,
          status: "error",
          recordsProcessed: 856,
          stage: 0,
          errorMessage: "Validation failed: Invalid date format in 2 records",
        },
        {
          logId: "proc_004",
          process: processName || "entity_recognition",
          timestamp: "2024-01-15T12:30:00Z",
          duration: 0,
          status: "running",
          recordsProcessed: 0,
          stage: 0,
        },
      ];
      setResults(mockResults);
      setIsLoading(false);
    }, 2000);
  };

  const getStatusIcon = (status: ProcessRecord["status"]) => {
    switch (status) {
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "error":
        return <XCircle className="w-4 h-4 text-red-400" />;
      case "running":
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusBadge = (status: ProcessRecord["status"]) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border";
    
    switch (status) {
      case "success":
        return `${baseClasses} bg-green-500/10 text-green-400 border-green-500/20`;
      case "error":
        return `${baseClasses} bg-red-500/10 text-red-400 border-red-500/20`;
      case "running":
        return `${baseClasses} bg-blue-500/10 text-blue-400 border-blue-500/20`;
      default:
        return `${baseClasses} bg-slate-500/10 text-slate-400 border-slate-500/20`;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds === 0) return "-";
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(1)}s`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-purple-500/10 rounded-xl">
            <Settings className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Metadatos de Procesos</h1>
            <p className="text-slate-400">
              Consulta información sobre procesos transformadores ejecutados
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="max-w-md">
            {/* Process Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Nombre del proceso
              </label>
              <select
                value={processName}
                onChange={(e) => setProcessName(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="">Todos los procesos</option>
                {processes.map((process) => (
                  <option key={process.value} value={process.value}>
                    {process.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Filtra por nombre específico del proceso transformador
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className={clsx(
              "w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-medium transition-all",
              isLoading
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-purple-600 text-white hover:bg-purple-500"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Procesando consulta...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Consultar Procesos
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800">
            <h2 className="text-xl font-bold text-white">Historial de Procesos</h2>
            <p className="text-slate-400 text-sm">
              Se encontraron {results.length} ejecuciones de procesos (stage = 0)
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Log ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Proceso
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Duración
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Registros
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {results.map((record) => (
                  <tr key={record.logId} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <span className="text-slate-300 font-mono text-sm">
                        {record.logId}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Play className="w-4 h-4 text-slate-500" />
                        <span className="text-slate-300">{record.process}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(record.status)}
                        <span className={getStatusBadge(record.status)}>
                          {record.status === "success" ? "Exitoso" :
                           record.status === "error" ? "Error" :
                           record.status === "running" ? "Ejecutando" : "Desconocido"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-slate-500" />
                        <span className="text-slate-300 text-sm">
                          {new Date(record.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-slate-300 font-mono text-sm">
                        {formatDuration(record.duration)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-slate-300">
                        {record.recordsProcessed.toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Error Details */}
      {results.some(r => r.status === "error") && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-400" />
            Detalles de Errores
          </h3>
          <div className="space-y-3">
            {results
              .filter(r => r.status === "error")
              .map((record) => (
                <div
                  key={record.logId}
                  className="p-4 bg-red-900/10 border border-red-800/30 rounded-lg"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium text-red-400">
                      {record.process}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {record.logId}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300">
                    {record.errorMessage || "Error desconocido"}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-purple-900/10 border border-purple-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-purple-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-purple-200 font-medium mb-2">Información sobre metadatos de procesos:</p>
          <p>
            Esta consulta utiliza el log "process_log" para mostrar información sobre 
            procesos transformadores ejecutados. Solo se muestran registros con stage = 0. 
            Los procesos pueden estar en estado exitoso, error o ejecutándose actualmente.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProcessMetadataView;