import React, { useState } from "react";
import {
  Calendar,
  Upload,
  Search,
  AlertCircle,
  FileText,
  Loader2,
} from "lucide-react";
import { clsx } from "clsx";

type QueryMode = "file" | "date_range";

const MissingDatesView: React.FC = () => {
  const [selectedNewspaper, setSelectedNewspaper] = useState("");
  const [queryMode, setQueryMode] = useState<QueryMode>("date_range");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<string[]>([]);

  const newspapers = [
    { value: "DB", label: "Diario de Barcelona" },
    { value: "DM", label: "Diario de Madrid" },
    { value: "SM", label: "Semanario de Málaga" },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNewspaper) return;

    setIsLoading(true);
    
    // Simulación de llamada a la API
    setTimeout(() => {
      const mockResults = [
        "1850-10-01 - Edición U",
        "1850-10-03 - Edición M",
        "1850-10-05 - Edición T",
        "1850-10-07 - Edición U",
        "1850-10-10 - Edición M",
      ];
      setResults(mockResults);
      setIsLoading(false);
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-blue-500/10 rounded-xl">
            <Calendar className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Consulta de Fechas Faltantes</h1>
            <p className="text-slate-400">
              Identifica fechas y ediciones faltantes en las publicaciones
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Newspaper Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Periódico a consultar *
            </label>
            <select
              value={selectedNewspaper}
              onChange={(e) => setSelectedNewspaper(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              required
            >
              <option value="">Selecciona un periódico</option>
              {newspapers.map((newspaper) => (
                <option key={newspaper.value} value={newspaper.value}>
                  {newspaper.label} ({newspaper.value})
                </option>
              ))}
            </select>
          </div>

          {/* Query Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Método de consulta
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setQueryMode("date_range")}
                className={clsx(
                  "p-4 rounded-lg border-2 transition-all text-left",
                  queryMode === "date_range"
                    ? "border-blue-500 bg-blue-500/10 text-blue-400"
                    : "border-slate-700 bg-slate-800/50 text-slate-300 hover:border-slate-600"
                )}
              >
                <Calendar className="w-5 h-5 mb-2" />
                <h3 className="font-medium mb-1">Rango de Fechas</h3>
                <p className="text-sm opacity-75">
                  Especifica fecha de inicio y final
                </p>
              </button>
              
              <button
                type="button"
                onClick={() => setQueryMode("file")}
                className={clsx(
                  "p-4 rounded-lg border-2 transition-all text-left",
                  queryMode === "file"
                    ? "border-blue-500 bg-blue-500/10 text-blue-400"
                    : "border-slate-700 bg-slate-800/50 text-slate-300 hover:border-slate-600"
                )}
              >
                <FileText className="w-5 h-5 mb-2" />
                <h3 className="font-medium mb-1">Archivo de Lista</h3>
                <p className="text-sm opacity-75">
                  Sube un archivo YAML, JSON o lista
                </p>
              </button>
            </div>
          </div>

          {/* Date Range Inputs */}
          {queryMode === "date_range" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Fecha de inicio (YYYY-MM-DD)
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Opcional - deja en blanco para buscar desde el inicio
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Fecha final (YYYY-MM-DD)
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Opcional - deja en blanco para buscar hasta el final
                </p>
              </div>
            </div>
          )}

          {/* File Upload */}
          {queryMode === "file" && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Archivo de fechas y ediciones
              </label>
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-700 rounded-lg cursor-pointer bg-slate-800/50 hover:border-slate-600 transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-2 text-slate-500" />
                  <p className="mb-2 text-sm text-slate-300">
                    <span className="font-semibold">Click para subir</span> archivo YAML, JSON o lista
                  </p>
                  <p className="text-xs text-slate-500">
                    Formatos: .yaml, .yml, .json, .txt
                  </p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  accept=".yaml,.yml,.json,.txt"
                  onChange={handleFileChange}
                />
              </label>
              {file && (
                <p className="text-sm text-slate-300 mt-2">
                  Archivo seleccionado: {file.name}
                </p>
              )}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!selectedNewspaper || isLoading || (queryMode === "file" && !file)}
            className={clsx(
              "w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-medium transition-all",
              !selectedNewspaper || isLoading || (queryMode === "file" && !file)
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-500"
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
                Ejecutar Consulta
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800">
            <h2 className="text-xl font-bold text-white">Fechas y Ediciones Faltantes</h2>
            <p className="text-slate-400 text-sm">
              Se encontraron {results.length} fechas faltantes
            </p>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            <div className="p-6 space-y-2">
              {results.map((result, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50"
                >
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span className="text-slate-300 font-mono text-sm">{result}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-blue-900/10 border border-blue-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-blue-200 font-medium mb-2">Formatos de archivo soportados:</p>
          <div className="space-y-1">
            <p><strong>YAML:</strong> 1850-10-01: [U] / 1850-10-02: [M, T]</p>
            <p><strong>JSON:</strong> {`[{"1850-10-01":["U"]}, {"1850-10-02":["M","T"]}]`}</p>
            <p><strong>Lista:</strong> Una fecha por línea (1850-10-01)</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissingDatesView;