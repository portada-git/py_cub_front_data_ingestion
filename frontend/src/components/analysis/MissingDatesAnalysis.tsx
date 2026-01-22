/**
 * Missing Dates Analysis component
 * Implements file upload for date lists and date range picker
 */

import React, { useState } from 'react';
import { Calendar, Upload, Search, FileText, Download } from 'lucide-react';
import { useNotificationStore } from '../../store/useStore';
import { apiService } from '../../services/api';
import DataTable, { TableColumn } from '../results/DataTable';
import DateRangePicker from '../forms/DateRangePicker';
import LoadingSpinner from '../LoadingSpinner';
import { MissingDateEntry } from '../../types';

interface LocalMissingDatesResponse {
  missing_dates: (MissingDateEntry & Record<string, unknown>)[];
  total_missing: number;
  date_range?: {
    start_date: string;
    end_date: string;
  };
}

const MissingDatesAnalysis: React.FC = () => {
  const { addNotification } = useNotificationStore();
  const [analysisType, setAnalysisType] = useState<'file' | 'range'>('file');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<LocalMissingDatesResponse | null>(null);
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  
  // Date range state
  const [dateRange, setDateRange] = useState({
    startDate: '',
    endDate: '',
    publication: ''
  });

  const handleFileSelect = (file: File) => {
    const validTypes = ['application/json', 'text/yaml', 'application/x-yaml', 'text/plain'];
    const validExtensions = ['.json', '.yaml', '.yml', '.txt'];
    
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!hasValidType && !hasValidExtension) {
      addNotification({
        type: 'error',
        title: 'Formato de archivo no válido',
        message: 'Por favor selecciona un archivo JSON, YAML o TXT'
      });
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileAnalysis = async () => {
    if (!selectedFile) {
      addNotification({
        type: 'error',
        title: 'Archivo requerido',
        message: 'Por favor selecciona un archivo con las fechas a analizar'
      });
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiService.analyzeMissingDatesFile(selectedFile);
      setResults(response as any);
      
      addNotification({
        type: 'success',
        title: 'Análisis completado',
        message: `Se encontraron ${response.total_missing} fechas faltantes`
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error en el análisis',
        message: error instanceof Error ? error.message : 'Error desconocido'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRangeAnalysis = async () => {
    if (!dateRange.startDate || !dateRange.endDate) {
      addNotification({
        type: 'error',
        title: 'Fechas requeridas',
        message: 'Por favor selecciona un rango de fechas válido'
      });
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiService.analyzeMissingDatesRange({
        start_date: dateRange.startDate,
        end_date: dateRange.endDate,
        publication: dateRange.publication || undefined
      });
      setResults(response as any);
      
      addNotification({
        type: 'success',
        title: 'Análisis completado',
        message: `Se encontraron ${response.total_missing} fechas faltantes`
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error en el análisis',
        message: error instanceof Error ? error.message : 'Error desconocido'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = () => {
    if (!results) return;
    
    const csvContent = [
      'Fecha,Edición,Duración',
      ...results.missing_dates.map(item => 
        `${item.date},${item.edition},${item.gap_duration || 'No especificado'}`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fechas_faltantes_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const columns: TableColumn[] = [
    {
      key: 'date',
      label: 'Fecha',
      sortable: true,
      filterable: true,
      format: (value: unknown) => {
        if (typeof value === 'string') {
          return new Date(value).toLocaleDateString('es-ES');
        }
        return String(value);
      }
    },
    {
      key: 'edition',
      label: 'Edición',
      sortable: true,
      filterable: true,
      format: (value: unknown) => String(value).toUpperCase()
    },
    {
      key: 'gap_duration',
      label: 'Duración',
      filterable: true,
      render: (value: unknown) => (
        <span className="text-sm text-gray-600">
          {String(value || 'No especificado')}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Análisis de Fechas Faltantes</h1>
        <p className="mt-1 text-sm text-gray-600">
          Buscar fechas y ediciones faltantes en los datos
        </p>
      </div>

      {/* Analysis Type Selector */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Tipo de Análisis</h2>
        <div className="flex space-x-4">
          <button
            onClick={() => setAnalysisType('file')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              analysisType === 'file'
                ? 'bg-primary-100 text-primary-700 border border-primary-200'
                : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
            }`}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Subir archivo de fechas
          </button>
          <button
            onClick={() => setAnalysisType('range')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              analysisType === 'range'
                ? 'bg-primary-100 text-primary-700 border border-primary-200'
                : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
            }`}
          >
            <Calendar className="w-4 h-4 inline mr-2" />
            Rango de fechas
          </button>
        </div>
      </div>

      {/* File Upload Analysis */}
      {analysisType === 'file' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Subir Archivo de Fechas</h2>
          <p className="text-sm text-gray-600 mb-4">
            Sube un archivo JSON, YAML o TXT con las fechas que quieres verificar
          </p>
          
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center ${
              dragActive
                ? 'border-primary-400 bg-primary-50'
                : selectedFile
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onDragEnter={() => setDragActive(true)}
            onDragLeave={() => setDragActive(false)}
          >
            {selectedFile ? (
              <div>
                <FileText className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="mt-2 text-sm text-red-600 hover:text-red-800"
                >
                  Remover archivo
                </button>
              </div>
            ) : (
              <div>
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-sm text-gray-600 mb-2">
                  Arrastra un archivo aquí o haz clic para seleccionar
                </p>
                <p className="text-xs text-gray-500">
                  Formatos soportados: JSON, YAML, TXT
                </p>
              </div>
            )}
            
            <input
              type="file"
              className="hidden"
              accept=".json,.yaml,.yml,.txt"
              onChange={handleFileInputChange}
              id="file-upload"
            />
            {!selectedFile && (
              <label
                htmlFor="file-upload"
                className="mt-4 inline-block btn btn-secondary cursor-pointer"
              >
                Seleccionar archivo
              </label>
            )}
          </div>
          
          {selectedFile && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleFileAnalysis}
                disabled={isLoading}
                className="btn btn-primary"
              >
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Analizando...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Analizar fechas
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Date Range Analysis */}
      {analysisType === 'range' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Análisis por Rango de Fechas</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <DateRangePicker
              value={{ startDate: dateRange.startDate, endDate: dateRange.endDate }}
              onChange={(range) => {
                setDateRange(prev => ({ 
                  ...prev, 
                  startDate: range?.startDate || '', 
                  endDate: range?.endDate || '' 
                }));
              }}
              label="Rango de Fechas"
            />
            
            <div>
              <label htmlFor="publication" className="block text-sm font-medium text-gray-700 mb-2">
                Publicación (opcional)
              </label>
              <select
                id="publication"
                value={dateRange.publication}
                onChange={(e) => setDateRange(prev => ({ ...prev, publication: e.target.value }))}
                className="input"
              >
                <option value="">Todas las publicaciones</option>
                <option value="db">Diario de Barcelona (DB)</option>
                <option value="dm">Diario de Madrid (DM)</option>
                <option value="sm">Semanario de Málaga (SM)</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={handleRangeAnalysis}
                disabled={isLoading || !dateRange.startDate || !dateRange.endDate}
                className="btn btn-primary w-full"
              >
                {isLoading ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Analizando...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Analizar rango
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-medium text-gray-900">
                  Resultados del Análisis
                </h2>
                <p className="text-sm text-gray-600">
                  {results.total_missing} fechas faltantes encontradas
                  {results.date_range && (
                    <span className="ml-2">
                      (del {new Date(results.date_range.start_date).toLocaleDateString('es-ES')} 
                      al {new Date(results.date_range.end_date).toLocaleDateString('es-ES')})
                    </span>
                  )}
                </p>
              </div>
              
              {results.missing_dates.length > 0 && (
                <button
                  onClick={handleExport}
                  className="btn btn-secondary"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Exportar CSV
                </button>
              )}
            </div>
            
            <DataTable
              columns={columns}
              data={results.missing_dates}
              loading={isLoading}
              emptyMessage="No se encontraron fechas faltantes"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default MissingDatesAnalysis;