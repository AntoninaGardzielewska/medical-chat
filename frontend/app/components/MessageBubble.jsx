export default function MessageBubble({ role, content }) {
  const isUser = role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "10px",
      }}
    >
      <div
        style={{
          background: isUser ? "#cce5ff" : "#e9ecef",
          padding: "10px",
          borderRadius: "10px",
          maxWidth: "70%",
        }}
      >
        {content}
      </div>
    </div>
  );
}
