import { useEffect, useRef } from "react";
import type { Source } from "../api/client";
import SourceCard from "./SourceCard";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

interface Props {
  messages: ChatMessage[];
}

export default function ChatWindow({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#9ca3af",
          fontSize: 14,
        }}
      >
        Select documents and ask a question to get started.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "12px 0" }}>
      {messages.map((msg, i) => (
        <div
          key={i}
          style={{
            marginBottom: 16,
            display: "flex",
            flexDirection: "column",
            alignItems: msg.role === "user" ? "flex-end" : "flex-start",
          }}
        >
          <div
            style={{
              maxWidth: "80%",
              padding: "10px 14px",
              borderRadius: 10,
              backgroundColor: msg.role === "user" ? "#6366f1" : "#f3f4f6",
              color: msg.role === "user" ? "#fff" : "#111827",
              fontSize: 14,
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
            }}
          >
            {msg.content}
          </div>

          {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
            <div style={{ maxWidth: "80%", marginTop: 8 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", marginBottom: 4 }}>
                SOURCES
              </div>
              {msg.sources.map((src, j) => (
                <SourceCard key={j} source={src} />
              ))}
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
