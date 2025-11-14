/**
 * API client for OCR PDF backend.
 * Provides typed fetch wrappers for all endpoints.
 */

const API_BASE_URL = '/api/v1';

/**
 * Generic fetch wrapper with error handling.
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Types

export interface FolderSettings {
  folder_path: string;
  include_subfolders: boolean;
  auto_ingest: boolean;
}

export interface ScanRequest {
  path?: string;
  include_subfolders?: boolean;
}

export interface ScanResponse {
  job_id: string;
  scan_path: string;
  include_subfolders: boolean;
  message: string;
}

export interface ScanJobStatus {
  job_id: string;
  scan_path: string;
  include_subfolders: boolean;
  started_at: string;
  completed_at: string | null;
  status: 'running' | 'completed' | 'failed';
  new_files: number | null;
  skipped_files: number | null;
  error_count: number | null;
  errors: string[] | null;
}

export interface SearchResult {
  document_id: number;
  filename: string;
  page_no: number;
  snippet: string;
  score: number;
  chunk_id?: number;
  bbox?: Record<string, unknown>;
}

export interface FullTextSearchResponse {
  query: string;
  total_results: number;
  page: number;
  page_size: number;
  results: SearchResult[];
}

export interface SemanticSearchRequest {
  query: string;
  top_k?: number;
  filters?: Record<string, unknown>;
}

export interface SemanticSearchResponse {
  query: string;
  results: SearchResult[];
}

// Settings API

export async function getFolderSettings(): Promise<FolderSettings> {
  return fetchAPI<FolderSettings>('/settings/folder');
}

export async function updateFolderSettings(
  settings: Partial<FolderSettings>
): Promise<FolderSettings> {
  return fetchAPI<FolderSettings>('/settings/folder', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

// Scan API

export async function triggerScan(
  request: ScanRequest = {}
): Promise<ScanResponse> {
  return fetchAPI<ScanResponse>('/scan', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getScanStatus(jobId: string): Promise<ScanJobStatus> {
  return fetchAPI<ScanJobStatus>(`/scan/${jobId}`);
}

// Search API

export async function searchFullText(
  query: string,
  page: number = 1,
  pageSize: number = 20
): Promise<FullTextSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  return fetchAPI<FullTextSearchResponse>(`/search/fulltext?${params}`);
}

export async function searchSemantic(
  request: SemanticSearchRequest
): Promise<SemanticSearchResponse> {
  return fetchAPI<SemanticSearchResponse>('/search/semantic', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
