import type { UploadRecord } from "../types";

interface Props {
  uploads: UploadRecord[];
  selectedCaseId: string | null;
  onSelectCase: (id: string) => void;
}

export default function HistorySection({ uploads, selectedCaseId, onSelectCase }: Props) {
  return (
    <div className="card-muted1" >
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>Previous analyses</h2>
      <p style={{ fontSize: "0.8rem", opacity: 0.85, marginBottom: 10 }}>
        Review all uploaded denial letters, medical records and AI decisions.
      </p>
      <div className="history-list">
        {uploads.length === 0 && (
          <div style={{ fontSize: "0.8rem", opacity: 0.8 }}>No analyses yet. Upload a case to get started.</div>
        )}
        {uploads.map((u) => (
          <button
            type="button"
            key={u.id}
            className="history-item"
            onClick={() => onSelectCase(u.id)}
            style={{
              borderColor: selectedCaseId === u.id ? "rgba(255,255,255,0.7)" : undefined,
              boxShadow: selectedCaseId === u.id ? "0 0 0 1px rgba(255,255,255,0.4)" : undefined,
            }}
          >
            <div>
              <div style={{ fontWeight: 500, marginBottom: 2, fontSize: "0.8rem" }}>
                {u.denial_filename || "Denial file"}
              </div>
              <div style={{ fontSize: "0.7rem", opacity: 0.8 }}>
                {new Date(u.created_at).toLocaleString()}
              </div>
            </div>
            <div style={{ fontSize: "0.75rem" }}>
              <div>{u.medical_filename || "Medical file"}</div>
              {u.insurer_name && <div style={{ opacity: 0.8 }}>Insurer: {u.insurer_name}</div>}
            </div>
            <div style={{ fontSize: "0.75rem" }}>
              <span className="badge">{u.denial_category || "Unknown"}</span>
            </div>
            <div style={{ textAlign: "right", fontSize: "0.75rem" }}>
              {typeof u.confidence_score === "number" && (
                <div>Score: {u.confidence_score.toFixed(0)}%</div>
              )}
              <div style={{ opacity: 0.9 }}>Status: {u.status}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
