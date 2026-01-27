/**
 * Process Metadata Analysis View
 * Modern implementation with dark theme and internationalization
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings } from 'lucide-react';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import AnalysisCard from '../components/AnalysisCard';
import QueryForm from '../components/QueryForm';
import { SelectField } from '../components/FormField';
import { ResultsCard, InfoMessage, EmptyState } from '../components/ResultsCard';

interface ProcessMetadataResponse {
  processes: Array<{
    process_name: string;
    process_type: string;
    status: string;
    started_at: string;
    completed_at?: string;
    records_processed: number;
    [key: string]: any;
  }>;
  total_count: number;
}

const ProcessMetadataView: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<ProcessMetadataResponse | null>(null);
  const [formData, setFormData] = useState({
    processName: ''
  });

  const processOptions = [
    { value: '', label: t('analysis.processMetadata.allProcesses') },
    { value: 'data_extraction', label: 'Data Extraction' },
    { value: 'data_transformation', label: 'Data Transformation' },
    { value: 'data_validation', label: 'Data Validation' },
    { value: 'entity_processing', label: 'Entity Processing' }
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      return await apiService.getProcessMetadata({
        process_name: formData.processName || undefined
      });
    });

    if (result) {
      setResults(result as ProcessMetadataResponse);
    }
    
    setIsLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <AnalysisCard
        title={t('analysis.processMetadata.title')}
        subtitle={t('analysis.processMetadata.subtitle')}
        icon={Settings}
      >
        <QueryForm
          onSubmit={handleSubmit}
          submitText={t('analysis.processMetadata.queryProcesses')}
          isLoading={isLoading}
          submitColor="purple"
        >
          <SelectField
            label={t('analysis.processMetadata.processName')}
            description={t('analysis.processMetadata.processNameDesc')}
            name="processName"
            value={formData.processName}
            onChange={handleInputChange}
            options={processOptions}
            className="md:col-span-2"
          />
        </QueryForm>
      </AnalysisCard>

      {/* Results */}
      {results && (
        <ResultsCard title={t('analysis.processMetadata.results')}>
          {!results.processes || results.processes.length === 0 ? (
            <EmptyState message={t('analysis.processMetadata.noResults')} />
          ) : (
            <div className="space-y-4">
              <InfoMessage
                message={`Total de procesos encontrados: ${results.total_count}`}
                type="success"
              />
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Proceso
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Tipo
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Estado
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Registros
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Iniciado
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        Completado
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.processes.map((process, index) => (
                      <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4 text-slate-700 font-medium">
                          {process.process_name}
                        </td>
                        <td className="py-3 px-4 text-slate-700">
                          {process.process_type}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(process.status)}`}>
                            {process.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-700 font-mono">
                          {process.records_processed.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-slate-700 text-sm">
                          {new Date(process.started_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-slate-700 text-sm">
                          {process.completed_at 
                            ? new Date(process.completed_at).toLocaleString()
                            : '-'
                          }
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
        message={t('analysis.processMetadata.infoMessage')}
        type="info"
      />
    </div>
  );
};

export default ProcessMetadataView;