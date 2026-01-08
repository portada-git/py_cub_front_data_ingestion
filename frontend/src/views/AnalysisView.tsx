import React, { useState } from "react";
import {
  BarChart3,
  Users,
  AlertTriangle,
  Calendar,
  Search,
  Link2,
  Database,
  Filter,
  ArrowUpRight,
} from "lucide-react";
import { useStore } from "../store/useStore";

const AnalysisView: React.FC = () => {
  const { analysisResult } = useStore();
  const [searchTerm, setSearchTerm] = useState("");

  if (!analysisResult) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center text-center space-y-4">
        <div className="p-6 bg-slate-900 rounded-full border border-slate-800">
          <BarChart3 className="w-12 h-12 text-slate-600" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">
            Sin datos para analizar
          </h3>
          <p className="text-slate-400 max-w-xs mx-auto">
            Primero debes cargar y procesar archivos en la sección de "Carga de
            Datos".
          </p>
        </div>
      </div>
    );
  }

  const filteredMetadata = analysisResult.metadata.filter(
    (item) =>
      item.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.value.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 pb-12">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Database className="w-16 h-16 text-blue-500" />
          </div>
          <p className="text-slate-400 text-sm font-medium mb-1">
            Total Registros
          </p>
          <h4 className="text-3xl font-bold text-white">
            {analysisResult.metrics.totalRecords.toLocaleString()}
          </h4>
          <div className="mt-4 flex items-center gap-2 text-xs text-emerald-400">
            <ArrowUpRight className="w-4 h-4" />
            <span>+12% vs anterior</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Users className="w-16 h-16 text-indigo-500" />
          </div>
          <p className="text-slate-400 text-sm font-medium mb-1">
            Entidades Detectadas
          </p>
          <h4 className="text-3xl font-bold text-white">
            {analysisResult.metrics.detectedEntities}
          </h4>
          <div className="mt-4 flex items-center gap-2 text-xs text-indigo-400">
            <Link2 className="w-4 h-4" />
            <span>Vinculadas al YAML</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <AlertTriangle className="w-16 h-16 text-amber-500" />
          </div>
          <p className="text-slate-400 text-sm font-medium mb-1">
            Errores / Gaps
          </p>
          <h4 className="text-3xl font-bold text-white">
            {analysisResult.metrics.errors}
          </h4>
          <div className="mt-4 flex items-center gap-2 text-xs text-amber-400">
            <AlertTriangle className="w-4 h-4" />
            <span>Requiere atención</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Missing Dates Section */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-blue-400" />
              <h3 className="font-bold text-white">Fechas Faltantes (Gaps)</h3>
            </div>
            <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded border border-blue-500/20">
              Proactivo
            </span>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analysisResult.missingDates.map((gap, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 font-mono text-xs">
                      {gap.date.split("-")[2]}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {gap.date}
                      </p>
                      <p className="text-xs text-slate-500">
                        Salto detectado en la serie
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-amber-400">
                      -{gap.gap}
                    </p>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                      Duración
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Known Entities Section */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-white">Entidades Vinculadas</h3>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 gap-4">
              {analysisResult.knownEntities.map((entity) => (
                <div
                  key={entity.id}
                  className="p-4 bg-slate-800/30 border border-slate-800 rounded-xl hover:border-indigo-500/30 transition-colors"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        {entity.name}
                      </h4>
                      <span className="text-[10px] bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded uppercase font-semibold">
                        {entity.type}
                      </span>
                    </div>
                    <Link2 className="w-4 h-4 text-slate-600" />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {entity.linkedTo.map((link, i) => (
                      <span
                        key={i}
                        className="text-[10px] text-slate-400 bg-slate-900 px-2 py-1 rounded-md border border-slate-800"
                      >
                        {link}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Metadata Search Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-white">Buscador de Metadatos</h3>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Filtrar por clave o valor..."
              className="bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 w-full md:w-64"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800/50">
                <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Clave
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Valor
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Origen
                </th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredMetadata.map((item) => (
                <tr
                  key={item.id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4 text-sm font-mono text-blue-400">
                    {item.key}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {item.value}
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-1 rounded border border-slate-700">
                      {item.source}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-slate-500 hover:text-white transition-colors">
                      <Filter className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredMetadata.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-6 py-12 text-center text-slate-500 text-sm"
                  >
                    No se encontraron metadatos que coincidan con la búsqueda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalysisView;
