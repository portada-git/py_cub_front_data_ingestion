/**
 * API service for PortAda backend integration
 * Modern implementation with proper error handling and TypeScript support
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
  PendingFilesResponse,
  KnownEntitiesResponse,
  DailyEntriesRequest,
  DailyEntriesResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';

class ApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = API_BASE_URL;
    // Load token from localStorage on initialization
    this.token = localStorage.getItem('access_token');
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

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid, clear it
          this.clearToken();
          throw new Error('Authentication required');
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
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
    dataPathDeltaLake?: string
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

    return this.request<IngestionResponse>('/ingestion/upload', {
      method: 'POST',
      headers: {
        // Don't set Content-Type for FormData, let browser set it
        'Authorization': this.token ? `Bearer ${this.token}` : '',
      },
      body: formData,
    });
  }

  async getIngestionStatus(taskId: string): Promise<IngestionStatusResponse> {
    return this.request<IngestionStatusResponse>(`/ingestion/status/${taskId}`);
  }

  async getIngestionTasks(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request(`/ingestion/tasks${params}`);
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
  async getPendingFiles(publication?: string, username?: string): Promise<PendingFilesResponse> {
    const params = new URLSearchParams();
    if (publication) params.append('publication', publication);
    if (username) params.append('username', username);
    
    const queryString = params.toString();
    return this.request<PendingFilesResponse>(`/analysis/pending-files${queryString ? '?' + queryString : ''}`);
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

  async analyzeMissingDatesFile(file: File): Promise<MissingDatesResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<MissingDatesResponse>('/analysis/missing-dates', {
      method: 'POST',
      headers: {
        'Authorization': this.token ? `Bearer ${this.token}` : '',
      },
      body: formData,
    });
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

  async uploadDatesFile(file: File, publicationName: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('publication_name', publicationName);

    return this.request('/analysis/missing-dates/upload', {
      method: 'POST',
      headers: {
        'Authorization': this.token ? `Bearer ${this.token}` : '',
      },
      body: formData,
    });
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