export default function Message({ role, content }) {
  return (
    <div className={`message ${role}`}>
      <strong>{role === "user" ? "You" : "Assistant"}</strong>
      <p>{content}</p>
    </div>
  );
}
