import { useState } from "react";

export default function InputBox({ onSend, loading }) {
  const [value, setValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!value.trim() || loading) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <form className="input-box" onSubmit={handleSubmit}>
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Ask about university policy..."
      />
      <button type="submit" disabled={loading}>
        {loading ? "Thinking..." : "Send"}
      </button>
    </form>
  );
}
