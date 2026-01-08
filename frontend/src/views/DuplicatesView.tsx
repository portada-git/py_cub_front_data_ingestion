import React, { useState } from "react";
import {
  Copy,
  Search,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  User,
  Calendar,
} from "lucide-react";
import { clsx } from "clsx";

interface DuplicateRecord {
  id: string;
  date: string;
  edition: string;
  publication: string;
  uploadedBy: string;
  duplicateIds: string[];
  duplicatesFilter: string;
}

interface DuplicateDetail {
  entryId: string;
  content: string;
  similarity: number;
}

const DuplicatesView: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedNewspaper, setSelectedNewspaper] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<DuplicateRecord[]>([]);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [duplicateDetails, setDuplicateDetails] = useState<DuplicateDetail[]>([]);

  const users = [
    { value: "admin", label: "Administrador" },
    { value: "user1", label: "Usuario 1" },
    { value: "user2", label: "Usuario 2" },
  ];

  const newspapers = [
    { value: "DB", label: "Diario de Barcelona" },
    { value: "DM", label: "Diario de Madrid" },
    { value: "SM", label: "Semanario de Málaga" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Simulación de llamada a la API
    setTimeout(() => {
      const mockResults: DuplicateRecord[] = [
        {
          id: "1",
          date: "1850-10-01",
          edition: "U",
          publication: "DB",
          uploadedBy: "admin",
          duplicateIds: ["dup_1", "dup_2"],
          duplicatesFilter: "date='1850-10-01' AND edition='U'",
        },
        {
          id: "2",
          date: "1850-10-03",
          edition: "M",
          publication: "DB",
          uploadedBy: "user1",
          duplicateIds: ["dup_3", "dup_4", "dup_5"],
          duplicatesFilter: "date='1850-10-03' AND edition='M'",
        },
      ];
      setResults(mockResults);
      setIsLoading(false);
    }, 2000);
  };

  const handleRowExpand = (recordId: string) => {
    if (expandedRow === recordId) {
      setExpandedRow(null);
      setDuplicateDetails([]);
    } else {
      setExpandedRow(recordId);
      // Simulación de carga de detalles
      const mockDetails: DuplicateDetail[] = [
        {
          entryId: "entry_1",
          content: "Contenido del registro duplicado 1...",
          similarity: 95.5,
        },
        {
          entryId: "entry_2", 
          content: "Contenido del registro duplicado 2...",
          similarity: 87.2,
        },
      ];
      setDuplicateDetails(mockDetails);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-amber-500/10 rounded-xl">
            <Copy className="w-8 h-8 text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Consulta de Duplicados</h1>
            <p className="text-slate-400">
              Identifica y analiza registros duplicados en las publicaciones
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* User Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Usuario responsable
              </label>
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="">Todos los usuarios</option>
                {users.map((user) => (
                  <option key={user.value} value={user.value}>
                    {user.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Newspaper Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Periódico
              </label>
              <select
                value={selectedNewspaper}
                onChange={(e) => setSelectedNewspaper(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="">Todas las publicaciones</option>
                {newspapers.map((newspaper) => (
                  <option key={newspaper.value} value={newspaper.value}>
                    {newspaper.label} ({newspaper.value})
                  </option>
                ))}
              </select>
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Fecha inicio
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Fecha final
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
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
                : "bg-amber-600 text-white hover:bg-amber-500"
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
                Buscar Duplicados
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800">
            <h2 className="text-xl font-bold text-white">Metadatos de Duplicados</h2>
            <p className="text-slate-400 text-sm">
              Se encontraron {results.length} registros con duplicados
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800/50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Fecha/Edición
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Publicación
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Duplicados
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {results.map((record) => (
                  <React.Fragment key={record.id}>
                    <tr className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-slate-500" />
                          <span className="text-slate-300 font-mono text-sm">
                            {record.date} - {record.edition}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-slate-300">{record.publication}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-slate-500" />
                          <span className="text-slate-300">{record.uploadedBy}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          {record.duplicateIds.length} duplicados
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleRowExpand(record.id)}
                          className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          {expandedRow === record.id ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          Ver detalles
                        </button>
                      </td>
                    </tr>
                    
                    {/* Expanded Details */}
                    {expandedRow === record.id && (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 bg-slate-800/20">
                          <div className="space-y-4">
                            <h4 className="text-sm font-medium text-slate-300">
                              Registros Duplicados:
                            </h4>
                            <div className="grid gap-3">
                              {duplicateDetails.map((detail) => (
                                <div
                                  key={detail.entryId}
                                  className="p-4 bg-slate-800/50 rounded-lg border border-slate-700/50"
                                >
                                  <div className="flex justify-between items-start mb-2">
                                    <span className="text-xs font-mono text-slate-400">
                                      ID: {detail.entryId}
                                    </span>
                                    <span className="text-xs text-amber-400">
                                      Similitud: {detail.similarity}%
                                    </span>
                                  </div>
                                  <p className="text-sm text-slate-300">
                                    {detail.content}
                                  </p>
                                </div>
                              ))}
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
      <div className="bg-amber-900/10 border border-amber-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-amber-200 font-medium mb-2">Información sobre duplicados:</p>
          <p>
            Esta consulta utiliza los logs "duplicates_log" y "duplicates_records" 
            para identificar registros duplicados. Los filtros se aplican sobre los 
            metadatos principales, y cada fila expandible muestra los registros 
            duplicados específicos encontrados.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DuplicatesView;