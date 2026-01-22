/**
 * Daily Entries Analysis View
 * Implements Requirements 10.1-10.7: Daily entry count analysis
 */

import React, { useState } from 'react';
import { 
  BarChart3, 
  Search, 
  AlertCircle, 
  Loader2, 
  Calendar,
  Database,
  TrendingUp,
  Download
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import { DailyEntriesRequest } from '../types';

interface DailyEntry {
  date: string;
  edition: string;
  entryCount: number;
  publication: string;
}

const DailyEntriesView: React.FC = () => {
  const [publication, setPublication] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<DailyEntry[]>([]);

  const publications = [
    { value: 'db', label: 'Diario de Barcelona' },
    { value: 'dm', label: 'Diario Mercantil' },
    { value: 'sm', label: 'Semanario Mercantil' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!publication) {
      return;
    }

    setIsLoading(true);
    
    const request: DailyEntriesRequest = {
      publication,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    };

    const result = await withErrorHandling(async () => {
      return await apiService.getDailyEntries(request);
    });

    if (result) {
      // Transform the API response to match our interface
      const transformedResults: DailyEntry[] = result.daily_entries?.map((entry: any) => ({
        date: entry.publication_date || entry.date,
        edition: entry.publication_edition || entry.edition,
        entryCount: entry.entry_count || entry.count,
        publication: entry.publication || publication
      })) || [];
      
      setResults(transformedResults);
    }
    
    setIsLoading(false);
  };

  const handleExportResults = () => {
    if (results.length === 0) return;

    const csvContent = [
      'Fecha,Edición,Publicación,Cantidad de Entradas',
      ...results.map(entry => 
        `${entry.date},${entry.edition},${entry.publication},${entry.entryCount}`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `daily_entries_${publication}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const getTotalEntries = () => {
    return results.reduce((sum, entry) => sum + entry.entryCount, 0);
  };

  const getAverageEntries = () => {
    if (results.length === 0) return 0;
    return Math.round(getTotalEntries() / results.length);
  };

  const getDateRange = () => {
    if (results.length === 0) return null;
    const dates = results.map(entry => new Date(entry.date)).sort((a, b) => a.getTime() - b.getTime());
    return {
      start: dates[0],
      end: dates[dates.length - 1]
    };
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header and Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-indigo-500/10 rounded-xl">
            <BarChart3 className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">
              Cantidad de Entradas Diarias
            </h1>
            <p className="text-slate-400">
              Analiza el volumen de entradas por día y edición para una publicación específica
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Publication Selection (Required) */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Publicación <span className="text-red-400">*</span>
              </label>
              <select
                value={publication}
                onChange={(e) => setPublication(e.target.value)}
                required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Seleccionar publicación"
              >
                <option value="">Selecciona una publicación</option>
                {publications.map((pub) => (
                  <option key={pub.value} value={pub.value}>
                    {pub.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Publicación requerida para el análisis
              </p>
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Fecha de inicio
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Fecha de inicio del análisis"
              />
              <p className="text-xs text-slate-500 mt-1">
                Opcional: desde la fecha más antigua si se omite
              </p>
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Fecha de fin
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Fecha de fin del análisis"
              />
              <p className="text-xs text-slate-500 mt-1">
                Opcional: hasta la fecha más reciente si se omite
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || !publication}
            className={clsx(
              "w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-medium transition-all",
              isLoading || !publication
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-indigo-600 text-white hover:bg-indigo-500"
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analizando entradas...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Analizar Entradas Diarias
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-6">
          {/* Summary Statistics */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Estadísticas del Análisis</h2>
              <button
                onClick={handleExportResults}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-500 transition-colors"
                aria-label="Exportar resultados a CSV"
              >
                <Download className="w-4 h-4" />
                Exportar CSV
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-indigo-400 mb-2">
                  {results.length}
                </div>
                <div className="text-slate-400">Días Analizados</div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">
                  {getTotalEntries().toLocaleString()}
                </div>
                <div className="text-slate-400">Total Entradas</div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">
                  {getAverageEntries().toLocaleString()}
                </div>
                <div className="text-slate-400">Promedio Diario</div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">
                  {Math.max(...results.map(r => r.entryCount)).toLocaleString()}
                </div>
                <div className="text-slate-400">Máximo Diario</div>
              </div>
            </div>

            {/* Date Range */}
            {getDateRange() && (
              <div className="mt-6 pt-6 border-t border-slate-800">
                <div className="flex items-center justify-center gap-4 text-sm text-slate-400">
                  <Calendar className="w-4 h-4" />
                  <span>
                    Período analizado: {getDateRange()!.start.toLocaleDateString()} - {getDateRange()!.end.toLocaleDateString()}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white">Detalle por Día y Edición</h3>
              <p className="text-slate-400 text-sm">
                Cantidad de entradas registradas por fecha y edición
              </p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-800/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Fecha
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Edición
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Publicación
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Cantidad de Entradas
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      % del Total
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {results
                    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                    .map((entry, index) => {
                      const percentage = ((entry.entryCount / getTotalEntries()) * 100).toFixed(1);
                      const isHighVolume = entry.entryCount > getAverageEntries() * 1.5;
                      
                      return (
                        <tr key={index} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4 text-slate-500" />
                              <span className="text-slate-300">
                                {new Date(entry.date).toLocaleDateString()}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                              {entry.edition}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Database className="w-4 h-4 text-slate-500" />
                              <span className="text-slate-300">{entry.publication}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {isHighVolume && (
                                <TrendingUp className="w-4 h-4 text-green-400" />
                              )}
                              <span className={clsx(
                                "font-mono text-lg",
                                isHighVolume ? "text-green-400" : "text-slate-300"
                              )}>
                                {entry.entryCount.toLocaleString()}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <span className="text-slate-400 text-sm">
                              {percentage}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {results.length === 0 && !isLoading && publication && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
          <BarChart3 className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">
            No se encontraron entradas
          </h3>
          <p className="text-slate-500">
            No hay datos de entradas para la publicación y período seleccionados.
          </p>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-indigo-900/10 border border-indigo-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-indigo-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-indigo-200 font-medium mb-2">
            Información sobre el análisis de entradas diarias:
          </p>
          <p>
            Este análisis utiliza la clase BoatFactIngestion de la librería PortAda para contar 
            las entradas diarias agrupadas por fecha y edición. Los datos se filtran por publicación 
            y opcionalmente por rango de fechas. Las entradas con volumen superior al 150% del promedio 
            se destacan con un indicador de tendencia.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DailyEntriesView;