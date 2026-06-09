"use client";

import Disclaimer from "./Disclaimer";
import References from "./References";
import type { Reference } from "../../lib/api";

export interface MessageData {
  role: "user" | "assistant";
  content: string;
  disclaimer?: string;
  references?: Reference[];
  include_sources?: boolean;
  isLoading?: boolean;
}

interface MessageProps {
  message: MessageData;
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          minWidth: "200px",
        }}
      >
        {/* User message - simple bubble */}
        {isUser ? (
          <div
            style={{
              background: "#2563eb",
              color: "white",
              padding: "12px 16px",
              borderRadius: "12px",
              wordWrap: "break-word",
            }}
          >
            {message.content}
          </div>
        ) : (
          /* Assistant message - with disclaimer and references */
          <div>
            {/* Disclaimer */}
            <Disclaimer text={message.disclaimer} />

            {/* Main answer */}
            <div
              style={{
                background: "#f3f4f6",
                padding: "12px 16px",
                borderRadius: "12px",
                wordWrap: "break-word",
                lineHeight: "1.6",
              }}
            >
              {message.isLoading ? (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    color: "#6b7280",
                  }}
                >
                  <div
                    style={{
                      display: "inline-block",
                      width: "6px",
                      height: "6px",
                      borderRadius: "50%",
                      background: "#2563eb",
                      animation: "blink 1.4s infinite",
                      marginRight: "4px",
                    }}
                  />
                  <style>{`
                    @keyframes blink {
                      0%, 20%, 50%, 80%, 100% { opacity: 1; }
                      40% { opacity: 0.3; }
                      60% { opacity: 0.5; }
                    }
                  `}</style>
                  Thinking...
                </div>
              ) : (
                message.content
              )}
            </div>

            {/* References */}
            {!message.isLoading && (message.include_sources ?? Boolean(message.references?.length)) && message.references && (
              <References references={message.references} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
