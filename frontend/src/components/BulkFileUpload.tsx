/**
 * Bulk File Upload Component
 * Handles massive file uploads with batch processing, queue management, and real-time monitoring
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Pause, 
  Play, 
  RotateCcw,
  Trash2,
  FolderOpen,
  BarChart3,
  Clock,
  Zap
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiService } from '../services/api';
import { withErrorHandling } from '../utils/apiErrorHandler';
import { IngestionResponse } from '../types';
import LoadingSpinner from './LoadingSpinner';

interface FileUploadItem {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'paused';
  progress: number;
  result?: IngestionResponse;
  error?: string;
  retryCount: number;
  uploadStartTime?: number;
  uploadEndTime?: number;
}

interface BulkUploadStats {
  total: number;
  pending: number;
  uploading: number;
  success: number;
  error: number;
  paused: number;
  totalRecordsProcessed: number;
  averageUploadTime: number;
  estimatedTimeRemaining: number;
}

interface BulkFileUploadProps {
  ingestionType: 'extraction_data' | 'known_entities';
  publication?: string;
  entityName?: string;
  maxConcurrentUploads?: number;
  maxRetries?: number;
  onUploadComplete?: (stats: BulkUploadStats) => void;
  onFileProcessed?: (file: FileUploadItem) => void;
}

const BulkFileUpload: React.FC<BulkFileUploadProps> = ({
  ingestionType,
  publication,
  entityName,
  maxConcurrentUploads = 5,
  maxRetries = 3,
  onUploadComplete,
  onFileProcessed
}) => {
  const [files, setFiles] = useState<FileUploadItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [stats, setStats] = useState<BulkUploadStats>({
    total: 0,
    pending: 0,
    uploading: 0,
    success: 0,
    error: 0,
    paused: 0,
    totalRecordsProcessed: 0,
    averageUploadTime: 0,
    estimatedTimeRemaining: 0
  });

  const activeUploadsRef = useRef<Set<string>>(new Set());
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map());

  // Calculate stats whenever files change
  useEffect(() => {
    // Calculate stats whenever files change
    const newStats: BulkUploadStats = {
      total: files.length,
      pending: files.filter(f => f.status === 'pending').length,
      uploading: files.filter(f => f.status === 'uploading').length,
      success: files.filter(f => f.status === 'success').length,
      error: files.filter(f => f.status === 'error').length,
      paused: files.filter(f => f.status === 'paused').length,
      totalRecordsProcessed: files.reduce((sum, f) => sum + (f.result?.records_processed || 0), 0),
      averageUploadTime: 0,
      estimatedTimeRemaining: 0
    };

    // Calculate average upload time
    const completedFiles = files.filter(f => f.uploadStartTime && f.uploadEndTime);
    if (completedFiles.length > 0) {
      const totalTime = completedFiles.reduce((sum, f) => 
        sum + (f.uploadEndTime! - f.uploadStartTime!), 0
      );
      newStats.averageUploadTime = totalTime / completedFiles.length;
      
      // Estimate remaining time
      const remainingFiles = newStats.pending + newStats.uploading;
      newStats.estimatedTimeRemaining = (remainingFiles * newStats.averageUploadTime) / maxConcurrentUploads;
    }

    setStats(newStats);
    
    // Call onUploadComplete when all files are processed
    if (newStats.total > 0 && (newStats.success + newStats.error) === newStats.total) {
      onUploadComplete?.(newStats);
    }
  }, [files, maxConcurrentUploads, onUploadComplete]);

  const generateFileId = () => Math.random().toString(36).substr(2, 9);

  const validateFile = (file: File): string | null => {
    const maxSize = 50 * 1024 * 1024; // 50MB per file
    if (file.size > maxSize) {
      return `Archivo demasiado grande: ${file.name}`;
    }

    const validExtensions = ['.json'];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(extension)) {
      return `Formato no válido: ${file.name}`;
    }

    return null;
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: FileUploadItem[] = [];
    const errors: string[] = [];

    acceptedFiles.forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(error);
        return;
      }

      // Check for duplicates
      const isDuplicate = files.some(f => f.file.name === file.name && f.file.size === file.size);
      if (isDuplicate) {
        errors.push(`Archivo duplicado: ${file.name}`);
        return;
      }

      newFiles.push({
        id: generateFileId(),
        file,
        status: 'pending',
        progress: 0,
        retryCount: 0
      });
    });

    if (errors.length > 0) {
      console.warn('Archivos rechazados:', errors);
    }

    setFiles(prev => [...prev, ...newFiles]);
  }, [files]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      'application/json': ['.json']
    },
    disabled: isProcessing && !isPaused
  });

  const uploadFile = async (fileItem: FileUploadItem): Promise<void> => {
    const controller = new AbortController();
    abortControllersRef.current.set(fileItem.id, controller);

    try {
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'uploading', uploadStartTime: Date.now() }
          : f
      ));

      const result = await withErrorHandling(async () => {
        return await apiService.uploadFile(
          fileItem.file,
          ingestionType,
          publication,
          entityName,
          undefined,
          (progress) => {
            setFiles(prev => prev.map(f => 
              f.id === fileItem.id ? { ...f, progress } : f
            ));
          }
        );
      });

      if (result) {
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { 
                ...f, 
                status: 'success', 
                progress: 100, 
                result,
                uploadEndTime: Date.now()
              }
            : f
        ));
        onFileProcessed?.(fileItem);
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { 
              ...f, 
              status: 'error', 
              error: errorMessage,
              uploadEndTime: Date.now()
            }
            : f
      ));
    } finally {
      abortControllersRef.current.delete(fileItem.id);
      activeUploadsRef.current.delete(fileItem.id);
    }
  };

  const processQueue = useCallback(async () => {
    if (isPaused || activeUploadsRef.current.size >= maxConcurrentUploads) {
      return;
    }

    const pendingFiles = files.filter(f => 
      f.status === 'pending' && !activeUploadsRef.current.has(f.id)
    );

    const filesToProcess = pendingFiles.slice(0, maxConcurrentUploads - activeUploadsRef.current.size);

    for (const file of filesToProcess) {
      activeUploadsRef.current.add(file.id);
      uploadFile(file);
    }
  }, [files, isPaused, maxConcurrentUploads, uploadFile]);

  useEffect(() => {
    if (isProcessing && !isPaused) {
      processQueue();
    }
  }, [isProcessing, isPaused, files, processQueue]);

  const startProcessing = () => {
    setIsProcessing(true);
    setIsPaused(false);
  };

  const pauseProcessing = () => {
    setIsPaused(true);
    // Cancel active uploads
    abortControllersRef.current.forEach(controller => controller.abort());
    abortControllersRef.current.clear();
    activeUploadsRef.current.clear();
    
    // Set uploading files back to pending
    setFiles(prev => prev.map(f => 
      f.status === 'uploading' ? { ...f, status: 'pending', progress: 0 } : f
    ));
  };

  const resumeProcessing = () => {
    setIsPaused(false);
  };

  const stopProcessing = () => {
    setIsProcessing(false);
    setIsPaused(false);
    pauseProcessing();
  };

  const retryFailed = () => {
    setFiles(prev => prev.map(f => 
      f.status === 'error' && f.retryCount < maxRetries
        ? { ...f, status: 'pending', error: undefined, retryCount: f.retryCount + 1 }
        : f
    ));
  };

  const removeFile = (id: string) => {
    // Cancel upload if active
    const controller = abortControllersRef.current.get(id);
    if (controller) {
      controller.abort();
      abortControllersRef.current.delete(id);
    }
    activeUploadsRef.current.delete(id);
    
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const clearAll = () => {
    stopProcessing();
    setFiles([]);
  };

  const formatTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className="space-y-6">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
          {
            'border-blue-400 bg-blue-50': isDragActive,
            'border-gray-300 hover:border-gray-400 hover:bg-gray-50': !isDragActive && !isProcessing,
            'border-gray-200 bg-gray-100 cursor-not-allowed': isProcessing && !isPaused
          }
        )}
      >
        <input {...getInputProps()} />
        <FolderOpen className={clsx(
          'w-16 h-16 mx-auto mb-4',
          isDragActive ? 'text-blue-500' : 'text-gray-400'
        )} />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {isDragActive 
            ? 'Suelta los archivos aquí' 
            : 'Carga Masiva de Archivos JSON'
          }
        </h3>
        <p className="text-gray-600 mb-4">
          Arrastra múltiples archivos JSON o haz clic para seleccionar
        </p>
        <div className="flex justify-center space-x-6 text-sm text-gray-500">
          <span>• Hasta 500+ archivos</span>
          <span>• Máximo 50MB por archivo</span>
          <span>• Procesamiento en paralelo</span>
        </div>
      </div>

      {/* Statistics Dashboard */}
      {files.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Estadísticas de Procesamiento
            </h3>
            <div className="flex space-x-2">
              {!isProcessing ? (
                <button
                  onClick={startProcessing}
                  disabled={stats.pending === 0}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Iniciar Procesamiento
                </button>
              ) : isPaused ? (
                <button
                  onClick={resumeProcessing}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Reanudar
                </button>
              ) : (
                <button
                  onClick={pauseProcessing}
                  className="flex items-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-500 transition-colors"
                >
                  <Pause className="w-4 h-4 mr-2" />
                  Pausar
                </button>
              )}
              
              {stats.error > 0 && (
                <button
                  onClick={retryFailed}
                  className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-500 transition-colors"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reintentar Errores
                </button>
              )}
              
              <button
                onClick={clearAll}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Limpiar Todo
              </button>
            </div>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{stats.total}</div>
              <div className="text-sm text-slate-400">Total</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{stats.pending}</div>
              <div className="text-sm text-slate-400">Pendientes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{stats.uploading}</div>
              <div className="text-sm text-slate-400">Subiendo</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{stats.success}</div>
              <div className="text-sm text-slate-400">Exitosos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{stats.error}</div>
              <div className="text-sm text-slate-400">Errores</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-cyan-400">{stats.totalRecordsProcessed.toLocaleString()}</div>
              <div className="text-sm text-slate-400">Registros</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-slate-400 mb-2">
              <span>Progreso General</span>
              <span>{Math.round((stats.success / stats.total) * 100)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full transition-all duration-300"
                style={{ width: `${(stats.success / stats.total) * 100}%` }}
              />
            </div>
          </div>

          {/* Time Estimates */}
          {stats.averageUploadTime > 0 && (
            <div className="flex justify-between text-sm text-slate-400">
              <span className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                Tiempo promedio: {formatTime(stats.averageUploadTime)}
              </span>
              {stats.estimatedTimeRemaining > 0 && (
                <span className="flex items-center">
                  <Zap className="w-4 h-4 mr-1" />
                  Tiempo estimado restante: {formatTime(stats.estimatedTimeRemaining)}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h3 className="font-semibold text-gray-900">
              Lista de Archivos ({files.length})
            </h3>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {files.map((fileItem) => (
              <div
                key={fileItem.id}
                className="p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1 min-w-0">
                    <FileText className={clsx(
                      'w-8 h-8 mr-3 flex-shrink-0',
                      {
                        'text-gray-400': fileItem.status === 'pending',
                        'text-blue-500': fileItem.status === 'uploading',
                        'text-green-500': fileItem.status === 'success',
                        'text-red-500': fileItem.status === 'error',
                        'text-yellow-500': fileItem.status === 'paused'
                      }
                    )} />
                    
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {fileItem.file.name}
                      </p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{formatFileSize(fileItem.file.size)}</span>
                        <span className={clsx(
                          'px-2 py-1 rounded-full text-xs font-medium',
                          {
                            'bg-gray-100 text-gray-600': fileItem.status === 'pending',
                            'bg-blue-100 text-blue-600': fileItem.status === 'uploading',
                            'bg-green-100 text-green-600': fileItem.status === 'success',
                            'bg-red-100 text-red-600': fileItem.status === 'error',
                            'bg-yellow-100 text-yellow-600': fileItem.status === 'paused'
                          }
                        )}>
                          {fileItem.status === 'pending' && 'Pendiente'}
                          {fileItem.status === 'uploading' && 'Subiendo'}
                          {fileItem.status === 'success' && 'Exitoso'}
                          {fileItem.status === 'error' && 'Error'}
                          {fileItem.status === 'paused' && 'Pausado'}
                        </span>
                        {fileItem.result?.records_processed && (
                          <span>{fileItem.result.records_processed} registros</span>
                        )}
                      </div>
                      
                      {/* Progress Bar for uploading files */}
                      {fileItem.status === 'uploading' && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${fileItem.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {/* Error Message */}
                      {fileItem.error && (
                        <p className="mt-1 text-sm text-red-600">{fileItem.error}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    {fileItem.status === 'uploading' && (
                      <LoadingSpinner size="sm" />
                    )}
                    {fileItem.status === 'success' && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {fileItem.status === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    
                    <button
                      onClick={() => removeFile(fileItem.id)}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      title="Eliminar archivo"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkFileUpload;