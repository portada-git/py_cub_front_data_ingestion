/**
 * Duplicates Analysis component
 * Placeholder for duplicates functionality
 */

import React from 'react';
import { Copy } from 'lucide-react';

const DuplicatesAnalysis: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Análisis de Duplicados</h1>
        <p className="mt-1 text-sm text-gray-600">
          Detectar y analizar registros duplicados
        </p>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <Copy className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Análisis de Duplicados
          </h3>
          <p className="text-gray-600">
            Esta funcionalidad estará disponible próximamente
          </p>
        </div>
      </div>
    </div>
  );
};

export default DuplicatesAnalysis;