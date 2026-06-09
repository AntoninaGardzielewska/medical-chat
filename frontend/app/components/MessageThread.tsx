"use client";

import { useEffect, useRef } from "react";
import Message, { type MessageData } from "./Message";

interface MessageThreadProps {
  messages: MessageData[];
}

export default function MessageThread({ messages }: MessageThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div
      style={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        marginBottom: "20px",
        paddingRight: "8px",
        border: "1px solid #e5e7eb",
        borderRadius: "12px",
        padding: "16px",
        background: "#ffffff",
      }}
    >
      {messages.length === 0 ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            color: "#9ca3af",
            textAlign: "center",
          }}
        >
          <p>Start a conversation by asking a medical question...</p>
        </div>
      ) : (
        <>
          {messages.map((message, index) => (
            <Message key={index} message={message} />
          ))}
          <div ref={endRef} />
        </>
      )}
    </div>
  );
}
