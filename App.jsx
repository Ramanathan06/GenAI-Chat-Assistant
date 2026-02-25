import { useEffect, useMemo, useState } from "react";
import ChatWindow from "./components/ChatWindow";
import InputBox from "./components/InputBox";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! Ask me anything about university policies." }
  ]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const existing = localStorage.getItem("rag_session_id");
    if (existing) {
      setSessionId(existing);
      return;
    }

    fetch(`${API_BASE_URL}/api/session`)
      .then((response) => response.json())
      .then((data) => {
        localStorage.setItem("rag_session_id", data.session_id);
        setSessionId(data.session_id);
      })
      .catch(() => {
        const fallback = `offline-${Date.now()}`;
        localStorage.setItem("rag_session_id", fallback);
        setSessionId(fallback);
      });
  }, []);

  const canAsk = useMemo(() => !!sessionId && !loading, [sessionId, loading]);

  const sendMessage = async (question) => {
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, question })
      });

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer || "I don't know." }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "I couldn't reach the server. Please try again." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <h1>Production-Grade RAG Assistant</h1>
      <p className="meta">Session: {sessionId || "creating..."}</p>
      <ChatWindow messages={messages} loading={loading} />
      <InputBox onSend={sendMessage} loading={!canAsk} />
    </main>
  );
}
