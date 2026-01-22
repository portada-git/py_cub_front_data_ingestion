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
  RefreshCw,
  Download,
  Eye
} from 'lucide-react';
import { clsx } from 'clsx';
import { useTranslation } from 'react-i18next';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import { PendingFilesResponse } from '../types';
import AdvancedFilters, { FilterState } from '../components/AdvancedFilters';
import DataExport from '../components/DataExport';

const PendingFilesView: React.FC = () => {
  const { t } = useTranslation();
  const [publication, setPublication] = useState('');
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<PendingFilesResponse | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filteredResults, setFilteredResults] = useState<PendingFilesResponse | null>(null);

  const publications = [
    { value: '', label: t('analysis.pendingFiles.allPublications') },
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
      setFilteredResults(result);
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
  }, [results]); // Removed fetchPendingFiles dependency to avoid infinite loop

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const handleAdvancedFilters = (filters: FilterState) => {
    if (!results) return;

    let filtered = [...results.pending_files];

    // Apply search term filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(file => 
        file.filename.toLowerCase().includes(searchLower) ||
        file.username.toLowerCase().includes(searchLower)
      );
    }

    // Apply publication filter
    if (filters.publications.length > 0) {
      filtered = filtered.filter(file => 
        filters.publications.includes(file.publication)
      );
    }

    // Apply user filter
    if (filters.users.length > 0) {
      filtered = filtered.filter(file => 
        filters.users.includes(file.username)
      );
    }

    // Apply date range filter
    if (filters.dateRange.start || filters.dateRange.end) {
      filtered = filtered.filter(file => {
        const fileDate = new Date(file.created_at);
        const startDate = filters.dateRange.start ? new Date(filters.dateRange.start) : null;
        const endDate = filters.dateRange.end ? new Date(filters.dateRange.end) : null;
        
        if (startDate && fileDate < startDate) return false;
        if (endDate && fileDate > endDate) return false;
        return true;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (filters.sortBy) {
        case 'name':
          aValue = a.filename;
          bValue = b.filename;
          break;
        case 'size':
          aValue = a.size;
          bValue = b.size;
          break;
        case 'date':
        default:
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
      }
      
      if (filters.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredResults({
      ...results,
      pending_files: filtered,
      total_files: filtered.length
    });
  };

  const handleResetFilters = () => {
    setFilteredResults(results);
  };

  const getFilterOptions = () => {
    if (!results) return {};

    const publications = Array.from(new Set(results.pending_files.map(f => f.publication)))
      .map(pub => ({
        value: pub,
        label: pub.toUpperCase(),
        count: results.pending_files.filter(f => f.publication === pub).length
      }));

    const users = Array.from(new Set(results.pending_files.map(f => f.username)))
      .map(user => ({
        value: user,
        label: user,
        count: results.pending_files.filter(f => f.username === user).length
      }));

    return { publications, users };
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const displayResults = filteredResults || results;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ficheros Pendientes de Ingestión</h1>
          <p className="mt-1 text-sm text-gray-600">
            Consulta qué ficheros están pendientes de procesar en la cola de ingestión
          </p>
        </div>
        <button
          onClick={fetchPendingFiles}
          disabled={isLoading}
          className="btn btn-secondary"
        >
          <RefreshCw className={clsx('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
          Actualizar
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="publication" className="block text-sm font-medium text-gray-700 mb-2">
                Publicación
              </label>
              <select
                id="publication"
                value={publication}
                onChange={(e) => setPublication(e.target.value)}
                className="input"
              >
                {publications.map((pub) => (
                  <option key={pub.value} value={pub.value}>
                    {pub.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Usuario
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nombre de usuario"
                className="input"
              />
            </div>
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Consultando...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Consultar Ficheros Pendientes
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Advanced Filters */}
          <AdvancedFilters
            isOpen={showAdvancedFilters}
            onToggle={() => setShowAdvancedFilters(!showAdvancedFilters)}
            onApply={handleAdvancedFilters}
            onReset={handleResetFilters}
            options={getFilterOptions()}
          />

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {displayResults?.total_files || 0}
              </div>
              <div className="text-gray-600">Ficheros Pendientes</div>
            </div>
            
            <div className="card text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {(displayResults?.pending_files.reduce((acc, file) => acc + file.size, 0) || 0) > 0 
                  ? formatFileSize(displayResults?.pending_files.reduce((acc, file) => acc + file.size, 0) || 0)
                  : '0 B'
                }
              </div>
              <div className="text-gray-600">Tamaño Total</div>
            </div>
            
            <div className="card text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {new Set(displayResults?.pending_files.map(f => f.publication) || []).size}
              </div>
              <div className="text-gray-600">Publicaciones</div>
            </div>
          </div>

          {/* Export Component */}
          {displayResults && displayResults.pending_files.length > 0 && (
            <DataExport
              data={displayResults.pending_files.map(file => ({
                filename: file.filename,
                publication: file.publication,
                username: file.username,
                created_at: formatDate(file.created_at),
                size: formatFileSize(file.size),
                size_bytes: file.size
              }))}
              filename="ficheros_pendientes"
              title="Exportar Lista de Ficheros"
            />
          )}

          {/* Files Table */}
          {displayResults && displayResults.pending_files.length > 0 ? (
            <div className="card p-0 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Lista de Ficheros ({displayResults.pending_files.length})
                </h3>
                {lastUpdated && (
                  <p className="text-sm text-gray-500 mt-1">
                    Última actualización: {formatDate(lastUpdated.toISOString())}
                  </p>
                )}
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Archivo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Publicación
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Usuario
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Fecha de Subida
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tamaño
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {displayResults.pending_files.map((file, index) => (
                      <tr key={index} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <FileText className="w-5 h-5 text-blue-500 mr-3" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {file.filename}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            <Database className="w-3 h-3 mr-1" />
                            {file.publication.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center text-sm text-gray-900">
                            <User className="w-4 h-4 text-gray-400 mr-2" />
                            {file.username}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center text-sm text-gray-500">
                            <Clock className="w-4 h-4 mr-2" />
                            {formatDate(file.created_at)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-mono text-gray-900">
                            {formatFileSize(file.size)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <button
                              className="text-blue-600 hover:text-blue-900 p-1 rounded"
                              title="Ver detalles"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              className="text-green-600 hover:text-green-900 p-1 rounded"
                              title="Descargar"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No hay ficheros pendientes
              </h3>
              <p className="text-gray-500">
                No se encontraron ficheros pendientes de procesar con los filtros aplicados.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Information */}
      <div className="card">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-blue-500 mr-3 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-1">Información importante:</p>
            <p>
              Esta vista muestra los ficheros que están en la cola de ingestión esperando ser procesados. 
              Los ficheros se actualizan automáticamente cada 30 segundos. Puedes filtrar por publicación 
              y usuario para encontrar ficheros específicos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PendingFilesView;