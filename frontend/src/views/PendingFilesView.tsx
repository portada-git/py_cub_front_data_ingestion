/**
 * Pending Files Analysis View
 * Implements Requirements 5.1-5.5: Query pending ingestion files
 */

import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  AlertCircle, 
  Loader2, 
  Clock,
  User,
  Database,
  RefreshCw
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import { PendingFilesResponse } from '../types';

const PendingFilesView: React.FC = () => {
  const [publication, setPublication] = useState('');
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<PendingFilesResponse | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const publications = [
    { value: 'db', label: 'Diario de Barcelona' },
    { value: 'dm', label: 'Diario Mercantil' },
    { value: 'sm', label: 'Semanario Mercantil' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetchPendingFiles();
  };

  const fetchPendingFiles = async () => {
    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      return await apiService.getPendingFiles(
        publication || undefined,
        username || undefined
      );
    });

    if (result) {
      setResults(result);
      setLastUpdated(new Date());
    }
    
    setIsLoading(false);
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (results) {
        fetchPendingFiles();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [results, publication, username]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header and Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-orange-500/10 rounded-xl">
            <FileText className="w-8 h-8 text-orange-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">
              Ficheros de Ingestión Pendientes
            </h1>
            <p className="text-slate-400">
              Consulta cuántos ficheros están pendientes de procesar en la cola de ingestión
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Publication Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Publicación
              </label>
              <select
                value={publication}
                onChange={(e) => setPublication(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Filtrar por publicación"
              >
                <option value="">Todas las publicaciones</option>
                {publications.map((pub) => (
                  <option key={pub.value} value={pub.value}>
                    {pub.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-slate-500 mt-1">
                Filtra por publicación específica
              </p>
            </div>

            {/* Username Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Usuario
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nombre de usuario"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Filtrar por usuario"
              />
              <p className="text-xs text-slate-500 mt-1">
                Filtra por usuario que subió los ficheros
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className={clsx(
                "flex-1 flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-medium transition-all",
                isLoading
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-orange-600 text-white hover:bg-orange-500"
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Consultando...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Consultar Ficheros Pendientes
                </>
              )}
            </button>
            
            {results && (
              <button
                type="button"
                onClick={fetchPendingFiles}
                disabled={isLoading}
                className="px-4 py-3 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
                aria-label="Actualizar resultados"
              >
                <RefreshCw className={clsx("w-5 h-5", isLoading && "animate-spin")} />
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="card-dark">
            <div className="card-header-dark">
              <h2 className="text-xl font-bold text-white">Resumen de Ficheros Pendientes</h2>
              {lastUpdated && (
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Clock className="w-4 h-4" />
                  Actualizado: {lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="stat-card stat-card-warning">
                <div className="stat-number stat-number-warning">
                  {results.total_files}
                </div>
                <div className="stat-label text-slate-400">Ficheros Pendientes</div>
              </div>
              
              <div className="stat-card stat-card-info">
                <div className="stat-number stat-number-info">
                  {results.pending_files.reduce((acc, file) => acc + file.size, 0) > 0 
                    ? formatFileSize(results.pending_files.reduce((acc, file) => acc + file.size, 0))
                    : '0 B'
                  }
                </div>
                <div className="stat-label text-slate-400">Tamaño Total</div>
              </div>
              
              <div className="stat-card stat-card-success">
                <div className="stat-number stat-number-success">
                  {new Set(results.pending_files.map(f => f.publication)).size}
                </div>
                <div className="stat-label text-slate-400">Publicaciones</div>
              </div>
            </div>
          </div>

          {/* Files List */}
          {results.pending_files.length > 0 && (
            <div className="table-container table-dark">
              <div className="table-header-dark">
                <h3 className="text-lg font-bold text-white">Detalle de Ficheros</h3>
                <p className="text-slate-400 text-sm">
                  Lista de ficheros pendientes de procesamiento
                </p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-800/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Fichero
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Publicación
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Fecha Subida
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Tamaño
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {results.pending_files.map((file, index) => (
                      <tr key={index} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-slate-500" />
                            <span className="text-slate-300 font-mono text-sm">
                              {file.filename}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Database className="w-4 h-4 text-slate-500" />
                            <span className="text-slate-300">
                              {file.publication || 'N/A'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-slate-500" />
                            <span className="text-slate-300">
                              {file.username || 'N/A'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-slate-500" />
                            <span className="text-slate-300 text-sm">
                              {new Date(file.created_at).toLocaleString()}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-slate-300 font-mono text-sm">
                            {formatFileSize(file.size)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Empty State */}
          {results.total_files === 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
              <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-300 mb-2">
                No hay ficheros pendientes
              </h3>
              <p className="text-slate-500">
                {publication || username 
                  ? 'No se encontraron ficheros pendientes con los filtros aplicados.'
                  : 'Todos los ficheros han sido procesados correctamente.'
                }
              </p>
            </div>
          )}
        </div>
      )}

      {/* Info Card */}
      <div className="bg-orange-900/10 border border-orange-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-orange-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-orange-200 font-medium mb-2">
            Información sobre ficheros pendientes:
          </p>
          <p>
            Esta consulta muestra los ficheros que están en la carpeta de ingestión 
            esperando ser procesados. Los ficheros se actualizan automáticamente cada 30 segundos. 
            Puedes filtrar por publicación y/o usuario para obtener resultados más específicos.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingFilesView;