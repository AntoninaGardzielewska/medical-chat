"use client";

interface DisclaimerProps {
  text?: string;
}

const DEFAULT_DISCLAIMER =
  "⚠️ This is a research tool and not a substitute for professional medical advice. Always consult a qualified healthcare provider before making medical decisions.";

export default function Disclaimer({ text = DEFAULT_DISCLAIMER }: DisclaimerProps) {
  return (
    <div
      style={{
        background: "linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)",
        border: "1px solid #d97706",
        borderRadius: "8px",
        padding: "12px 16px",
        marginBottom: "12px",
        fontSize: "0.9rem",
        lineHeight: "1.5",
        color: "#78350f",
        fontWeight: "500",
      }}
      role="alert"
      aria-live="polite"
    >
      {text}
    </div>
  );
}
