/**
 * Duplicates Analysis component
 * Implements master table for duplicates metadata and detail view for duplicate records
 */

import React, { useState } from 'react';
import { Copy, Search, Download, Filter } from 'lucide-react';
import { useNotificationStore } from '../../store/useStore';
import { apiService } from '../../services/api';
import MasterDetailView from '../results/MasterDetailView';
import DataTable, { TableColumn } from '../results/DataTable';
import DateRangePicker from '../forms/DateRangePicker';
import PublicationSelector from '../PublicationSelector';
import LoadingSpinner from '../LoadingSpinner';

interface DuplicateMetadata extends Record<string, unknown> {
  log_id: string;
  user: string;
  publication: string;
  process_date: string;
  duplicates_count: number;
  duplicates_filter: string;
  created_at: string;
}

interface DuplicateRecord extends Record<string, unknown> {
  id: string;
  title: string;
  date: string;
  publication: string;
  duplicate_group: string;
  similarity_score?: number;
  content_preview?: string;
}

interface DuplicateDetail {
  log_id: string;
  metadata: DuplicateMetadata;
  duplicate_records: DuplicateRecord[];
  total_records: number;
}

const DuplicatesAnalysis: React.FC = () => {
  const { addNotification } = useNotificationStore();
  const [isLoading, setIsLoading] = useState(false);
  const [masterData, setMasterData] = useState<DuplicateMetadata[]>([]);
  const [filters, setFilters] = useState({
    user: '',
    publication: '',
    startDate: '',
    endDate: ''
  });

  const loadDuplicatesMetadata = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.getDuplicatesMetadata({
        user: filters.user || undefined,
        publication: filters.publication || undefined,
        start_date: filters.startDate || undefined,
        end_date: filters.endDate || undefined
      });
      setMasterData((response as any).duplicates_metadata || []);
      
      addNotification({
        type: 'success',
        title: 'Datos cargados',
        message: `Se encontraron ${(response as any).duplicates_metadata?.length || 0} registros de duplicados`
      });
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error al cargar datos',
        message: error instanceof Error ? error.message : 'Error desconocido'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadDuplicateDetails = async (masterRow: Record<string, unknown>): Promise<DuplicateDetail> => {
    try {
      const logId = String(masterRow.log_id);
      const response = await apiService.getDuplicateDetails(logId);
      return response as DuplicateDetail;
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Error al cargar detalles',
        message: error instanceof Error ? error.message : 'Error desconocido'
      });
      throw error;
    }
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const applyFilters = () => {
    loadDuplicatesMetadata();
  };

  const handleExportMaster = () => {
    if (masterData.length === 0) return;
    
    const csvContent = [
      'ID Log,Usuario,Publicación,Fecha Proceso,Cantidad Duplicados,Filtro,Fecha Creación',
      ...masterData.map(item => 
        `${item.log_id},${item.user},${item.publication},${item.process_date},${item.duplicates_count},"${item.duplicates_filter}",${item.created_at}`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `duplicados_metadata_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportDetails = (detailData: DuplicateDetail) => {
    const detail = detailData;
    if (!detail.duplicate_records || detail.duplicate_records.length === 0) return;
    
    const csvContent = [
      'ID,Título,Fecha,Publicación,Grupo Duplicado,Puntuación Similitud,Vista Previa',
      ...detail.duplicate_records.map(record => 
        `${record.id},"${record.title}",${record.date},${record.publication},${record.duplicate_group},${record.similarity_score || ''},"${record.content_preview || ''}"`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `duplicados_detalles_${detail.log_id}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const masterColumns: TableColumn[] = [
    {
      key: 'log_id',
      label: 'ID Log',
      width: '120px',
      filterable: true
    },
    {
      key: 'user',
      label: 'Usuario',
      sortable: true,
      filterable: true
    },
    {
      key: 'publication',
      label: 'Publicación',
      sortable: true,
      filterable: true,
      format: (value: unknown) => String(value).toUpperCase()
    },
    {
      key: 'process_date',
      label: 'Fecha Proceso',
      sortable: true,
      format: (value: unknown) => {
        if (typeof value === 'string') {
          return new Date(value).toLocaleDateString('es-ES');
        }
        return String(value);
      }
    },
    {
      key: 'duplicates_count',
      label: 'Duplicados',
      align: 'center' as const,
      sortable: true,
      render: (value: unknown) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {String(value)}
        </span>
      )
    },
    {
      key: 'duplicates_filter',
      label: 'Filtro Aplicado',
      render: (value: unknown) => (
        <span className="text-xs text-gray-600 max-w-xs truncate block" title={String(value)}>
          {String(value)}
        </span>
      )
    },
    {
      key: 'created_at',
      label: 'Fecha Creación',
      sortable: true,
      format: (value: unknown) => {
        if (typeof value === 'string') {
          return new Date(value).toLocaleString('es-ES');
        }
        return String(value);
      }
    }
  ];

  const detailColumns: TableColumn[] = [
    {
      key: 'id',
      label: 'ID',
      width: '100px'
    },
    {
      key: 'title',
      label: 'Título',
      render: (value: unknown) => (
        <div className="max-w-xs">
          <p className="text-sm font-medium text-gray-900 truncate" title={String(value)}>
            {String(value)}
          </p>
        </div>
      )
    },
    {
      key: 'date',
      label: 'Fecha',
      sortable: true,
      format: (value: unknown) => {
        if (typeof value === 'string') {
          return new Date(value).toLocaleDateString('es-ES');
        }
        return String(value);
      }
    },
    {
      key: 'publication',
      label: 'Publicación',
      format: (value: unknown) => String(value).toUpperCase()
    },
    {
      key: 'duplicate_group',
      label: 'Grupo',
      render: (value: unknown) => (
        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
          {String(value)}
        </span>
      )
    },
    {
      key: 'similarity_score',
      label: 'Similitud',
      align: 'center' as const,
      render: (value: unknown) => {
        if (value && typeof value === 'number') {
          const score = Math.round(value * 100);
          return (
            <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
              score >= 90 ? 'bg-red-100 text-red-800' :
              score >= 70 ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {score}%
            </span>
          );
        }
        return '-';
      }
    },
    {
      key: 'content_preview',
      label: 'Vista Previa',
      render: (value: unknown) => (
        <div className="max-w-xs">
          <p className="text-xs text-gray-600 truncate" title={String(value)}>
            {String(value) || 'No disponible'}
          </p>
        </div>
      )
    }
  ];

  const renderDetailView = (detailData: DuplicateDetail) => {
    const detail = detailData;
    
    if (!detail || !detail.duplicate_records) {
      return (
        <div className="text-center py-8">
          <p className="text-gray-500">No hay registros de duplicados disponibles</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-lg font-medium text-gray-900">
              Registros Duplicados
            </h4>
            <p className="text-sm text-gray-600">
              {detail.total_records} registros encontrados
            </p>
          </div>
          
          <button
            onClick={() => handleExportDetails(detail)}
            className="btn btn-secondary btn-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </button>
        </div>
        
        <DataTable
          columns={detailColumns}
          data={detail.duplicate_records}
          emptyMessage="No hay registros duplicados"
        />
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Análisis de Duplicados</h1>
        <p className="mt-1 text-sm text-gray-600">
          Detectar y analizar registros duplicados
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          <Filter className="w-5 h-5 inline mr-2" />
          Filtros de Búsqueda
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label htmlFor="user" className="block text-sm font-medium text-gray-700 mb-2">
              Usuario
            </label>
            <input
              type="text"
              id="user"
              value={filters.user}
              onChange={(e) => handleFilterChange('user', e.target.value)}
              className="input"
              placeholder="Nombre de usuario"
            />
          </div>
          
          <div>
            <label htmlFor="publication" className="block text-sm font-medium text-gray-700 mb-2">
              Publicación
            </label>
            <PublicationSelector
              value={filters.publication}
              onChange={(value) => handleFilterChange('publication', value)}
              placeholder="Todas las publicaciones"
              includeAll={true}
              allLabel="Todas las publicaciones"
            />
          </div>
          
          <DateRangePicker
            value={{ startDate: filters.startDate, endDate: filters.endDate }}
            onChange={(range) => {
              handleFilterChange('startDate', range?.startDate || '');
              handleFilterChange('endDate', range?.endDate || '');
            }}
            label="Rango de Fechas"
          />
          
          <div className="flex items-end space-x-2">
            <button
              onClick={applyFilters}
              disabled={isLoading}
              className="btn btn-primary flex-1"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Buscando...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Buscar
                </>
              )}
            </button>
            
            {masterData.length > 0 && (
              <button
                onClick={handleExportMaster}
                className="btn btn-secondary"
                title="Exportar lista principal"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Master-Detail View */}
      {masterData.length > 0 ? (
        <MasterDetailView
          masterData={masterData as Record<string, unknown>[]}
          masterColumns={masterColumns}
          detailRenderer={(detailData: Record<string, unknown>) => renderDetailView(detailData as unknown as DuplicateDetail)}
          onDetailLoad={async (masterRow: Record<string, unknown>) => {
            const result = await loadDuplicateDetails(masterRow);
            return result as unknown as Record<string, unknown>;
          }}
          masterTitle="Registros de Duplicados"
          detailTitle="Detalles de Duplicados"
          expandMode="inline"
          loading={isLoading}
        />
      ) : !isLoading ? (
        <div className="card">
          <div className="text-center py-12">
            <Copy className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No hay datos de duplicados
            </h3>
            <p className="text-gray-600 mb-4">
              Usa los filtros para buscar registros de duplicados
            </p>
            <button
              onClick={applyFilters}
              className="btn btn-primary"
            >
              <Search className="w-4 h-4 mr-2" />
              Buscar duplicados
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default DuplicatesAnalysis;