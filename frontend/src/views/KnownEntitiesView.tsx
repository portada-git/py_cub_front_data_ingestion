/**
 * Known Entities Analysis View
 * Implements Requirements 11.1-11.3: Query known entities
 */

import React, { useState, useEffect } from 'react';
import { 
  Tags, 
  Search, 
  AlertCircle, 
  Loader2, 
  Calendar,
  RefreshCw,
  Download,
  Eye
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';

interface KnownEntity {
  id: string;
  name: string;
  type: string;
  category: string;
  uploadDate: string;
  uploadedBy: string;
  recordCount: number;
  lastUsed?: string;
}

interface KnownEntitiesResponse {
  entities: KnownEntity[];
  totalCount: number;
  categories: string[];
  types: string[];
}

const KnownEntitiesView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<KnownEntitiesResponse | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [expandedEntity, setExpandedEntity] = useState<string | null>(null);

  const fetchKnownEntities = async () => {
    setIsLoading(true);
    
    const result = await withErrorHandling(async () => {
      return await apiService.getKnownEntities();
    });

    if (result) {
      // Transform the API response to match our interface
      const transformedResult: KnownEntitiesResponse = {
        entities: result.entities?.map((e: any, index: number) => ({
          id: e.id || `entity-${index}`,
          name: e.name || 'Unknown',
          type: e.type || 'Unknown',
          category: e.category || 'General',
          uploadDate: e.uploadDate || new Date().toISOString(),
          uploadedBy: e.uploadedBy || 'System',
          recordCount: e.count || e.recordCount || 0,
          lastUsed: e.lastUsed
        })) || [],
        totalCount: result.entities?.length || 0,
        categories: [...new Set(result.entities?.map((e: any) => e.category || 'General') || [])],
        types: [...new Set(result.entities?.map((e: any) => e.type || 'Unknown') || [])]
      };
      setResults(transformedResult);
      setLastUpdated(new Date());
    }
    
    setIsLoading(false);
  };

  useEffect(() => {
    fetchKnownEntities();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetchKnownEntities();
  };

  const filteredEntities = results?.entities.filter(entity => {
    const matchesSearch = !searchTerm || 
      entity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entity.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = !selectedCategory || entity.category === selectedCategory;
    const matchesType = !selectedType || entity.type === selectedType;
    
    return matchesSearch && matchesCategory && matchesType;
  }) || [];

  const handleEntityExpand = (entityId: string) => {
    setExpandedEntity(expandedEntity === entityId ? null : entityId);
  };

  const handleExportEntity = (entity: KnownEntity) => {
    // Create a simple CSV export of the entity data
    const csvContent = `Name,Type,Category,Upload Date,Uploaded By,Record Count\n${entity.name},${entity.type},${entity.category},${entity.uploadDate},${entity.uploadedBy},${entity.recordCount}`;
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `entity_${entity.name.replace(/\s+/g, '_')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header and Search */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-cyan-500/10 rounded-xl">
            <Tags className="w-8 h-8 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">
              Entidades Conocidas
            </h1>
            <p className="text-slate-400">
              Consulta todas las entidades conocidas subidas al sistema
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search Term */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Buscar entidad
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Nombre o tipo de entidad"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Buscar entidad por nombre o tipo"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Categoría
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Filtrar por categoría"
              >
                <option value="">Todas las categorías</option>
                {results?.categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Tipo
              </label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                aria-label="Filtrar por tipo"
              >
                <option value="">Todos los tipos</option>
                {results?.types.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className={clsx(
                "flex-1 flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-medium transition-all",
                isLoading
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-cyan-600 text-white hover:bg-cyan-500"
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Cargando...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Buscar Entidades
                </>
              )}
            </button>
            
            {results && (
              <button
                type="button"
                onClick={fetchKnownEntities}
                disabled={isLoading}
                className="px-4 py-3 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
                aria-label="Actualizar resultados"
              >
                <RefreshCw className={clsx("w-5 h-5", isLoading && "animate-spin")} />
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white">Resumen de Entidades</h2>
              {lastUpdated && (
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Calendar className="w-4 h-4" />
                  Actualizado: {lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-cyan-400 mb-2">
                  {filteredEntities.length}
                </div>
                <div className="text-slate-400">Entidades Mostradas</div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">
                  {results.totalCount}
                </div>
                <div className="text-slate-400">Total Entidades</div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">
                  {results.categories.length}
                </div>
                <div className="text-slate-400">Categorías</div>
              </div>
              
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">
                  {results.types.length}
                </div>
                <div className="text-slate-400">Tipos</div>
              </div>
            </div>
          </div>

          {/* Entities List */}
          {filteredEntities.length > 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="p-6 border-b border-slate-800">
                <h3 className="text-lg font-bold text-white">Lista de Entidades</h3>
                <p className="text-slate-400 text-sm">
                  {filteredEntities.length} entidades encontradas
                </p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-800/50">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Nombre
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Tipo
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Categoría
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Subido por
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Fecha
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Registros
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {filteredEntities.map((entity) => (
                      <React.Fragment key={entity.id}>
                        <tr className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Tags className="w-4 h-4 text-slate-500" />
                              <span className="text-slate-300 font-medium">
                                {entity.name}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                              {entity.type}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-slate-300">{entity.category}</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-slate-300">{entity.uploadedBy}</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-slate-300 text-sm">
                              {new Date(entity.uploadDate).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-slate-300 font-mono">
                              {entity.recordCount.toLocaleString()}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleEntityExpand(entity.id)}
                                className="text-cyan-400 hover:text-cyan-300 transition-colors"
                                aria-label={`Ver detalles de ${entity.name}`}
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleExportEntity(entity)}
                                className="text-green-400 hover:text-green-300 transition-colors"
                                aria-label={`Exportar ${entity.name}`}
                              >
                                <Download className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                        
                        {/* Expanded Details */}
                        {expandedEntity === entity.id && (
                          <tr>
                            <td colSpan={7} className="px-6 py-4 bg-slate-800/20">
                              <div className="space-y-3">
                                <h4 className="text-sm font-medium text-slate-300">
                                  Detalles de la entidad:
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="text-slate-400">ID:</span>
                                    <span className="text-slate-300 ml-2 font-mono">{entity.id}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-400">Último uso:</span>
                                    <span className="text-slate-300 ml-2">
                                      {entity.lastUsed 
                                        ? new Date(entity.lastUsed).toLocaleString()
                                        : 'Nunca usado'
                                      }
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            /* Empty State */
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
              <Tags className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-300 mb-2">
                No se encontraron entidades
              </h3>
              <p className="text-slate-500">
                {searchTerm || selectedCategory || selectedType
                  ? 'No hay entidades que coincidan con los filtros aplicados.'
                  : 'No hay entidades conocidas en el sistema.'
                }
              </p>
            </div>
          )}
        </div>
      )}

      {/* Info Card */}
      <div className="bg-cyan-900/10 border border-cyan-800/30 rounded-xl p-6 flex gap-4 items-start">
        <AlertCircle className="w-6 h-6 text-cyan-400 shrink-0 mt-0.5" />
        <div className="text-sm text-slate-400 leading-relaxed">
          <p className="text-cyan-200 font-medium mb-2">
            Información sobre entidades conocidas:
          </p>
          <p>
            Esta consulta muestra todas las entidades conocidas que han sido subidas al sistema. 
            Las entidades son datos de referencia utilizados para el reconocimiento y procesamiento 
            de información en los documentos históricos. Puedes filtrar por nombre, categoría o tipo 
            para encontrar entidades específicas.
          </p>
        </div>
      </div>
    </div>
  );
};

export default KnownEntitiesView;