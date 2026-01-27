/**
 * Enhanced API service for PortAda backend integration
 * Features: error handling, request/response interceptors, retry logic, and TypeScript support
 */

import { 
  LoginRequest, 
  LoginResponse, 
  IngestionResponse, 
  IngestionStatusResponse,
  MissingDatesRequest,
  MissingDatesResponse,
  DuplicatesRequest,
  DuplicatesResponse,
  KnownEntitiesResponse,
  DailyEntriesRequest,
  DailyEntriesResponse,
  PublicationsResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';

// Types for interceptors
type RequestInterceptor = (config: RequestInit & { url: string }) => RequestInit & { url: string };
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;
type ErrorInterceptor = (error: Error) => Error | Promise<Error>;

interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryCondition?: (error: Error) => boolean;
}

interface ApiError extends Error {
  status?: number;
  code?: string;
  details?: any;
}

class ApiService {
  private baseUrl: string;
  private token: string | null = null;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];
  private retryConfig: RetryConfig = {
    maxRetries: 3,
    retryDelay: 1000,
    retryCondition: (error: ApiError) => {
      // Retry on network errors or 5xx server errors
      return !error.status || error.status >= 500;
    }
  };

  constructor() {
    this.baseUrl = API_BASE_URL;
    // Load token from localStorage on initialization
    this.token = localStorage.getItem('access_token');
    
    // Set up default interceptors
    this.setupDefaultInterceptors();
  }

  private setupDefaultInterceptors() {
    // Request interceptor for logging
    this.addRequestInterceptor((config) => {
      console.log(`[API] ${config.method || 'GET'} ${config.url}`);
      return config;
    });

    // Response interceptor for logging
    this.addResponseInterceptor((response) => {
      console.log(`[API] Response ${response.status} for ${response.url}`);
      return response;
    });

    // Error interceptor for enhanced error handling
    this.addErrorInterceptor((error: ApiError) => {
      console.error('[API] Error:', error.message, error.details);
      
      // Handle authentication errors globally
      if (error.status === 401) {
        console.warn('[API] Authentication failed - clearing token');
        this.clearToken();
        
        // Dispatch a custom event to notify components
        window.dispatchEvent(new CustomEvent('auth-error', { 
          detail: { error: error.message } 
        }));
      }
      
      return error;
    });
  }

  // Interceptor management
  addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor);
  }

  setRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config };
  }

  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private createApiError(message: string, status?: number, details?: any): ApiError {
    const error = new Error(message) as ApiError;
    error.status = status;
    error.details = details;
    return error;
  }

  private async executeWithRetry<T>(
    operation: () => Promise<T>,
    attempt: number = 1
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      const apiError = error as ApiError;
      
      // Apply error interceptors
      let processedError = apiError;
      for (const interceptor of this.errorInterceptors) {
        processedError = await interceptor(processedError);
      }

      // Check if we should retry
      if (
        attempt < this.retryConfig.maxRetries &&
        this.retryConfig.retryCondition?.(processedError)
      ) {
        console.log(`[API] Retrying request (attempt ${attempt + 1}/${this.retryConfig.maxRetries})`);
        await this.sleep(this.retryConfig.retryDelay * attempt);
        return this.executeWithRetry(operation, attempt + 1);
      }

      throw processedError;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    return this.executeWithRetry(async () => {
      const url = `${this.baseUrl}${endpoint}`;
      
      let config: RequestInit & { url: string } = {
        ...options,
        url,
        credentials: 'include', // IMPORTANT: Include cookies in requests
        headers: {
          ...this.getAuthHeaders(),
          ...options.headers,
        },
      };

      // Apply request interceptors
      for (const interceptor of this.requestInterceptors) {
        config = interceptor(config);
      }

      try {
        let response = await fetch(config.url, config);
        
        // Apply response interceptors
        for (const interceptor of this.responseInterceptors) {
          response = await interceptor(response);
        }
        
        if (!response.ok) {
          let errorData: any = {};
          try {
            errorData = await response.json();
          } catch {
            // Response is not JSON
          }

          if (response.status === 401) {
            // Token expired or invalid, clear it
            this.clearToken();
            throw this.createApiError('Authentication required', 401, errorData);
          }
          
          const message = errorData.detail || errorData.message || `HTTP error! status: ${response.status}`;
          throw this.createApiError(message, response.status, errorData);
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        } else {
          return {} as T;
        }
      } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
          // Network error
          throw this.createApiError('Network error: Unable to connect to server', undefined, error);
        }
        throw error;
      }
    });
  }

  // File upload with enhanced error handling
  private async uploadRequest<T>(
    endpoint: string,
    formData: FormData,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    return this.executeWithRetry(async () => {
      const url = `${this.baseUrl}${endpoint}`;
      
      let config: RequestInit & { url: string } = {
        method: 'POST',
        url,
        credentials: 'include', // IMPORTANT: Include cookies in requests
        headers: {
          // Don't set Content-Type for FormData, let browser set it
          'Authorization': this.token ? `Bearer ${this.token}` : '',
        },
        body: formData,
      };

      // Apply request interceptors (excluding Content-Type for FormData)
      for (const interceptor of this.requestInterceptors) {
        config = interceptor(config);
      }

      try {
        // Create XMLHttpRequest for progress tracking if callback provided
        if (onProgress) {
          return new Promise<T>((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (event) => {
              if (event.lengthComputable) {
                const progress = (event.loaded / event.total) * 100;
                onProgress(progress);
              }
            });

            xhr.addEventListener('load', async () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                try {
                  const result = JSON.parse(xhr.responseText);
                  resolve(result);
                } catch {
                  resolve({} as T);
                }
              } else {
                let errorData: any = {};
                try {
                  errorData = JSON.parse(xhr.responseText);
                } catch {
                  // Response is not JSON
                }
                
                if (xhr.status === 401) {
                  this.clearToken();
                  reject(this.createApiError('Authentication required', 401, errorData));
                } else {
                  const message = errorData.detail || errorData.message || `HTTP error! status: ${xhr.status}`;
                  reject(this.createApiError(message, xhr.status, errorData));
                }
              }
            });

            xhr.addEventListener('error', () => {
              reject(this.createApiError('Network error: Upload failed', undefined, xhr));
            });

            xhr.open('POST', config.url);
            if (config.headers && typeof config.headers === 'object') {
              Object.entries(config.headers).forEach(([key, value]) => {
                if (key !== 'Content-Type' && typeof value === 'string') {
                  xhr.setRequestHeader(key, value);
                }
              });
            }
            xhr.send(formData);
          });
        } else {
          // Use fetch for simple uploads without progress
          let response = await fetch(config.url, config);
          
          // Apply response interceptors
          for (const interceptor of this.responseInterceptors) {
            response = await interceptor(response);
          }
          
          if (!response.ok) {
            let errorData: any = {};
            try {
              errorData = await response.json();
            } catch {
              // Response is not JSON
            }

            if (response.status === 401) {
              this.clearToken();
              throw this.createApiError('Authentication required', 401, errorData);
            }
            
            const message = errorData.detail || errorData.message || `HTTP error! status: ${response.status}`;
            throw this.createApiError(message, response.status, errorData);
          }

          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            return await response.json();
          } else {
            return {} as T;
          }
        }
      } catch (error) {
        if (error instanceof TypeError && error.message.includes('fetch')) {
          throw this.createApiError('Network error: Unable to connect to server', undefined, error);
        }
        throw error;
      }
    });
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    // Store the token
    this.setToken(response.access_token);
    
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', {
        method: 'POST',
      });
    } finally {
      // Always clear token, even if logout request fails
      this.clearToken();
    }
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Ingestion
  async uploadFile(
    file: File, 
    ingestionType: 'extraction_data' | 'known_entities',
    publication?: string,
    entityName?: string,
    dataPathDeltaLake?: string,
    onProgress?: (progress: number) => void
  ): Promise<IngestionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ingestion_type', ingestionType);
    
    if (publication) {
      formData.append('publication', publication);
    }
    if (entityName) {
      formData.append('entity_name', entityName);
    }
    if (dataPathDeltaLake) {
      formData.append('data_path_delta_lake', dataPathDeltaLake);
    }

    return this.uploadRequest<IngestionResponse>('/ingestion/upload', formData, onProgress);
  }

  async getIngestionStatus(taskId: string): Promise<IngestionStatusResponse> {
    return this.request<IngestionStatusResponse>(`/ingestion/status/${taskId}`);
  }

  async getIngestionTasks(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request(`/ingestion/tasks/global${params}`);
  }

  async cancelTask(taskId: string) {
    return this.request(`/ingestion/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async getProcessStatus() {
    return this.request('/ingestion/process-status');
  }

  // Analysis - Basic Queries
  async getPublications(): Promise<PublicationsResponse> {
    return this.request('/analysis/publications');
  }

  async getKnownEntities(): Promise<KnownEntitiesResponse> {
    return this.request<KnownEntitiesResponse>('/analysis/known-entities');
  }

  async getDailyEntries(request: DailyEntriesRequest): Promise<DailyEntriesResponse> {
    return this.request<DailyEntriesResponse>('/analysis/daily-entries', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Analysis - Missing Dates
  async getMissingDates(request: MissingDatesRequest): Promise<MissingDatesResponse> {
    return this.request<MissingDatesResponse>('/analysis/missing-dates', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async analyzeMissingDatesFile(file: File, onProgress?: (progress: number) => void): Promise<MissingDatesResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.uploadRequest<MissingDatesResponse>('/analysis/missing-dates', formData, onProgress);
  }

  async analyzeMissingDatesRange(request: {
    start_date: string;
    end_date: string;
    publication?: string;
  }): Promise<MissingDatesResponse> {
    return this.request<MissingDatesResponse>('/analysis/missing-dates', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async uploadDatesFile(file: File, publicationName: string, onProgress?: (progress: number) => void) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('publication_name', publicationName);

    return this.uploadRequest('/analysis/missing-dates/upload', formData, onProgress);
  }

  // Analysis - Duplicates
  async getDuplicates(request: DuplicatesRequest): Promise<DuplicatesResponse> {
    return this.request<DuplicatesResponse>('/analysis/duplicates', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getDuplicatesMetadata(request: {
    user?: string;
    publication?: string;
    start_date?: string;
    end_date?: string;
  }) {
    return this.request('/analysis/duplicates', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getDuplicateDetails(logId: string) {
    return this.request(`/analysis/duplicates/${logId}/details`);
  }

  // Analysis - Storage and Process Metadata
  async getStorageMetadata(request: any) {
    return this.request('/analysis/storage-metadata', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getFieldLineage(logId: string) {
    return this.request(`/analysis/storage-metadata/${logId}/lineage`);
  }

  async getProcessMetadata(request: any) {
    return this.request('/analysis/process-metadata', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Admin endpoints
  async cleanupFiles(maxAgeHours?: number) {
    const params = maxAgeHours ? `?max_age_hours=${maxAgeHours}` : '';
    return this.request(`/ingestion/cleanup${params}`, {
      method: 'POST',
    });
  }

  async listUploadFiles() {
    return this.request('/ingestion/files');
  }

  async cleanupTasks(maxAgeHours?: number) {
    const params = maxAgeHours ? `?max_age_hours=${maxAgeHours}` : '';
    return this.request(`/ingestion/tasks/cleanup${params}`, {
      method: 'POST',
    });
  }

  async getQueueStatus() {
    return this.request('/ingestion/queue-status');
  }

  // Health check
  async healthCheck() {
    return this.request<{status: string; service: string}>('/health');
  }
}

export const apiService = new ApiService();