import type { DocumentRecord } from "../api/client";

interface Props {
  documents: DocumentRecord[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

const STATUS_COLORS: Record<string, string> = {
  complete: "#16a34a",
  processing: "#d97706",
  pending: "#6b7280",
  failed: "#dc2626",
};

export default function DocumentList({ documents, selectedIds, onToggle, onDelete }: Props) {
  if (documents.length === 0) {
    return <p style={{ color: "#9ca3af", fontSize: 13 }}>No documents uploaded yet.</p>;
  }

  return (
    <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {documents.map((doc) => {
        const isSelected = selectedIds.includes(doc.id);
        const isReady = doc.status === "complete";

        return (
          <li
            key={doc.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              marginBottom: 4,
              borderRadius: 6,
              border: `1px solid ${isSelected ? "#6366f1" : "#e5e7eb"}`,
              backgroundColor: isSelected ? "#eef2ff" : "#fff",
              cursor: isReady ? "pointer" : "default",
              opacity: isReady ? 1 : 0.65,
            }}
            onClick={() => isReady && onToggle(doc.id)}
          >
            <input
              type="checkbox"
              checked={isSelected}
              readOnly
              disabled={!isReady}
              style={{ cursor: isReady ? "pointer" : "default" }}
            />
            <span style={{ flex: 1, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {doc.name}
            </span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: STATUS_COLORS[doc.status] ?? "#6b7280",
                whiteSpace: "nowrap",
              }}
            >
              {doc.status}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(doc.id);
              }}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "#9ca3af",
                fontSize: 16,
                lineHeight: 1,
                padding: "0 2px",
              }}
              title="Delete document"
            >
              ×
            </button>
          </li>
        );
      })}
    </ul>
  );
}
