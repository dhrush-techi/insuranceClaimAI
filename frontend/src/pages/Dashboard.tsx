import type { AppUser, UploadRecord, ChatMessage, TemplateOption } from "../types";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import UploadSection from "../components/UploadSection";
import ChatSection from "../components/ChatSection";
import HistorySection from "../components/HistorySection";
import InsuranceLinks from "../components/InsuranceLinks";
import TemplateSelector from "../components/TemplateSelector";

const backendUrl =
  import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

interface Props {
  user: AppUser;
}

export default function Dashboard({ user }: Props) {
  const navigate = useNavigate();

  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [templates, setTemplates] = useState<TemplateOption[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  // -------------------------
  // Fetch history & templates
  // -------------------------
  useEffect(() => {
    const fetchHistory = async () => {
      const res = await fetch(
        `${backendUrl}/api/history?user_id=${user.id}`,
      );
      if (res.ok) {
        const data = (await res.json()) as UploadRecord[];
        setUploads(data);
      }
    };

    const fetchTemplates = async () => {
      const res = await fetch(`${backendUrl}/api/template-options`);
      if (res.ok) {
        const data = (await res.json()) as TemplateOption[];
        setTemplates(data);
      }
    };

    void fetchHistory();
    void fetchTemplates();
  }, [user.id]);

  // -------------------------
  // Handlers
  // -------------------------
  const handleUploadComplete = (record: UploadRecord) => {
    setUploads((prev) => [record, ...prev]);
    setSelectedCaseId(record.id);
  };

  const handleChatUpdate = (messages: ChatMessage[]) => {
    setChatMessages(messages);
  };

  // -------------------------
  // Render
  // -------------------------
  return (
    <main>
      <section className="card">
        {/* ---------------- HEADER ---------------- */}
        <div className="dashboard-grid">
          <div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: 12,
              }}
            >
              <div>
                <h1
                  style={{
                    fontSize: "1.4rem",
                    marginBottom: 6,
                  }}
                >
                  Dashboard
                </h1>
                <p
                  style={{
                    fontSize: "0.85rem",
                    opacity: 0.9,
                  }}
                >
                  Welcome back, {user.email}.  
                  Your documents and AI workspace are private,
                  isolated, and explainable.
                </p>
              </div>

              {/* ✅ NAVIGATION TO EVALUATION */}
              <button
                className="btn btn-primary"
                onClick={() => navigate("/evaluate")}
              >
                📊 Evaluation
              </button>
            </div>

            {/* Badges */}
            <div
              style={{
                marginTop: 12,
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
              }}
            >
              <span className="badge">Per-user document store</span>
              <span className="badge">Multi-agent reasoning</span>
              <span className="badge">Explainable AI</span>
              <span className="badge">Confidence calibration</span>
              <span className="badge">Analytics & evaluation</span>
            </div>
          </div>

          <InsuranceLinks />
        </div>

        {/* ---------------- UPLOAD + HISTORY ---------------- */}
        <div
          className="dashboard-grid-wide"
          style={{ marginTop: 22 }}
        >
          <UploadSection
            user={user}
            onUploadComplete={handleUploadComplete}
          />

          <HistorySection
            uploads={uploads}
            selectedCaseId={selectedCaseId}
            onSelectCase={(id) => setSelectedCaseId(id)}
          />
        </div>

        {/* ---------------- CHAT + TEMPLATE ---------------- */}
        <div
          className="dashboard-grid-wide"
          style={{ marginTop: 18 }}
        >
          <ChatSection
            user={user}
            onMessagesChange={handleChatUpdate}
          />

          <TemplateSelector
            templates={templates}
            selectedCaseId={selectedCaseId}
            backendUrl={backendUrl}
            user={user}
          />
        </div>
      </section>
    </main>
  );
}
