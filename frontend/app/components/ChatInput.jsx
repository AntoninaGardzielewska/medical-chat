export default function ChatInput({
  input,
  setInput,
  onSend,
}) {
  return (
    <div style={{ display: "flex", gap: "10px" }}>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask a medical question..."
        style={{ flex: 1, padding: "10px" }}
      />

      <button onClick={onSend}>
        Send
      </button>
    </div>
  );
}
