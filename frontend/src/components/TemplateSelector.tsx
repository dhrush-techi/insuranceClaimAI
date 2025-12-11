import { useState } from "react";
import type { AppUser, TemplateOption } from "../types";

interface Props {
  templates: TemplateOption[];
  selectedCaseId: string | null;
  backendUrl: string;
  user: AppUser;
}

export default function TemplateSelector({ templates, selectedCaseId, backendUrl, user }: Props) {
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [format, setFormat] = useState<"pdf" | "docx" | "txt">("pdf");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    if (!selectedCaseId || !templateId) {
      setStatus("Select a case and template first.");
      return;
    }

    setLoading(true);
    setStatus("Generating letter…");

    try {
      const res = await fetch(`${backendUrl}/api/generate-letter`, {
        method: "POST",
        body: JSON.stringify({
          user_id: user.id,
          case_id: selectedCaseId,
          template_id: templateId,
          format,
        }),
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Generation failed");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `appeal-letter-${selectedCaseId}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setStatus("Letter downloaded.");
    } catch (err: any) {
      setStatus(err.message || "Error generating letter.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-muted">
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>Appeal letter templates</h2>
      <p style={{ fontSize: "0.8rem", opacity: 0.9, marginBottom: 8 }}>
        Choose a template that matches your denial category and export the draft as PDF, Word, or text.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <select
          className="select"
          value={templateId ?? ""}
          onChange={(e) => setTemplateId(e.target.value || null)}
        >
          <option value="">Select template…</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name} ({t.category})
            </option>
          ))}
        </select>

        <div style={{ display: "flex", gap: 8 }}>
          <select
            className="select"
            style={{ maxWidth: 160 }}
            value={format}
            onChange={(e) => setFormat(e.target.value as "pdf" | "docx" | "txt")}
          >
            <option value="pdf">PDF</option>
            <option value="docx">Word (.docx)</option>
            <option value="txt">Text (.txt)</option>
          </select>
          <button className="btn btn-primary" type="button" onClick={handleDownload} disabled={loading}>
            {loading ? "Generating…" : "Download"}
          </button>
        </div>
        {status && (
          <div style={{ fontSize: "0.8rem", opacity: 0.9 }}>
            {status}
          </div>
        )}
        {!selectedCaseId && (
          <div style={{ fontSize: "0.7rem", opacity: 0.8 }}>
            Tip: click a case in “Previous analyses” to choose which denial this letter should be based on.
          </div>
        )}
      </div>
    </div>
  );
}
