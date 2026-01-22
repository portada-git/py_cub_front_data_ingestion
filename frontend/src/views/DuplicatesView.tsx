/**
 * Duplicates Analysis View
 * Modern implementation with dark theme and internationalization
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Copy } from 'lucide-react';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import { DuplicatesResponse } from '../types';
import AnalysisCard from '../components/AnalysisCard';
import QueryForm from '../components/QueryForm';
import { SelectField } from '../components/FormField';
import { ResultsCard, InfoMessage, EmptyState } from '../components/ResultsCard';

const DuplicatesView: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<DuplicatesResponse | null>(null);
  const [formData, setFormData] = useState({
    publication: ''
  });

  const publications = [
    { value: '', label: t('analysis.duplicates.allPublications') },
    { value: 'db', label: 'Diario de Barcelona' },
    { value: 'dm', label: 'Diario Mercantil' },
    { value: 'sm', label: 'Semanario Mercantil' },
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const result = await withErrorHandling(async () => {
      return await apiService.getDuplicates({
        publication: formData.publication
      });
    });

    if (result) {
      setResults(result);
    }

    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      <AnalysisCard
        title={t('analysis.duplicates.title')}
        subtitle={t('analysis.duplicates.description')}
        icon={Copy}
      >
        <QueryForm
          onSubmit={handleSubmit}
          submitText={t('analysis.duplicates.queryDuplicates')}
          isLoading={isLoading}
          submitColor="orange"
        >
          <SelectField
            label={t('analysis.duplicates.publication')}
            value={formData.publication}
            onChange={handleInputChange}
            options={publications}
            required
            className="md:col-span-2"
          />
        </QueryForm>
      </AnalysisCard>

      {/* Results */}
      {results && results.duplicates.length > 0 ? (
        <ResultsCard title={t('analysis.duplicates.results')}>
          <div className="space-y-4">
            <p className="text-slate-400">
              {results.total_duplicates} {t('analysis.duplicates.duplicatesFound')}
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-700">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                      {t('analysis.duplicates.logId')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                      {t('analysis.duplicates.date')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                      {t('analysis.duplicates.edition')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                      {t('analysis.duplicates.publication')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                      {t('analysis.duplicates.uploadedBy')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                      {t('analysis.duplicates.count')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-slate-900 divide-y divide-slate-700">
                  {results.duplicates.map((duplicate, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-xs bg-slate-700 px-2 py-1 rounded">
                          {duplicate.log_id}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                        {new Date(duplicate.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                        {duplicate.edition}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                        {duplicate.publication.toUpperCase()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300">
                        {duplicate.uploaded_by}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-semibold text-orange-400">
                          {duplicate.duplicate_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </ResultsCard>
      ) : results ? (
        <EmptyState message={t('analysis.duplicates.noDuplicatesDescription')} />
      ) : null}

      <InfoMessage message={t('analysis.duplicates.info')} />
    </div>
  );
};

export default DuplicatesView;