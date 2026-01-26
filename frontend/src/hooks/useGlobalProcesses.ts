/**
 * Hook para sincronizar procesos globalmente entre todos los usuarios
 * Combina el store local con datos del servidor
 */

import { useEffect, useCallback, useRef } from 'react';
import { useUploadStore } from '../store/useUploadStore';
import { apiService } from '../services/api';

interface GlobalProcess {
  task_id: string;
  file_name: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  message: string;
  records_processed: number;
  user_id: string;
  user_name: string;
  started_at: string;
  updated_at: string;
}

export const useGlobalProcesses = () => {
  const { tasks, addTask, updateTask, removeTask } = useUploadStore();
  const syncIntervalRef = useRef<number>();
  
  // Sync with server every 5 seconds
  const syncWithServer = useCallback(async () => {
    try {
      console.log('[GlobalProcesses] Syncing with server...');
      
      // Get all active tasks from server
      const response: any = await apiService.getIngestionTasks('active');
      const serverTasks: GlobalProcess[] = response.data || [];
      
      console.log('[GlobalProcesses] Server tasks:', serverTasks);
      
      // Update or add tasks from server
      serverTasks.forEach(serverTask => {
        const existingTask = tasks.find(t => t.taskId === serverTask.task_id);
        
        if (existingTask) {
          // Update existing task
          updateTask(existingTask.id, {
            status: serverTask.status as any,
            progress: serverTask.progress_percentage,
            message: serverTask.message,
            recordsProcessed: serverTask.records_processed
          });
        } else {
          // Add new task from server (from other users)
          addTask({
            taskId: serverTask.task_id,
            fileName: serverTask.file_name,
            fileSize: serverTask.file_size,
            status: serverTask.status as any,
            progress: serverTask.progress_percentage,
            message: `${serverTask.message} (Usuario: ${serverTask.user_name})`,
            ingestionType: 'extraction_data', // Default, could be enhanced
            recordsProcessed: serverTask.records_processed,
            maxRetries: 3
          });
        }
      });
      
      // Remove completed tasks older than 1 hour
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
      tasks.forEach(task => {
        if (task.status === 'completed' && task.endTime && task.endTime < oneHourAgo) {
          removeTask(task.id);
        }
      });
      
    } catch (error) {
      console.error('[GlobalProcesses] Error syncing with server:', error);
    }
  }, [tasks, addTask, updateTask, removeTask]);
  
  // Start syncing when there are active tasks
  useEffect(() => {
    const activeTasks = tasks.filter(t => 
      ['pending', 'uploading', 'processing'].includes(t.status)
    );
    
    if (activeTasks.length > 0) {
      console.log('[GlobalProcesses] Starting sync - active tasks:', activeTasks.length);
      
      // Initial sync
      syncWithServer();
      
      // Set up interval
      syncIntervalRef.current = window.setInterval(syncWithServer, 5000);
    } else {
      console.log('[GlobalProcesses] Stopping sync - no active tasks');
      
      if (syncIntervalRef.current) {
        window.clearInterval(syncIntervalRef.current);
        syncIntervalRef.current = undefined;
      }
    }
    
    return () => {
      if (syncIntervalRef.current) {
        window.clearInterval(syncIntervalRef.current);
      }
    };
  }, [tasks.length, syncWithServer]);
  
  return {
    syncWithServer,
    isGlobalSyncActive: !!syncIntervalRef.current
  };
};