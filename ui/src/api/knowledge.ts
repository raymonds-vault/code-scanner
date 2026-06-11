import { apiFetch, apiFormFetch } from "./client.ts";

export interface KnowledgeDocument {
  id: string;
  source: string;
  category: string;
  doc_version: string;
  namespace: string;
  chunk_count: number;
  path?: string;
  created_at: string;
}

export interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocument[];
  total: number;
}

export interface IngestResponse {
  source: string;
  category: string;
  doc_version: string;
  namespace: string;
  embedding_model: string;
  chunk_count: number;
  content_hashes: string[];
}

export async function listDocuments(): Promise<KnowledgeDocumentListResponse> {
  return apiFetch<KnowledgeDocumentListResponse>("/api/v1/knowledge/documents");
}

export async function uploadDocumentText(payload: {
  source: string;
  category: string;
  text: string;
  doc_version?: string;
  namespace?: string;
}): Promise<IngestResponse> {
  return apiFetch<IngestResponse>("/api/v1/knowledge/documents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadDocumentFile(
  file: File,
  meta: { source: string; category: string; doc_version?: string; namespace?: string }
): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("source", meta.source);
  form.append("category", meta.category);
  if (meta.doc_version) form.append("doc_version", meta.doc_version);
  if (meta.namespace) form.append("namespace", meta.namespace);
  return apiFormFetch<IngestResponse>("/api/v1/knowledge/files", form);
}
