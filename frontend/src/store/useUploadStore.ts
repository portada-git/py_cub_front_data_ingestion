/**
 * Upload Store - Gestión persistente de uploads y procesos en segundo plano
 * Mantiene el estado de todos los uploads activos, completados y fallidos
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UploadTask {
  id: string;
  taskId: string;
  fileName: string;
  fileSize: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message: string;
  ingestionType: 'extraction_data' | 'known_entities';
  publication?: string;
  entityName?: string;
  recordsProcessed?: number;
  estimatedTotal?: number;
  startTime: Date;
  endTime?: Date;
  error?: string;
  retryCount: number;
  maxRetries: number;
}

export interface UploadStats {
  totalTasks: number;
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalRecordsProcessed: number;
  averageProcessingTime: number;
}

interface UploadState {
  tasks: UploadTask[];
  isPolling: boolean;
  pollInterval: number;
  
  // Actions
  addTask: (task: Omit<UploadTask, 'id' | 'startTime' | 'retryCount'>) => string;
  updateTask: (id: string, updates: Partial<UploadTask>) => void;
  removeTask: (id: string) => void;
  clearCompletedTasks: () => void;
  clearAllTasks: () => void;
  retryTask: (id: string) => void;
  cancelTask: (id: string) => void;
  
  // Getters
  getTask: (id: string) => UploadTask | undefined;
  getTaskByTaskId: (taskId: string) => UploadTask | undefined;
  getActiveTasks: () => UploadTask[];
  getCompletedTasks: () => UploadTask[];
  getFailedTasks: () => UploadTask[];
  getStats: () => UploadStats;
  
  // Polling control
  startPolling: () => void;
  stopPolling: () => void;
  setPollInterval: (interval: number) => void;
}

export const useUploadStore = create<UploadState>()(
  persist(
    (set, get) => ({
      tasks: [],
      isPolling: false,
      pollInterval: 3000, // 3 seconds
      
      addTask: (taskData) => {
        const id = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const task: UploadTask = {
          ...taskData,
          id,
          startTime: new Date(),
          retryCount: 0,
          maxRetries: 3,
        };
        
        set((state) => ({
          tasks: [...state.tasks, task]
        }));
        
        return id;
      },
      
      updateTask: (id, updates) => {
        set((state) => ({
          tasks: state.tasks.map(task => 
            task.id === id 
              ? { 
                  ...task, 
                  ...updates,
                  // Set end time if status is final
                  endTime: ['completed', 'failed', 'cancelled'].includes(updates.status || task.status) 
                    ? updates.endTime || new Date() 
                    : task.endTime
                }
              : task
          )
        }));
      },
      
      removeTask: (id) => {
        set((state) => ({
          tasks: state.tasks.filter(task => task.id !== id)
        }));
      },
      
      clearCompletedTasks: () => {
        set((state) => ({
          tasks: state.tasks.filter(task => 
            !['completed', 'failed', 'cancelled'].includes(task.status)
          )
        }));
      },
      
      clearAllTasks: () => {
        set({ tasks: [] });
      },
      
      retryTask: (id) => {
        set((state) => ({
          tasks: state.tasks.map(task => 
            task.id === id 
              ? {
                  ...task,
                  status: 'pending' as const,
                  progress: 0,
                  message: 'Reintentando...',
                  error: undefined,
                  retryCount: task.retryCount + 1,
                  startTime: new Date(),
                  endTime: undefined
                }
              : task
          )
        }));
      },
      
      cancelTask: (id) => {
        set((state) => ({
          tasks: state.tasks.map(task => 
            task.id === id 
              ? {
                  ...task,
                  status: 'cancelled' as const,
                  message: 'Cancelado por el usuario',
                  endTime: new Date()
                }
              : task
          )
        }));
      },
      
      getTask: (id) => {
        return get().tasks.find(task => task.id === id);
      },
      
      getTaskByTaskId: (taskId) => {
        return get().tasks.find(task => task.taskId === taskId);
      },
      
      getActiveTasks: () => {
        return get().tasks.filter(task => 
          ['pending', 'uploading', 'processing'].includes(task.status)
        );
      },
      
      getCompletedTasks: () => {
        return get().tasks.filter(task => task.status === 'completed');
      },
      
      getFailedTasks: () => {
        return get().tasks.filter(task => 
          ['failed', 'cancelled'].includes(task.status)
        );
      },
      
      getStats: () => {
        const tasks = get().tasks;
        const completedTasks = tasks.filter(t => t.status === 'completed');
        
        let averageProcessingTime = 0;
        if (completedTasks.length > 0) {
          const totalTime = completedTasks.reduce((sum, task) => {
            if (task.startTime && task.endTime) {
              return sum + (task.endTime.getTime() - task.startTime.getTime());
            }
            return sum;
          }, 0);
          averageProcessingTime = totalTime / completedTasks.length;
        }
        
        return {
          totalTasks: tasks.length,
          activeTasks: tasks.filter(t => ['pending', 'uploading', 'processing'].includes(t.status)).length,
          completedTasks: completedTasks.length,
          failedTasks: tasks.filter(t => ['failed', 'cancelled'].includes(t.status)).length,
          totalRecordsProcessed: tasks.reduce((sum, t) => sum + (t.recordsProcessed || 0), 0),
          averageProcessingTime
        };
      },
      
      startPolling: () => {
        set({ isPolling: true });
      },
      
      stopPolling: () => {
        set({ isPolling: false });
      },
      
      setPollInterval: (interval) => {
        set({ pollInterval: interval });
      }
    }),
    {
      name: 'upload-storage',
      // Only persist essential data, not functions
      partialize: (state) => ({
        tasks: state.tasks.map(task => ({
          ...task,
          // Convert dates to strings for persistence
          startTime: task.startTime,
          endTime: task.endTime
        })),
        pollInterval: state.pollInterval
      }),
      // Rehydrate dates from strings
      onRehydrateStorage: () => (state) => {
        if (state?.tasks) {
          state.tasks = state.tasks.map(task => ({
            ...task,
            startTime: new Date(task.startTime),
            endTime: task.endTime ? new Date(task.endTime) : undefined
          }));
        }
      }
    }
  )
);