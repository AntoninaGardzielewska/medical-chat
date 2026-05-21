import MessageBubble from "./MessageBubble";

export default function MessageThread({ messages }) {
  return (
    <div style={{ marginTop: "20px" }}>
      {messages.map((msg, i) => (
        <MessageBubble
          key={i}
          role={msg.role}
          content={msg.content}
        />
      ))}
    </div>
  );
}
