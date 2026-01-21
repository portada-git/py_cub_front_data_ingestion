/**
 * API service for PortAda backend integration
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface IngestionResponse {
  success: boolean;
  message: string;
  task_id?: string;
  records_processed?: number;
}

export interface IngestionStatus {
  task_id: string;
  status: string;
  progress?: number;
  message?: string;
  records_processed?: number;
  error_details?: string;
}

export interface MissingDatesRequest {
  publication_name: string;
  query_mode: string;
  start_date?: string;
  end_date?: string;
  date_and_edition_list?: string;
}

export interface MissingDateEntry {
  date: string;
  edition: string;
  gap_duration?: string;
}

export interface MissingDatesResponse {
  success: boolean;
  publication_name: string;
  missing_dates: MissingDateEntry[];
  total_missing: number;
}

export interface DuplicatesRequest {
  user_responsible?: string;
  publication?: string;
  start_date?: string;
  end_date?: string;
}

export interface DuplicateRecord {
  log_id: string;
  date: string;
  edition: string;
  publication: string;
  uploaded_by: string;
  duplicate_count: number;
  duplicates_filter: string;
  duplicate_ids: string[];
}

export interface DuplicatesResponse {
  success: boolean;
  duplicates_metadata: DuplicateRecord[];
  total_records: number;
}

export interface StorageMetadataRequest {
  table_name?: string;
  process?: string;
}

export interface StorageRecord {
  log_id: string;
  table_name: string;
  process: string;
  timestamp: string;
  record_count: number;
  stage: number;
}

export interface StorageMetadataResponse {
  success: boolean;
  storage_records: StorageRecord[];
  total_records: number;
}

export interface ProcessMetadataRequest {
  process_name?: string;
}

export interface ProcessRecord {
  log_id: string;
  process: string;
  timestamp: string;
  duration?: number;
  status: string;
  records_processed: number;
  stage: number;
  error_message?: string;
}

export interface ProcessMetadataResponse {
  success: boolean;
  process_records: ProcessRecord[];
  total_records: number;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(username: string) {
    return this.request<{success: boolean; user: any}>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username }),
    });
  }

  async logout() {
    return this.request<{message: string}>('/auth/logout', {
      method: 'POST',
    });
  }

  // Ingestion
  async uploadFile(file: File, ingestionType: string): Promise<IngestionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ingestion_type', ingestionType);

    return this.request<IngestionResponse>('/ingestion/upload', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }

  async getIngestionStatus(taskId: string): Promise<IngestionStatus> {
    return this.request<IngestionStatus>(`/ingestion/status/${taskId}`);
  }

  // Analysis - Missing Dates
  async getMissingDates(request: MissingDatesRequest): Promise<MissingDatesResponse> {
    return this.request<MissingDatesResponse>('/analysis/missing-dates', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Analysis - Duplicates
  async getDuplicates(request: DuplicatesRequest): Promise<DuplicatesResponse> {
    return this.request<DuplicatesResponse>('/analysis/duplicates', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getDuplicateDetails(logId: string, duplicatesFilter: string, duplicateIds: string[]) {
    const params = new URLSearchParams({
      duplicates_filter: duplicatesFilter,
      duplicate_ids: duplicateIds.join(','),
    });
    
    return this.request(`/analysis/duplicates/${logId}/details?${params}`);
  }

  // Analysis - Storage Metadata
  async getStorageMetadata(request: StorageMetadataRequest): Promise<StorageMetadataResponse> {
    return this.request<StorageMetadataResponse>('/analysis/storage-metadata', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getFieldLineage(logId: string) {
    return this.request(`/analysis/storage-metadata/${logId}/lineage`);
  }

  // Analysis - Process Metadata
  async getProcessMetadata(request: ProcessMetadataRequest): Promise<ProcessMetadataResponse> {
    return this.request<ProcessMetadataResponse>('/analysis/process-metadata', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Health check
  async healthCheck() {
    return this.request<{status: string; message: string}>('/health');
  }
}

export const apiService = new ApiService();