/**
 * Hook para integrar uploads con el store persistente
 * Conecta los componentes de upload con el sistema de monitoreo global
 */

import { useCallback } from 'react';
import { useUploadStore } from '../store/useUploadStore';
import { useNotificationStore } from '../store/useStore';
import { IngestionResponse } from '../types';

interface UseUploadIntegrationProps {
  ingestionType: 'extraction_data' | 'known_entities';
  publication?: string;
  entityName?: string;
}

export const useUploadIntegration = ({
  ingestionType,
  publication,
  entityName
}: UseUploadIntegrationProps) => {
  const { addTask, updateTask, getTask } = useUploadStore();
  const { addNotification } = useNotificationStore();
  
  // Register a new upload task
  const registerUpload = useCallback((
    file: File,
    taskId: string
  ): string => {
    const uploadId = addTask({
      taskId,
      fileName: file.name,
      fileSize: file.size,
      status: 'uploading',
      progress: 0,
      message: 'Subiendo archivo...',
      ingestionType,
      publication,
      entityName,
      maxRetries: 3
    });
    
    addNotification({
      type: 'info',
      title: 'Upload iniciado',
      message: `Procesando ${file.name}...`
    });
    
    return uploadId;
  }, [addTask, addNotification, ingestionType, publication, entityName]);
  
  // Update upload progress
  const updateUploadProgress = useCallback((
    uploadId: string,
    progress: number,
    message?: string
  ) => {
    updateTask(uploadId, {
      progress,
      message: message || `Subiendo... ${progress}%`
    });
  }, [updateTask]);
  
  // Handle upload completion
  const handleUploadComplete = useCallback((
    uploadId: string,
    result: IngestionResponse
  ) => {
    updateTask(uploadId, {
      status: 'processing',
      progress: 100,
      message: 'Archivo subido, procesando...',
      recordsProcessed: result.records_processed
    });
  }, [updateTask]);
  
  // Handle upload error
  const handleUploadError = useCallback((
    uploadId: string,
    error: string
  ) => {
    updateTask(uploadId, {
      status: 'failed',
      progress: 0,
      message: 'Error en la subida',
      error,
      endTime: new Date()
    });
    
    const task = getTask(uploadId);
    if (task) {
      addNotification({
        type: 'error',
        title: 'Error en upload',
        message: `${task.fileName}: ${error}`
      });
    }
  }, [updateTask, getTask, addNotification]);
  
  // Create integrated upload handler
  const createUploadHandler = useCallback((
    uploadFunction: (file: File, onProgress?: (progress: number) => void) => Promise<IngestionResponse>
  ) => {
    return async (file: File): Promise<string> => {
      let uploadId: string | null = null;
      
      try {
        // Start upload
        const result = await uploadFunction(file, (progress) => {
          if (uploadId) {
            updateUploadProgress(uploadId, progress);
          }
        });
        
        // Register task after getting taskId
        uploadId = registerUpload(file, result.task_id);
        
        // Handle completion
        handleUploadComplete(uploadId, result);
        
        return uploadId;
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
        
        if (uploadId) {
          handleUploadError(uploadId, errorMessage);
        } else {
          // If we couldn't register the task, show notification directly
          addNotification({
            type: 'error',
            title: 'Error en upload',
            message: `${file.name}: ${errorMessage}`
          });
        }
        
        throw error;
      }
    };
  }, [registerUpload, updateUploadProgress, handleUploadComplete, handleUploadError, addNotification]);
  
  return {
    registerUpload,
    updateUploadProgress,
    handleUploadComplete,
    handleUploadError,
    createUploadHandler
  };
};