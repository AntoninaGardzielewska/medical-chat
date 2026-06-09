"use client";

import { useState, useCallback } from "react";
import Link from "next/link";

import MessageThread from "./components/MessageThread";
import ChatInput from "./components/ChatInput";
import { sendMessage } from "../lib/api";
import type { MessageData } from "./components/Message";

export default function HomePage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<MessageData[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm your medical research assistant. I can help you find evidence-based information on medical topics. Ask me anything about medical conditions, treatments, or research findings.",
      disclaimer:
        "⚠️ This is a research tool and not a substitute for professional medical advice. Always consult a qualified healthcare provider before making medical decisions.",
      references: [],
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    // Add user message
    const userMessage: MessageData = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Add loading placeholder
    const loadingMessage: MessageData = {
      role: "assistant",
      content: "",
      isLoading: true,
      disclaimer: "",
      references: [],
      include_sources: false,
    };

    setMessages((prev) => [...prev, loadingMessage]);

    try {
      const response = await sendMessage(input);

      // Replace loading message with actual response
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: response.answer,
          disclaimer: response.disclaimer,
          references: response.references,
          include_sources: response.include_sources,
          isLoading: false,
        };
        return updated;
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Something went wrong";

      // Replace loading message with error
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `Error: ${errorMessage}. Please try again.`,
          disclaimer: "",
          references: [],
          isLoading: false,
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading]);

  return (
    <main
      style={{
        fontFamily: "system-ui, -apple-system, sans-serif",
        padding: "2rem",
        maxWidth: "900px",
        margin: "0 auto",
        minHeight: "100vh",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ marginBottom: "1rem" }}>
        <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "2rem" }}>
          🏥 Medical Chat
        </h1>
        <p style={{ margin: 0, color: "#6b7280", fontSize: "0.9rem" }}>
          Powered by evidence-based medical research •{" "}
          <Link href="/health" style={{ color: "#2563eb" }}>
            Backend Status
          </Link>
        </p>
      </div>

      {/* Chat Area */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}
      >
        <MessageThread messages={messages} />

        {/* Input Area */}
        <ChatInput
          input={input}
          setInput={setInput}
          onSend={handleSend}
          disabled={isLoading}
        />
      </div>
    </main>
  );
}
