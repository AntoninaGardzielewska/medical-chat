"use client";

import { useState } from "react";
import type { Reference } from "../../lib/api";

interface ReferencesProps {
  references: Reference[];
}

export default function References({ references }: ReferencesProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!references || references.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        marginTop: "16px",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        backgroundColor: "#f9fafb",
      }}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: "100%",
          padding: "12px 16px",
          textAlign: "left",
          background: "none",
          border: "none",
          cursor: "pointer",
          fontSize: "0.95rem",
          fontWeight: "600",
          color: "#1f2937",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span>
          📚 Source{references.length === 1 ? "" : "s"} cited ({references.length})
        </span>
        <span style={{ fontSize: "1.2rem" }}>
          {isExpanded ? "▼" : "▶"}
        </span>
      </button>

      {isExpanded && (
        <div
          style={{
            borderTop: "1px solid #e5e7eb",
            padding: "12px 16px",
          }}
        >
          <ol
            style={{
              margin: 0,
              paddingLeft: "20px",
              listStylePosition: "outside",
            }}
          >
            {references.map((ref) => (
              <li
                key={`${ref.pmid}-${ref.number}`}
                style={{
                  marginBottom: "16px",
                  fontSize: "0.9rem",
                  lineHeight: "1.6",
                }}
              >
                <div style={{ fontWeight: "600", marginBottom: "4px" }}>
                  [{ref.number}] {ref.title}
                </div>
                <div style={{ color: "#6b7280", fontSize: "0.85rem" }}>
                  {ref.authors.length > 100
                    ? `${ref.authors.substring(0, 100)}...`
                    : ref.authors}
                </div>
                <div style={{ color: "#6b7280", fontSize: "0.85rem" }}>
                  {ref.journal} ({ref.year})
                </div>
                <a
                  href={ref.pubmed_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "#2563eb",
                    textDecoration: "none",
                    fontSize: "0.85rem",
                    fontWeight: "600",
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLAnchorElement).style.textDecoration =
                      "underline";
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLAnchorElement).style.textDecoration =
                      "none";
                  }}
                >
                  View on PubMed →
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
