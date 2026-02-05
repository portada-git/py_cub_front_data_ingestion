/**
 * Storage Metadata Analysis View
 * Modern implementation with dark theme and internationalization
 * Updated to use new /api/metadata/storage endpoint with comprehensive filtering
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Database, Filter, Download, RefreshCw, Search, X } from 'lucide-react';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import { Publication } from '../types';
import AnalysisCard from '../components/AnalysisCard';
import { ResultsCard, InfoMessage, EmptyState } from '../components/ResultsCard';

interface StorageMetadataItem {
  stored_log_id: string;
  publication_name: string;
  table_name: string;
  process_name: string;
  stage: string;
  records_count: number;
  file_path: string;
  stored_at: string;
  metadata: {
    format: string;
    compression: string;
    schema_version: string;
    partition_columns: string[];
  };
}

interface StorageMetadataResponse {
  storage_records: StorageMetadataItem[];
  total_records: number;
  filters_applied: {
    publication?: string;
    table_name?: string;
    process_name?: string;
    stage?: string;
    start_date?: string;
    end_date?: string;
  };
}

interface FilterState {
  publication: string;
  table_name: string;
  process_name: string;
  stage: string;
  start_date: string;
  end_date: string;
}

const StorageMetadataView: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<StorageMetadataResponse | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    publication: '',
    table_name: '',
    process_name: '',
    stage: '',
    start_date: '',
    end_date: ''
  });

  // Available stages for filtering
  const stages = ['bronze', 'silver', 'gold'];

  // Fetch available publications on mount
  useEffect(() => {
    const fetchPublications = async () => {
      const result = await withErrorHandling(async () => {
        return await apiService.getPublications();
      });
      
      if (result && result.publications) {
        setPublications(result.publications);
      }
    };

    fetchPublications();
    // Load all data initially
    handleSearch();
  }, []);

  const handleSearch = async () => {
    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      // Filter out empty values
      const activeFilters = Object.entries(filters).reduce((acc, [key, value]) => {
        if (value && value.trim()) {
          acc[key as keyof FilterState] = value.trim();
        }
        return acc;
      }, {} as Partial<FilterState>);

      return await apiService.getStorageMetadata(activeFilters);
    });
    
    if (result) {
      setResults(result);
    }
    
    setIsLoading(false);
  };

  const handleFilterChange = (field: keyof FilterState, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const clearFilters = () => {
    setFilters({
      publication: '',
      table_name: '',
      process_name: '',
      stage: '',
      start_date: '',
      end_date: ''
    });
  };

  const exportData = () => {
    if (!results?.storage_records) return;
    
    const csv = [
      // Header
      'Log ID,Publication,Table,Process,Stage,Records,File Path,Stored At,Format,Compression',
      // Data rows
      ...results.storage_records.map(item => 
        `"${item.stored_log_id}","${item.publication_name}","${item.table_name}","${item.process_name}","${item.stage}",${item.records_count},"${item.file_path}","${item.stored_at}","${item.metadata.format}","${item.metadata.compression}"`
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `storage_metadata_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasActiveFilters = Object.values(filters).some(value => value && value.trim());

  return (
    <div className="space-y-6">
      {/* Header */}
      <AnalysisCard
        title={t('analysis.storageMetadata.title')}
        description={t('analysis.storageMetadata.description')}
        icon={Database}
      />

      {/* Controls */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showFilters 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Filter className="w-4 h-4" />
              {t('common.filters')}
              {hasActiveFilters && (
                <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                  {Object.values(filters).filter(v => v && v.trim()).length}
                </span>
              )}
            </button>
            
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
                {t('common.clearFilters')}
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSearch}
              disabled={isLoading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              {t('common.search')}
            </button>
            
            {results?.storage_records && results.storage_records.length > 0 && (
              <button
                onClick={exportData}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                {t('common.export')}
              </button>
            )}
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="border-t border-gray-700 pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('common.publication')}
                </label>
                <select
                  value={filters.publication}
                  onChange={(e) => handleFilterChange('publication', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{t('common.all')}</option>
                  {publications.map(pub => (
                    <option key={pub.name} value={pub.name}>
                      {pub.display_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('analysis.storageMetadata.tableName')}
                </label>
                <input
                  type="text"
                  value={filters.table_name}
                  onChange={(e) => handleFilterChange('table_name', e.target.value)}
                  placeholder={t('analysis.storageMetadata.tableNamePlaceholder')}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('analysis.storageMetadata.processName')}
                </label>
                <input
                  type="text"
                  value={filters.process_name}
                  onChange={(e) => handleFilterChange('process_name', e.target.value)}
                  placeholder={t('analysis.storageMetadata.processNamePlaceholder')}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('analysis.storageMetadata.stage')}
                </label>
                <select
                  value={filters.stage}
                  onChange={(e) => handleFilterChange('stage', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">{t('common.all')}</option>
                  {stages.map(stage => (
                    <option key={stage} value={stage}>
                      {stage.charAt(0).toUpperCase() + stage.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('common.startDate')}
                </label>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => handleFilterChange('start_date', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {t('common.endDate')}
                </label>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => handleFilterChange('end_date', e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <ResultsCard
          title={t('analysis.storageMetadata.results')}
          totalCount={results.total_records}
          isLoading={isLoading}
        >
          {results.storage_records.length === 0 ? (
            <EmptyState message={t('analysis.storageMetadata.noData')} />
          ) : (
            <div className="space-y-4">
              {/* Summary */}
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-400">
                      {results.storage_records.length}
                    </div>
                    <div className="text-sm text-gray-400">
                      {t('analysis.storageMetadata.totalRecords')}
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-400">
                      {results.storage_records.reduce((sum, item) => sum + item.records_count, 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-400">
                      {t('analysis.storageMetadata.totalStoredRecords')}
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-400">
                      {new Set(results.storage_records.map(item => item.publication_name)).size}
                    </div>
                    <div className="text-sm text-gray-400">
                      {t('analysis.storageMetadata.uniquePublications')}
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-orange-400">
                      {new Set(results.storage_records.map(item => item.stage)).size}
                    </div>
                    <div className="text-sm text-gray-400">
                      {t('analysis.storageMetadata.uniqueStages')}
                    </div>
                  </div>
                </div>
              </div>

              {/* Data Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.logId')}
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('common.publication')}
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.table')}
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.process')}
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.stage')}
                      </th>
                      <th className="text-right py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.records')}
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.format')}
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-gray-300">
                        {t('analysis.storageMetadata.storedAt')}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.storage_records.map((item, index) => (
                      <tr 
                        key={item.stored_log_id} 
                        className={`border-b border-gray-800 hover:bg-gray-700 transition-colors ${
                          index % 2 === 0 ? 'bg-gray-800/50' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-mono text-xs text-blue-400">
                          {item.stored_log_id}
                        </td>
                        <td className="py-3 px-4 text-white">
                          {item.publication_name}
                        </td>
                        <td className="py-3 px-4 text-gray-300">
                          {item.table_name}
                        </td>
                        <td className="py-3 px-4 text-gray-300">
                          {item.process_name}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            item.stage === 'bronze' ? 'bg-orange-900 text-orange-300' :
                            item.stage === 'silver' ? 'bg-gray-600 text-gray-300' :
                            'bg-yellow-900 text-yellow-300'
                          }`}>
                            {item.stage}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right text-green-400 font-medium">
                          {item.records_count.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-gray-400">
                          {item.metadata.format} ({item.metadata.compression})
                        </td>
                        <td className="py-3 px-4 text-gray-400 text-xs">
                          {new Date(item.stored_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </ResultsCard>
      )}
    </div>
  );
};

export default StorageMetadataView;
    
    fetchPublications();
  }, []);

  const publicationOptions = [
    { value: '', label: t('analysis.storageMetadata.allPublications') || 'All Publications' },
    ...publications.map(pub => ({ value: pub.code, label: pub.name || pub.code }))
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      return await apiService.getStorageMetadata(
        formData.publication || undefined
      );
    });

    if (result) {
      setResults(result as StorageMetadataResponse);
    }
    
    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      <AnalysisCard
        title={t('analysis.storageMetadata.title')}
        subtitle={t('analysis.storageMetadata.subtitle')}
        icon={Database}
      >
        <QueryForm
          onSubmit={handleSubmit}
          submitText={t('analysis.storageMetadata.queryMetadata')}
          isLoading={isLoading}
          submitColor="green"
        >
          <SelectField
            label={t('analysis.storageMetadata.publication') || 'Publication'}
            description={t('analysis.storageMetadata.publicationDesc') || 'Filter by publication name'}
            name="publication"
            value={formData.publication}
            onChange={handleInputChange}
            options={publicationOptions}
            className="md:col-span-2"
          />
        </QueryForm>
      </AnalysisCard>

      {/* Results */}
      {results && (
        <ResultsCard title={t('analysis.storageMetadata.results')}>
          {!results.storage_metadata || results.storage_metadata.length === 0 ? (
            <EmptyState message={t('analysis.storageMetadata.noResults')} />
          ) : (
            <div className="space-y-4">
              <InfoMessage
                message={`Total de registros de almacenamiento: ${results.total_count}`}
                type="success"
              />
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Log ID
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Publicación
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Registros
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Ruta del Archivo
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Fecha de Almacenamiento
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.storage_metadata.map((item, index) => (
                      <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4 text-slate-700 font-mono text-xs">
                          {item.stored_log_id.substring(0, 8)}...
                        </td>
                        <td className="py-3 px-4 text-slate-700 font-medium">
                          {item.publication_name}
                        </td>
                        <td className="py-3 px-4 text-slate-700 font-mono">
                          {item.records_count.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-slate-700 text-sm font-mono truncate max-w-xs" title={item.file_path}>
                          {item.file_path}
                        </td>
                        <td className="py-3 px-4 text-slate-700 text-sm">
                          {new Date(item.stored_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </ResultsCard>
      )}

      {/* Info Message */}
      <InfoMessage
        message={t('analysis.storageMetadata.infoMessage') || 'Storage metadata shows information about data stored in the Delta Lake.'}
        type="info"
      />
    </div>
  );
};

export default StorageMetadataView;