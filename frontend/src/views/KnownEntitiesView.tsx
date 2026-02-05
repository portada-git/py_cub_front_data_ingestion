/**
 * Known Entities Analysis View
 * Implements Requirements 11.1-11.3: Query known entities
 */

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Users, Search, AlertCircle, Loader2, Eye } from "lucide-react";
import { apiService } from "../services/api";
import { withErrorHandling } from "../utils/apiErrorHandler";
import { KnownEntitiesResponse } from "../types";
import DataExport from "../components/DataExport";

const KnownEntitiesView: React.FC = () => {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<KnownEntitiesResponse | null>(null);
  const [formData, setFormData] = useState({
    searchTerm: "",
    entityType: "",
  });

  const typeOptions = [
    { value: "", label: "Todos los tipos" },
    { value: "flag", label: t("ingestion.entity_flag") },
    { value: "comodity", label: t("ingestion.entity_comodity") },
    { value: "ship_type", label: t("ingestion.entity_ship_type") },
    { value: "unit", label: t("ingestion.entity_unit") },
    { value: "port", label: t("ingestion.entity_port") },
    { value: "master_role", label: t("ingestion.entity_master_role") },
  ];

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, searchTerm: e.target.value }));
  };

  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, entityType: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetchKnownEntities();
  };

  const fetchKnownEntities = async () => {
    setIsLoading(true);

    const result = await withErrorHandling(async () => {
      return await apiService.getKnownEntities();
    });

    if (result) {
      setResults(result);
    }

    setIsLoading(false);
  };

  // Load entities on component mount
  useEffect(() => {
    fetchKnownEntities();
  }, []);

  const getTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      flag: "bg-blue-100 text-blue-800",
      comodity: "bg-green-100 text-green-800",
      ship_type: "bg-purple-100 text-purple-800",
      unit: "bg-cyan-100 text-cyan-800",
      port: "bg-orange-100 text-orange-800",
      master_role: "bg-indigo-100 text-indigo-800",
    };
    return colors[type] || "bg-gray-100 text-gray-800";
  };

  const getTypeLabel = (type: string): string => {
    const option = typeOptions.find((opt) => opt.value === type);
    return option ? option.label : type;
  };

  const filteredEntities =
    results?.entities.filter((entity) => {
      const matchesSearch =
        !formData.searchTerm ||
        entity.name.toLowerCase().includes(formData.searchTerm.toLowerCase());
      const matchesType =
        !formData.entityType || entity.type === formData.entityType;
      return matchesSearch && matchesType;
    }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t("navigation.knownEntities")}
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            {t(
              "known_entities.description",
              "Consulta las entidades conocidas almacenadas en el sistema",
            )}
          </p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="searchTerm"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Buscar entidad
              </label>
              <input
                type="text"
                id="searchTerm"
                value={formData.searchTerm}
                onChange={handleSearchChange}
                placeholder="Nombre de la entidad..."
                className="input"
              />
            </div>

            <div>
              <label
                htmlFor="entityType"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Tipo de entidad
              </label>
              <select
                id="entityType"
                value={formData.entityType}
                onChange={handleTypeChange}
                className="input"
              >
                {typeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Consultando...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Buscar Entidades
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {filteredEntities.length}
              </div>
              <div className="text-gray-600">Entidades Encontradas</div>
            </div>

            <div className="card text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {new Set(filteredEntities.map((e) => e.type)).size}
              </div>
              <div className="text-gray-600">Tipos Diferentes</div>
            </div>

            <div className="card text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {filteredEntities
                  .reduce((sum, e) => sum + e.count, 0)
                  .toLocaleString()}
              </div>
              <div className="text-gray-600">Total de Referencias</div>
            </div>
          </div>

          {/* Export Component */}
          {filteredEntities.length > 0 && (
            <DataExport
              data={filteredEntities.map((entity) => ({
                name: entity.name,
                type: entity.type,
                count: entity.count,
              }))}
              filename="entidades_conocidas"
              title="Exportar Lista de Entidades"
            />
          )}

          {/* Entities Grid */}
          {filteredEntities.length > 0 ? (
            <div className="card p-0 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Entidades ({filteredEntities.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                {filteredEntities.map((entity, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">
                          {entity.name}
                        </h4>
                      </div>
                      <button
                        className="text-gray-400 hover:text-gray-600 p-1 rounded"
                        title="Ver detalles"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Tipo:</span>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(entity.type)}`}
                        >
                          {getTypeLabel(entity.type)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">
                          Referencias:
                        </span>
                        <span className="font-mono text-sm font-semibold text-gray-900">
                          {entity.count.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No se encontraron entidades
              </h3>
              <p className="text-gray-500">
                No hay entidades que coincidan con los criterios de búsqueda.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Information */}
      <div className="card">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-blue-500 mr-3 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-1">
              Información importante:
            </p>
            <p>
              Esta vista muestra todas las entidades conocidas que han sido
              ingresadas en el sistema. Puedes buscar por nombre o filtrar por
              tipo de entidad. El número de referencias indica cuántas veces
              aparece cada entidad en los datos procesados.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnownEntitiesView;
