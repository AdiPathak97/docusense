import { useCallback, useEffect, useRef, useState } from "react";
import { deleteDocument, listDocuments, queryDocuments } from "../api/client";
import type { DocumentRecord } from "../api/client";
import DocumentList from "../components/DocumentList";
import ChatWindow, { type ChatMessage } from "../components/ChatWindow";

const POLL_INTERVAL_MS = 4000;

export default function Chat() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Fetch document list on mount and poll for status changes
  const fetchDocs = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // Silently ignore polling errors
    }
  }, []);

  useEffect(() => {
    fetchDocs();
    const id = setInterval(fetchDocs, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchDocs]);

  function toggleDocument(id: string) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  async function handleDelete(id: string) {
    try {
      await deleteDocument(id);
      setSelectedIds((prev) => prev.filter((x) => x !== id));
      await fetchDocs();
    } catch {
      setError("Failed to delete document.");
    }
  }

  async function handleSubmit() {
    const q = question.trim();
    if (!q || loading) return;

    setLoading(true);
    setError("");
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);

    try {
      const res = await queryDocuments(q, selectedIds, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Query failed";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${msg}` },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div style={{ display: "flex", height: "calc(100vh - 60px)", gap: 0 }}>
      {/* Sidebar — Document selector */}
      <div
        style={{
          width: 280,
          borderRight: "1px solid #e5e7eb",
          padding: 16,
          overflowY: "auto",
          flexShrink: 0,
        }}
      >
        <div style={{ fontSize: 12, fontWeight: 700, color: "#6b7280", marginBottom: 10, letterSpacing: "0.05em" }}>
          DOCUMENTS
        </div>
        <DocumentList
          documents={documents}
          selectedIds={selectedIds}
          onToggle={toggleDocument}
          onDelete={handleDelete}
        />
        {selectedIds.length === 0 && documents.some((d) => d.status === "complete") && (
          <p style={{ fontSize: 11, color: "#9ca3af", marginTop: 8 }}>
            Select documents to limit search scope, or leave none selected to search all.
          </p>
        )}
      </div>

      {/* Main chat area */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          padding: "0 24px",
          minWidth: 0,
        }}
      >
        <ChatWindow messages={messages} />

        {error && (
          <p style={{ fontSize: 12, color: "#dc2626", marginBottom: 8 }}>{error}</p>
        )}

        {/* Input row */}
        <div
          style={{
            display: "flex",
            gap: 8,
            padding: "12px 0 16px",
            borderTop: "1px solid #e5e7eb",
          }}
        >
          <textarea
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
            style={{
              flex: 1,
              resize: "none",
              padding: "10px 12px",
              borderRadius: 8,
              border: "1px solid #d1d5db",
              fontSize: 14,
              fontFamily: "inherit",
              outline: "none",
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !question.trim()}
            style={{
              padding: "0 20px",
              borderRadius: 8,
              border: "none",
              backgroundColor: loading || !question.trim() ? "#a5b4fc" : "#6366f1",
              color: "#fff",
              fontWeight: 600,
              fontSize: 14,
              cursor: loading || !question.trim() ? "default" : "pointer",
              alignSelf: "stretch",
            }}
          >
            {loading ? "…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
