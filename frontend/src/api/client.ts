import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const http = axios.create({ baseURL: BASE_URL });

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DocumentRecord {
  id: string;
  name: string;
  content_type: string;
  status: "pending" | "processing" | "complete" | "failed";
  chunk_count: number;
  created_at: string;
}

export interface UploadResponse {
  id: string;
  name: string;
  status: string;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  content: string;
  relevance_score: number | null;
}

export interface QueryResponse {
  answer: string;
  session_id: string;
  sources: Source[];
}

// ── Documents API ─────────────────────────────────────────────────────────────

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await http.post<UploadResponse>("/api/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const res = await http.get<DocumentRecord[]>("/api/documents/");
  return res.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await http.delete(`/api/documents/${id}`);
}

// ── Chat API ──────────────────────────────────────────────────────────────────

export async function queryDocuments(
  question: string,
  documentIds: string[],
  sessionId?: string
): Promise<QueryResponse> {
  const res = await http.post<QueryResponse>("/api/chat/query", {
    question,
    document_ids: documentIds,
    session_id: sessionId ?? null,
  });
  return res.data;
}
