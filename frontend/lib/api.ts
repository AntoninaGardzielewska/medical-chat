/**
 * API client for the Medical Chat backend
 */

export interface Reference {
  number: number;
  pmid: string;
  title: string;
  authors: string;
  journal: string;
  year: string;
  pubmed_url: string;
}

export interface ChatResponse {
  disclaimer: string;
  answer: string;
  references: Reference[];
  include_sources: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendMessage(question: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(
      error.detail || "Failed to send message. Please try again."
    );
  }

  return response.json();
}
