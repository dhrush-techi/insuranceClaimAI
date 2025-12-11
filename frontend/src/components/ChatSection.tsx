import { FormEvent, useEffect, useRef, useState } from "react";
import type { AppUser, ChatMessage } from "../types";

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

interface Props {
  user: AppUser;
  onMessagesChange: (messages: ChatMessage[]) => void;
}

export default function ChatSection({ user, onMessagesChange }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      const res = await fetch(`${backendUrl}/api/chat/history?user_id=${user.id}`);
      if (res.ok) {
        const data = (await res.json()) as ChatMessage[];
        setMessages(data);
        onMessagesChange(data);
      }
    };
    void fetchHistory();
  }, [user.id, onMessagesChange]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
      created_at: new Date().toISOString(),
    };
    const optimistic = [...messages, userMessage];
    setMessages(optimistic);
    onMessagesChange(optimistic);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${backendUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, message: userMessage.content }),
      });
      const botMessage = (await res.json()) as ChatMessage;
      const updated = [...optimistic, botMessage];
      setMessages(updated);
      onMessagesChange(updated);
    } catch {
      // In production add error UI
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-muted">
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>Lighthouse AI Chat</h2>
      <p style={{ fontSize: "0.8rem", opacity: 0.9, marginBottom: 8 }}>
        Ask questions about your denial and medical history. The bot uses only your own uploaded documents.
      </p>
      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`chat-message ${m.role === "user" ? "user" : "bot"}`}
            >
              {m.content}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form onSubmit={sendMessage} className="chat-input-row">
          <input
            className="input"
            placeholder="Ask about your denial, treatments, coding, etc."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "…" : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
