/**
 * Configuration view component
 * Handles administrative and system configuration views
 */

import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import StorageMetadataView from "./StorageMetadataView";
import ProcessMetadataView from "./ProcessMetadataView";
import KnownEntitiesView from "./KnownEntitiesView";

const ConfigurationView: React.FC = () => {
  return (
    <div className="space-y-6">
      <Routes>
        <Route path="/" element={<Navigate to="storage-metadata" replace />} />
        <Route path="storage-metadata" element={<StorageMetadataView />} />
        <Route path="process-metadata" element={<ProcessMetadataView />} />
        <Route path="known-entities" element={<KnownEntitiesView />} />
        <Route path="*" element={<Navigate to="storage-metadata" replace />} />
      </Routes>
    </div>
  );
};

export default ConfigurationView;
