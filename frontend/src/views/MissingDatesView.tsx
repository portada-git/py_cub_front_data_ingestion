/**
 * Missing Dates Analysis View
 * Modern implementation with dark theme and internationalization
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Calendar } from 'lucide-react';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import AnalysisCard from '../components/AnalysisCard';
import QueryForm from '../components/QueryForm';
import { SelectField, InputField } from '../components/FormField';
import { ResultsCard, InfoMessage, EmptyState } from '../components/ResultsCard';

interface MissingDateEntry {
  date: string;
  edition: string;
  gap_duration?: string;
}

interface MissingDatesResponse {
  publication_name: string;
  query_type: string;
  missing_dates: MissingDateEntry[];
  total_missing: number;
}

const MissingDatesView: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<MissingDatesResponse | null>(null);
  const [formData, setFormData] = useState({
    publication: '',
    queryMethod: 'date_range',
    startDate: '',
    endDate: ''
  });

  const publications = [
    { value: '', label: t('analysis.missingDates.selectPublication') },
    { value: 'db', label: 'Diario de Barcelona (DB)' },
    { value: 'dm', label: 'Diario de Madrid (DM)' },
    { value: 'sm', label: 'Semanario de Málaga (SM)' }
  ];

  const queryMethods = [
    { value: 'date_range', label: t('analysis.missingDates.dateRange') },
    { value: 'file_list', label: t('analysis.missingDates.fileList') }
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.publication) return;

    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      return await apiService.getMissingDates({
        publication_name: formData.publication,
        start_date: formData.startDate || undefined,
        end_date: formData.endDate || undefined
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
        title={t('analysis.missingDates.title')}
        subtitle={t('analysis.missingDates.subtitle')}
        icon={Calendar}
      >
        <QueryForm
          onSubmit={handleSubmit}
          submitText={t('analysis.missingDates.executeQuery')}
          isLoading={isLoading}
          submitColor="blue"
        >
          <SelectField
            label={t('analysis.missingDates.publication')}
            value={formData.publication}
            onChange={handleInputChange}
            options={publications}
            required
          />

          <SelectField
            label={t('analysis.missingDates.queryMethod')}
            value={formData.queryMethod}
            onChange={handleInputChange}
            options={queryMethods}
          />

          {formData.queryMethod === 'date_range' && (
            <>
              <InputField
                label={t('analysis.missingDates.startDate')}
                description={t('analysis.missingDates.startDateOptional')}
                type="date"
                value={formData.startDate}
                onChange={handleInputChange}
              />

              <InputField
                label={t('analysis.missingDates.endDate')}
                description={t('analysis.missingDates.endDateOptional')}
                type="date"
                value={formData.endDate}
                onChange={handleInputChange}
              />
            </>
          )}
        </QueryForm>
      </AnalysisCard>

      {/* Results */}
      {results && (
        <ResultsCard title={t('analysis.missingDates.results')}>
          {results.missing_dates.length === 0 ? (
            <EmptyState message={t('analysis.missingDates.noResults')} />
          ) : (
            <div className="space-y-4">
              <InfoMessage
                message={t('analysis.missingDates.totalMissing', { count: results.total_missing })}
                type="info"
              />
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        {t('analysis.missingDates.date')}
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">
                        {t('analysis.missingDates.edition')}
                      </th>
                      {results.missing_dates.some(d => d.gap_duration) && (
                        <th className="text-left py-3 px-4 font-semibold text-slate-900">
                          {t('analysis.missingDates.duration')}
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {results.missing_dates.map((entry, index) => (
                      <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4 text-slate-700">{entry.date}</td>
                        <td className="py-3 px-4 text-slate-700">{entry.edition}</td>
                        {entry.gap_duration && (
                          <td className="py-3 px-4 text-slate-700">{entry.gap_duration}</td>
                        )}
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

export default MissingDatesView;