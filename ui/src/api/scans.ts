import { apiFetch } from "./client.ts";

export interface ScanSummary {
  id: string;
  status: string;
  progress: number;
  finding_count: number;
  created_at: string;
  metadata: Record<string, unknown>;
}

export interface Finding {
  id: string;
  file_path: string;
  line_number: number;
  vulnerability_type: string;
  severity: string;
  confidence: number;
  source: string;
  explanation?: string;
  fix?: string;
}

export interface ScanDetail {
  id: string;
  status: string;
  progress: number;
  metadata: Record<string, unknown>;
  findings: Finding[];
}

export interface ScanListResponse {
  scans: ScanSummary[];
  total: number;
}

export async function listScans(limit = 50, offset = 0): Promise<ScanListResponse> {
  return apiFetch<ScanListResponse>(`/api/v1/scans?limit=${limit}&offset=${offset}`);
}

export async function getScan(id: string): Promise<ScanDetail> {
  return apiFetch<ScanDetail>(`/api/v1/scan/${id}`);
}
