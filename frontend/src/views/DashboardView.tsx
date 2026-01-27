/**
 * Dashboard view component
 * Main overview of the system status and recent activities
 */

import React, { useEffect, useState } from 'react';
import { 
  Upload, 
  BarChart3, 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  TrendingUp,
  Database
} from 'lucide-react';
import { useAuthStore } from '../store/useStore';
import { apiService } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

interface DashboardStats {
  recentTasks: number;
  totalEntities: number;
  systemStatus: 'healthy' | 'warning' | 'error';
}

const DashboardView: React.FC = () => {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats>({
    recentTasks: 0,
    totalEntities: 0,
    systemStatus: 'healthy',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load dashboard statistics
      const [healthCheck, knownEntities] = await Promise.all([
        apiService.healthCheck().catch(() => ({ status: 'error' })),
        apiService.getKnownEntities().catch(() => ({ total_entities: 0 })),
      ]);

      setStats({
        recentTasks: 0, // This would come from a recent tasks endpoint
        totalEntities: knownEntities.total_entities || 0,
        systemStatus: healthCheck.status === 'healthy' ? 'healthy' : 'warning',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading dashboard data');
      setStats(prev => ({ ...prev, systemStatus: 'error' }));
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Sistema operativo';
      case 'warning':
        return 'Advertencias detectadas';
      case 'error':
        return 'Errores del sistema';
      default:
        return 'Estado desconocido';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Bienvenido, {user?.full_name || user?.username}. Aquí tienes un resumen del sistema.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* System Status */}
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {getStatusIcon(stats.systemStatus)}
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900">Estado del Sistema</p>
              <p className="text-xs text-gray-600">{getStatusText(stats.systemStatus)}</p>
            </div>
          </div>
        </div>

        {/* Total Entities */}
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Database className="w-5 h-5 text-green-500" />
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900">Entidades Conocidas</p>
              <p className="text-2xl font-bold text-green-600">{stats.totalEntities}</p>
            </div>
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="w-5 h-5 text-purple-500" />
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900">Tareas Recientes</p>
              <p className="text-2xl font-bold text-purple-600">{stats.recentTasks}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={() => window.location.href = '/ingestion'}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Upload className="w-6 h-6 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Subir Datos</p>
              <p className="text-sm text-gray-600">Cargar archivos de extracción o entidades</p>
            </div>
          </button>

          <button
            onClick={() => window.location.href = '/analysis/missing-dates'}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <BarChart3 className="w-6 h-6 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Analizar Fechas</p>
              <p className="text-sm text-gray-600">Buscar fechas faltantes en los datos</p>
            </div>
          </button>

          <button
            onClick={() => window.location.href = '/analysis/duplicates'}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FileText className="w-6 h-6 text-primary-600 mr-3" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Ver Duplicados</p>
              <p className="text-sm text-gray-600">Revisar registros duplicados</p>
            </div>
          </button>
        </div>
      </div>

      {/* System Information */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Información del Sistema</h2>
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Versión del Sistema</span>
            <span className="text-sm font-medium text-gray-900">1.0.0</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Usuario Actual</span>
            <span className="text-sm font-medium text-gray-900">{user?.username}</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Rol</span>
            <span className="text-sm font-medium text-gray-900">{user?.role}</span>
          </div>
          <div className="flex justify-between items-center py-2">
            <span className="text-sm text-gray-600">Última Actualización</span>
            <span className="text-sm font-medium text-gray-900">
              {new Date().toLocaleDateString('es-ES')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;