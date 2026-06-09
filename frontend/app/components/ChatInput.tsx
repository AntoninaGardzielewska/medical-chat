"use client";

import { KeyboardEvent } from "react";

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export default function ChatInput({
  input,
  setInput,
  onSend,
  disabled = false,
}: ChatInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !disabled) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div style={{ display: "flex", gap: "12px" }}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a medical question..."
        disabled={disabled}
        style={{
          flex: 1,
          padding: "12px 16px",
          border: "1px solid #d1d5db",
          borderRadius: "8px",
          fontSize: "1rem",
          fontFamily: "inherit",
          opacity: disabled ? 0.6 : 1,
          cursor: disabled ? "not-allowed" : "text",
        }}
      />

      <button
        onClick={onSend}
        disabled={disabled || !input.trim()}
        style={{
          padding: "12px 24px",
          background: disabled || !input.trim() ? "#9ca3af" : "#2563eb",
          color: "white",
          border: "none",
          borderRadius: "8px",
          fontSize: "1rem",
          fontWeight: "600",
          cursor: disabled || !input.trim() ? "not-allowed" : "pointer",
          transition: "background 0.2s",
        }}
        onMouseEnter={(e) => {
          if (!disabled && input.trim()) {
            (e.target as HTMLButtonElement).style.background = "#1d4ed8";
          }
        }}
        onMouseLeave={(e) => {
          if (!disabled && input.trim()) {
            (e.target as HTMLButtonElement).style.background = "#2563eb";
          }
        }}
      >
        {disabled ? "Sending..." : "Send"}
      </button>
    </div>
  );
}
