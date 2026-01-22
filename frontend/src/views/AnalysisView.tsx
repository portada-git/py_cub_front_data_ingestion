/**
 * Analysis view component
 * Handles all analysis queries as specified in the UI requirements
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PendingFilesAnalysis from '../components/analysis/PendingFilesAnalysis';
import MissingDatesAnalysis from '../components/analysis/MissingDatesAnalysis';
import DuplicatesAnalysis from '../components/analysis/DuplicatesAnalysis';
import DailyEntriesAnalysis from '../components/analysis/DailyEntriesAnalysis';
import KnownEntitiesAnalysis from '../components/analysis/KnownEntitiesAnalysis';
import StorageMetadataAnalysis from '../components/analysis/StorageMetadataAnalysis';
import ProcessMetadataAnalysis from '../components/analysis/ProcessMetadataAnalysis';

const AnalysisView: React.FC = () => {
  return (
    <div className="space-y-6">
      <Routes>
        <Route path="/" element={<Navigate to="pending-files" replace />} />
        <Route path="pending-files" element={<PendingFilesAnalysis />} />
        <Route path="missing-dates" element={<MissingDatesAnalysis />} />
        <Route path="duplicates" element={<DuplicatesAnalysis />} />
        <Route path="daily-entries" element={<DailyEntriesAnalysis />} />
        <Route path="known-entities" element={<KnownEntitiesAnalysis />} />
        <Route path="storage-metadata" element={<StorageMetadataAnalysis />} />
        <Route path="process-metadata" element={<ProcessMetadataAnalysis />} />
        <Route path="*" element={<Navigate to="pending-files" replace />} />
      </Routes>
    </div>
  );
};

export default AnalysisView;