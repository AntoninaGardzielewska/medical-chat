"use client";

import { useState } from "react";
import Link from "next/link";

import MessageThread from "./components/MessageThread";
import ChatInput from "./components/ChatInput";

export default function HomePage() {
  const [input, setInput] = useState("");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am your medical assistant. Ask me anything.",
    },
  ]);

  function handleSend() {
    if (!input.trim()) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: input },
    ]);

    setInput("");
  }

  return (
    <main
      style={{
        fontFamily: "system-ui, sans-serif",
        padding: "2rem",
        maxWidth: "800px",
        margin: "0 auto",
      }}
    >
      <h1>Medical Chat</h1>

      <p>
        Backend health check:{" "}
        <Link href="/health">/health</Link>
      </p>

      {/* CHAT UI */}
      <MessageThread messages={messages} />

      <ChatInput
        input={input}
        setInput={setInput}
        onSend={handleSend}
      />
    </main>
  );
}
