import Message from "./Message";

export default function ChatWindow({ messages, loading }) {
  return (
    <section className="chat-window">
      {messages.map((message, index) => (
        <Message key={`${message.role}-${index}`} role={message.role} content={message.content} />
      ))}
      {loading ? <div className="loading">Loading response...</div> : null}
    </section>
  );
}
