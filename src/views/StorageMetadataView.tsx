import React, { useState } from "react";
import {
  Archive,
  Search,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Database,
  Clock,
} from "lucide-react";
import { clsx } from "clsx";

interface StorageRecord {
  logId: string;
  tableName: string;
  process: string;
  timestamp: string;
  recordCount: number;
  stage: number;
}

interface FieldLineage {
  fieldName: string;
  operation: string;
  oldValue: string;
  newValue: string;
  timestamp: string;
}

const StorageMetadataView: React.FC = () => {
  const [tableName, setTableName] = useState("");
  const [processName, setProcessName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<StorageRecord[]>([]);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [fieldLineage, setFieldLineage] = useState<FieldLineage[]>([]);

  const tableNames = [
    { value: "ship_entries", label: "Ship Entries" },
    { value: "passenger_records", label: "Passenger Records" },
    { value: "cargo_manifest", label: "Cargo Manifest" },
  ];

  const processes = [
    { value: "data_ingestion", label: "Data Ingestion" },
    { value: "data_cleaning", label: "Data Cleaning" },
    { value: "data_transformation", label: "Data Transformation" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulación de llamada a la API
    setTimeout(() => {
      const mockResults: StorageRecord[] = [
        {
          logId: "log_001",
          tableName: tableName || "ship_entries",
          process: processName || "data_ingestion",
          timestamp: "2024-01-15T10:30:00Z",
          recordCount: 1250,
          stage: 0,
        },
        {
          logId: "log_002",
          tableName: tableName || "ship_entries",
          process: processName || "data_cleaning",
          timestamp: "2024-01-15T11:45:00Z",
          recordCount: 1248,
          stage: 0,
        },
      ];
      setResults(mockResults);
      setIsLoading(false);
    }, 2000);
  };

  const handleRowExpand = (logId: string) => {
    if (expandedRow === logId) {
      setExpandedRow(null);
      setFieldLineage([]);
    } else {
      setExpandedRow(logId);
      // Simulación de carga de field lineage
      const mockLineage: FieldLineage[] = [
        {
          fieldName: "ship_name",
          operation: "NORMALIZE",
          oldValue: "S.S. BRITANNIA",
          newValue: "SS Britannia",
          timestamp: "2024-01-15T10:31:15Z",
        },
        {
          fieldName: "departure_date",
          operation: "FORMAT",
          oldValue: "15/01/1850",
          newValue: "1850-01-15",
          timestamp: "2024-01-15T10:31:20Z",
        },
        {
          fieldName: "passenger_count",
          operation: "VALIDATE",
          oldValue: "null",
          newValue: "0",
          timestamp: "2024-01-15T10:31:25Z",
        },
      ];
      setFieldLineage(mockLineage);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-green-500/10 rounded-xl">
            <Archive className="w-8 h-8 text-green-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Metadatos de Almacenaje</h1>
            <p className="text-slate-400">
              Consulta información sobre el almacenamiento y transformaciones de datos
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Table Name Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Nombre de tabla
              </label>
              <select
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="">Todas las tablas</option>
                {tableNames.map((table) => (
                  <option key={table.value} value={table.value}>
                    {table.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Nombre con el que se conocen los datos
              </p>
            </div>

            {/* Process Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Proceso responsable
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
                Proceso responsable del almacenamiento
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
                : "bg-green-600 text-white hover:bg-green-500"
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
                Consultar Metadatos
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800">
            <h2 className="text-xl font-bold text-white">Metadatos de Almacenamiento</h2>
            <p className="text-slate-400 text-sm">
              Se encontraron {results.length} registros de almacenamiento (stage = 0)
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
                    Tabla
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Proceso
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Registros
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {results.map((record) => (
                  <React.Fragment key={record.logId}>
                    <tr className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <span className="text-slate-300 font-mono text-sm">
                          {record.logId}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4 text-slate-500" />
                          <span className="text-slate-300">{record.tableName}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-slate-300">{record.process}</span>
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
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                          {record.recordCount.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleRowExpand(record.logId)}
                          className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          {expandedRow === record.logId ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          Ver lineage
                        </button>
                      </td>
                    </tr>
                    
                    {/* Expanded Field Lineage */}
                    {expandedRow === record.logId && (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 bg-slate-800/20">
                          <div className="space-y-4">
                            <h4 className="text-sm font-medium text-slate-300">
                              Field Lineage - Cambios realizados:
                            </h4>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b border-slate-700">
                                    <th className="text-left py-2 text-slate-400">Campo</th>
                                    <th className="text-left py-2 text-slate-400">Operación</th>
                                    <th className="text-left py-2 text-slate-400">Valor Anterior</th>
                                    <th className="text-left py-2 text-slate-400">Valor Nuevo</th>
                                    <th className="text-left py-2 text-slate-400">Timestamp</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700/50">
                                  {fieldLineage.map((lineage, index) => (
                                    <tr key={index}>
                                      <td className="py-2 text-slate-300 font-mono">
                                        {lineage.fieldName}
                                      </td>
                                      <td className="py-2">
                                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                          {lineage.operation}
                                        </span>
                                      </td>
                                      <td className="py-2 text-slate-400 font-mono text-xs">
                                        {lineage.oldValue}
                                      </td>
                                      <td className="py-2 text-slate-300 font-mono text-xs">
                                        {lineage.newValue}
                                      </td>
                                      <td className="py-2 text-slate-500 text-xs">
                                        {new Date(lineage.timestamp).toLocaleString()}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-green-900/10 border border-green-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-green-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-green-200 font-medium mb-2">Información sobre metadatos de almacenaje:</p>
          <p>
            Esta consulta utiliza los logs "storage_log" y "field_lineage_log" para mostrar 
            información detallada sobre el almacenamiento de datos. Solo se muestran registros 
            con stage = 0. El field lineage muestra los cambios realizados en cada campo 
            durante las transformaciones.
          </p>
        </div>
      </div>
    </div>
  );
};

export default StorageMetadataView;