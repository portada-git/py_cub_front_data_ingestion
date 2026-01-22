/**
 * Pending Files Analysis component
 * Shows files waiting to be processed
 */

import React, { useState, useEffect } from 'react';
import { FileText, Search, RefreshCw } from 'lucide-react';
import { apiService } from '../../services/api';
import { useNotificationStore } from '../../store/useStore';
import LoadingSpinner from '../LoadingSpinner';

interface PendingFile {
  filename: string;
  size: number;
  created_at: string;
  publication: string;
  username: string;
}

const PendingFilesAnalysis: React.FC = () => {
  const { addNotification } = useNotificationStore();
  const [files, setFiles] = useState<PendingFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState({
    publication: '',
    username: '',
  });

  useEffect(() => {
    loadPendingFiles();
  }, []);

  const loadPendingFiles = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getPendingFiles(
        filters.publication || undefined,
        filters.username || undefined
      );
      setFiles(response.pending_files || []);
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error al cargar archivos',
        message: error instanceof Error ? error.message : 'Error desconocido'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const applyFilters = () => {
    loadPendingFiles();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Archivos Pendientes</h1>
        <p className="mt-1 text-sm text-gray-600">
          Archivos subidos que están esperando ser procesados
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Filtros</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="publication" className="block text-sm font-medium text-gray-700 mb-2">
              Publicación
            </label>
            <select
              id="publication"
              name="publication"
              value={filters.publication}
              onChange={handleFilterChange}
              className="input"
            >
              <option value="">Todas las publicaciones</option>
              <option value="db">Diario de Barcelona (DB)</option>
              <option value="dm">Diario de Madrid (DM)</option>
              <option value="sm">Semanario de Málaga (SM)</option>
            </select>
          </div>
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Usuario
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={filters.username}
              onChange={handleFilterChange}
              className="input"
              placeholder="Nombre de usuario"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={applyFilters}
              disabled={isLoading}
              className="btn btn-primary mr-2"
            >
              <Search className="w-4 h-4 mr-2" />
              Buscar
            </button>
            <button
              onClick={loadPendingFiles}
              disabled={isLoading}
              className="btn btn-secondary"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            Resultados ({files.length} archivos)
          </h2>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : files.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No hay archivos pendientes</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Archivo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tamaño
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
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {files.map((file, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-gray-400 mr-3" />
                        <span className="text-sm font-medium text-gray-900">
                          {file.filename}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {file.publication?.toUpperCase() || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {file.username}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(file.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PendingFilesAnalysis;