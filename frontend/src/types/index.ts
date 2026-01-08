export interface RawDataFile {
  name: string;
  size: number;
  type: 'json';
  content?: any;
}

export interface KnownEntityFile {
  name: string;
  size: number;
  type: 'yaml' | 'yml';
  content?: any;
}

export interface AnalysisMetrics {
  totalRecords: number;
  detectedEntities: number;
  errors: number;
}

export interface MissingDate {
  date: string;
  gap: string;
}

export interface MetadataEntry {
  id: string;
  key: string;
  value: string;
  source: string;
}

export interface KnownEntity {
  id: string;
  name: string;
  type: string;
  linkedTo: string[];
}

export interface AnalysisResult {
  metrics: AnalysisMetrics;
  missingDates: MissingDate[];
  metadata: MetadataEntry[];
  knownEntities: KnownEntity[];
}

export type AuthStatus = 'unauthenticated' | 'loading' | 'authenticated';

export interface User {
  name: string;
  email: string;
  picture: string;
}
