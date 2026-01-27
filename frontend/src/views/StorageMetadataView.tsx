/**
 * Storage Metadata Analysis View
 * Modern implementation with dark theme and internationalization
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Database } from 'lucide-react';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import AnalysisCard from '../components/AnalysisCard';
import QueryForm from '../components/QueryForm';
import { SelectField } from '../components/FormField';
import { ResultsCard, InfoMessage, EmptyState } from '../components/ResultsCard';

interface StorageMetadataResponse {
  metadata: Array<{
    table_name: string;
    field_lineage: string;
    process_name: string;
    created_at: string;
    [key: string]: any;
  }>;
  total_count: number;
}

const StorageMetadataView: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<StorageMetadataResponse | null>(null);
  const [formData, setFormData] = useState({
    tableName: '',
    responsibleProcess: ''
  });

  const tableOptions = [
    { value: '', label: t('analysis.storageMetadata.allTables') },
    { value: 'ship_entries', label: 'ship_entries' },
    { value: 'known_entities', label: 'known_entities' },
    { value: 'transformations', label: 'transformations' }
  ];

  const processOptions = [
    { value: '', label: t('analysis.storageMetadata.allProcesses') },
    { value: 'extraction', label: 'Extraction Process' },
    { value: 'transformation', label: 'Transformation Process' },
    { value: 'validation', label: 'Validation Process' }
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      return await apiService.getStorageMetadata({
        table_name: formData.tableName || undefined,
        responsible_process: formData.responsibleProcess || undefined
      });
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
            label={t('analysis.storageMetadata.tableName')}
            description={t('analysis.storageMetadata.tableNameDesc')}
            name="tableName"
            value={formData.tableName}
            onChange={handleInputChange}
            options={tableOptions}
          />

          <SelectField
            label={t('analysis.storageMetadata.responsibleProcess')}
            description={t('analysis.storageMetadata.responsibleProcessDesc')}
            name="responsibleProcess"
            value={formData.responsibleProcess}
            onChange={handleInputChange}
            options={processOptions}
          />
        </QueryForm>
      </AnalysisCard>

      {/* Results */}
      {results && (
        <ResultsCard title={t('analysis.storageMetadata.results')}>
          {!results.metadata || results.metadata.length === 0 ? (
            <EmptyState message={t('analysis.storageMetadata.noResults')} />
          ) : (
            <div className="space-y-4">
              <InfoMessage
                message={`Total de metadatos encontrados: ${results.total_count}`}
                type="success"
              />
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Tabla
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Linaje de Campo
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Proceso
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Fecha de Creación
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.metadata.map((item, index) => (
                      <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4 text-slate-700 font-mono text-sm">
                          {item.table_name}
                        </td>
                        <td className="py-3 px-4 text-slate-700 text-sm">
                          {item.field_lineage}
                        </td>
                        <td className="py-3 px-4 text-slate-700">
                          {item.process_name}
                        </td>
                        <td className="py-3 px-4 text-slate-700 text-sm">
                          {new Date(item.created_at).toLocaleString()}
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
        message={t('analysis.storageMetadata.infoMessage')}
        type="info"
      />
    </div>
  );
};

export default StorageMetadataView;