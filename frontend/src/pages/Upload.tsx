import { useRef, useState } from "react";
import { uploadDocument } from "../api/client";

export default function Upload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleUpload() {
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setStatus("uploading");
    setMessage("");

    try {
      const res = await uploadDocument(file);
      setStatus("done");
      setMessage(`"${res.name}" accepted (id: ${res.id}). Processing in background…`);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err: unknown) {
      setStatus("error");
      const msg = err instanceof Error ? err.message : "Upload failed";
      setMessage(msg);
    }
  }

  return (
    <div style={{ maxWidth: 520, margin: "40px auto", padding: "0 16px" }}>
      <h2 style={{ marginBottom: 24, fontSize: 20, fontWeight: 700 }}>Upload Document</h2>

      <div
        style={{
          border: "2px dashed #d1d5db",
          borderRadius: 10,
          padding: "36px 24px",
          textAlign: "center",
          backgroundColor: "#f9fafb",
        }}
      >
        <p style={{ color: "#6b7280", marginBottom: 16, fontSize: 14 }}>
          Supported formats: PDF, DOCX, TXT
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          style={{ display: "block", margin: "0 auto 16px" }}
        />
        <button
          onClick={handleUpload}
          disabled={status === "uploading"}
          style={{
            padding: "8px 24px",
            backgroundColor: status === "uploading" ? "#a5b4fc" : "#6366f1",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: status === "uploading" ? "default" : "pointer",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          {status === "uploading" ? "Uploading…" : "Upload"}
        </button>
      </div>

      {message && (
        <p
          style={{
            marginTop: 16,
            fontSize: 13,
            color: status === "error" ? "#dc2626" : "#16a34a",
            padding: "10px 14px",
            borderRadius: 6,
            backgroundColor: status === "error" ? "#fef2f2" : "#f0fdf4",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}
