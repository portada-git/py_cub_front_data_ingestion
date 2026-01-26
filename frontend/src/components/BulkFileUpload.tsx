/**
 * Unified File Upload Component
 * Handles both single and multiple file uploads with batch processing, queue management, and real-time monitoring
 * Integrado con el sistema de monitoreo persistente
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useDropzone } from 'react-dropzone';
import { Link, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle, 
  FolderOpen,
  Play,
  ExternalLink,
  ArrowRight
} from 'lucide-react';
import { clsx } from 'clsx';
import { apiService } from '../services/api';
import { IngestionResponse } from '../types';
import { useUploadIntegration } from '../hooks/useUploadIntegration';
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
  uploadId?: string; // ID en el store persistente
}

interface UnifiedUploadStats {
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

interface UnifiedFileUploadProps {
  ingestionType: 'extraction_data' | 'known_entities';
  publication?: string;
  entityName?: string;
  maxConcurrentUploads?: number;
  maxRetries?: number;
  onUploadComplete?: (stats: UnifiedUploadStats) => void;
  onFileProcessed?: (file: FileUploadItem) => void;
}

const UnifiedFileUpload: React.FC<UnifiedFileUploadProps> = ({
  ingestionType,
  publication,
  entityName,
  maxConcurrentUploads = 5,
  maxRetries = 3,
  onUploadComplete,
  onFileProcessed
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [files, setFiles] = useState<FileUploadItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const activeUploadsRef = useRef<Set<string>>(new Set());
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map());
  
  // Integration with persistent upload store
  const { createUploadHandler } = useUploadIntegration({
    ingestionType,
    publication,
    entityName
  });

  // Calculate stats whenever files change
  useEffect(() => {
    // Calculate stats whenever files change
    const newStats: UnifiedUploadStats = {
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
  }, [files, maxConcurrentUploads]);

  // Separate effect for completion callback to avoid infinite loops
  useEffect(() => {
    if (stats.total > 0 && (stats.success + stats.error) === stats.total) {
      onUploadComplete?.(stats);
    }
  }, [stats.success, stats.error, stats.total, onUploadComplete]);

  const generateFileId = () => Math.random().toString(36).substr(2, 9);

  const validateFile = (file: File): string | null => {
    const maxSize = 50 * 1024 * 1024; // 50MB per file
    if (file.size > maxSize) {
      return t('notifications.fileTooLarge', { filename: file.name });
    }

    const validExtensions = ['.json'];
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(extension)) {
      return t('notifications.invalidFormat', { filename: file.name });
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
        errors.push(t('notifications.duplicateFile', { filename: file.name }));
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
      console.warn(t('notifications.filesRejected'), errors);
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

      // Use integrated upload handler that connects to persistent store
      const uploadHandler = createUploadHandler(async (file, onProgress) => {
        return await apiService.uploadFile(
          file,
          ingestionType,
          publication,
          entityName,
          undefined,
          onProgress
        );
      });

      const uploadId = await uploadHandler(fileItem.file);

      // Mark as uploaded and processing - the persistent store will handle status updates
      setFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { 
              ...f, 
              status: 'success', // Local success - file uploaded
              progress: 100,
              uploadEndTime: Date.now(),
              uploadId // Store the persistent upload ID for reference
            }
          : f
      ));
      
      onFileProcessed?.(fileItem);

    } catch (error) {
      let errorMessage = t('notifications.unknownError');
      
      if (error instanceof Error) {
        // Handle structured error responses from backend
        const apiError = error as any;
        if (apiError.details && apiError.details.error_code) {
          switch (apiError.details.error_code) {
            case 'PUBLICATION_REQUIRED':
              errorMessage = t('notifications.publicationRequired');
              break;
            case 'FILE_VALIDATION_ERROR':
              errorMessage = apiError.details.errors ? 
                apiError.details.errors.join('. ') : 
                t('notifications.invalidFormat', { filename: fileItem.file.name });
              break;
            case 'VALIDATION_ERROR':
              errorMessage = apiError.details.errors ? 
                apiError.details.errors.join('. ') : 
                t('notifications.validationError');
              break;
            default:
              errorMessage = apiError.details.message || error.message;
          }
        } else if (error.message.includes('Publication is required')) {
          errorMessage = t('notifications.publicationRequired');
        } else if (error.message.includes('validation error')) {
          errorMessage = t('notifications.validationError');
        } else {
          errorMessage = error.message;
        }
      }
      
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
          'upload-zone border-2 border-dashed rounded-xl p-8 text-center cursor-pointer',
          {
            'drag-active': isDragActive,
            'border-gray-300': !isDragActive && !isProcessing,
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
            ? t('ingestion.dragFilesActive')
            : t('ingestion.fileUpload')
          }
        </h3>
        <p className="text-gray-600 mb-4">
          {t('ingestion.dragFiles')}
        </p>
        {ingestionType === 'extraction_data' && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              💡 La publicación se extrae automáticamente de los datos JSON. Puedes seleccionar una publicación específica si deseas sobrescribir esta información.
            </p>
          </div>
        )}
        <div className="flex justify-center space-x-6 text-sm text-gray-500">
          <span>• {t('ingestion.multipleFiles')}</span>
          <span>• {t('ingestion.maxFileSize')}</span>
          <span>• {t('ingestion.parallelProcessing')}</span>
        </div>
      </div>

      {/* Statistics Dashboard */}
      {files.length > 0 && (
        <div className="card-dark">
          <div className="card-header-dark">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              {t('ingestion.statistics')}
            </h3>
            <div className="flex space-x-2">
              <Link
                to="/processes"
                className="btn btn-secondary"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Ver Dashboard Completo
              </Link>
              
              {!isProcessing ? (
                <button
                  onClick={startProcessing}
                  disabled={stats.pending === 0}
                  className="btn btn-success"
                >
                  <Play className="w-4 h-4 mr-2" />
                  {t('ingestion.startProcessing')}
                </button>
              ) : isPaused ? (
                <button
                  onClick={resumeProcessing}
                  className="btn btn-primary"
                >
                  <Play className="w-4 h-4 mr-2" />
                  {t('ingestion.resumeProcessing')}
                </button>
              ) : (
                <button
                  onClick={pauseProcessing}
                  className="btn btn-warning"
                >
                  <Pause className="w-4 h-4 mr-2" />
                  {t('ingestion.pauseProcessing')}
                </button>
              )}
              
              {stats.error > 0 && (
                <button
                  onClick={retryFailed}
                  className="btn btn-warning"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  {t('ingestion.retryErrors')}
                </button>
              )}
              
              <button
                onClick={clearAll}
                className="btn btn-danger"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                {t('ingestion.clearAll')}
              </button>
            </div>
          </div>

          {/* Progress Overview */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <div className="stat-card stat-card-primary">
              <div className="stat-number stat-number-primary">{stats.total}</div>
              <div className="stat-label text-slate-400">{t('ingestion.total')}</div>
            </div>
            <div className="stat-card stat-card-warning">
              <div className="stat-number stat-number-warning">{stats.pending}</div>
              <div className="stat-label text-slate-400">{t('ingestion.pending')}</div>
            </div>
            <div className="stat-card stat-card-info">
              <div className="stat-number stat-number-info">{stats.uploading}</div>
              <div className="stat-label text-slate-400">{t('ingestion.uploading_status')}</div>
            </div>
            <div className="stat-card stat-card-success">
              <div className="stat-number stat-number-success">{stats.success}</div>
              <div className="stat-label text-slate-400">{t('ingestion.success')}</div>
            </div>
            <div className="stat-card stat-card-error">
              <div className="stat-number stat-number-error">{stats.error}</div>
              <div className="stat-label text-slate-400">{t('ingestion.errors')}</div>
            </div>
            <div className="stat-card stat-card-info">
              <div className="stat-number stat-number-info">{stats.totalRecordsProcessed.toLocaleString()}</div>
              <div className="stat-label text-slate-400">{t('ingestion.records')}</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-slate-400 mb-2">
              <span>{t('ingestion.generalProgress')}</span>
              <span>{Math.round((stats.success / stats.total) * 100)}%</span>
            </div>
            <div className="progress-bar bg-slate-800">
              <div
                className="progress-fill progress-fill-success"
                style={{ width: `${(stats.success / stats.total) * 100}%` }}
              />
            </div>
          </div>

          {/* Time Estimates */}
          {stats.averageUploadTime > 0 && (
            <div className="flex justify-between text-sm text-slate-400">
              <span className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {t('ingestion.averageTime')}: {formatTime(stats.averageUploadTime)}
              </span>
              {stats.estimatedTimeRemaining > 0 && (
                <span className="flex items-center">
                  <Zap className="w-4 h-4 mr-1" />
                  {t('ingestion.estimatedRemaining')}: {formatTime(stats.estimatedTimeRemaining)}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Global Monitoring Info */}
      {files.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <BarChart3 className="w-5 h-5 text-blue-600 mt-0.5" />
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-900">
                Monitoreo Global Activo
              </h4>
              <p className="text-sm text-blue-700 mt-1">
                Los archivos subidos se procesan en segundo plano y se pueden monitorear desde cualquier vista. 
                Usa el <strong>monitor flotante</strong> (esquina inferior derecha) o el <strong>Dashboard de Procesos</strong> 
                para seguimiento completo.
              </p>
              <div className="mt-2">
                <Link
                  to="/processes"
                  className="text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  Ver Dashboard de Procesos →
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="table-container">
          <div className="table-header">
            <h3 className="font-semibold text-gray-900">
              {t('ingestion.filesList')} ({files.length})
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
                          {fileItem.status === 'pending' && t('ingestion.pending_status')}
                          {fileItem.status === 'uploading' && t('ingestion.uploading_status')}
                          {fileItem.status === 'success' && t('ingestion.success_status')}
                          {fileItem.status === 'error' && t('ingestion.error_status')}
                          {fileItem.status === 'paused' && 'Pausado'}
                        </span>
                        {fileItem.result?.records_processed && (
                          <span>{fileItem.result.records_processed} {t('ingestion.records').toLowerCase()}</span>
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
                      title={t('ingestion.removeFile')}
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

export default UnifiedFileUpload;