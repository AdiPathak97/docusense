import { useState } from "react";
import Upload from "./pages/Upload";
import Chat from "./pages/Chat";

type Tab = "chat" | "upload";

export default function App() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", backgroundColor: "#fff" }}>
      {/* Nav */}
      <nav
        style={{
          display: "flex",
          alignItems: "center",
          gap: 24,
          padding: "0 24px",
          height: 60,
          borderBottom: "1px solid #e5e7eb",
          backgroundColor: "#fff",
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 16, color: "#111827" }}>
          DocuSense
        </span>
        {(["chat", "upload"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 14,
              fontWeight: tab === t ? 700 : 400,
              color: tab === t ? "#6366f1" : "#6b7280",
              borderBottom: tab === t ? "2px solid #6366f1" : "2px solid transparent",
              padding: "4px 0",
              textTransform: "capitalize",
            }}
          >
            {t}
          </button>
        ))}
      </nav>

      {/* Page */}
      {tab === "chat" ? <Chat /> : <Upload />}
    </div>
  );
}
