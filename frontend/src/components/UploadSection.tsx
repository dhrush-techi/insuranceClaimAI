import { FormEvent, useState } from "react";
import type { AppUser, UploadRecord } from "../types";

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

interface Props {
  user: AppUser;
  onUploadComplete: (record: UploadRecord) => void;
}

export default function UploadSection({ user, onUploadComplete }: Props) {
  const [denialFile, setDenialFile] = useState<File | null>(null);
  const [medicalFile, setMedicalFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!denialFile && !medicalFile) {
      setStatus("Please upload at least one file.");
      return;
    }

    const formData = new FormData();
    formData.append("user_id", user.id);
    if (denialFile) formData.append("denial_letter", denialFile);
    if (medicalFile) formData.append("medical_record", medicalFile);

    setLoading(true);
    setStatus("Uploading and analyzing…");

    try {
      const res = await fetch(`${backendUrl}/api/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Upload error");
      }

      const data = (await res.json()) as UploadRecord;
      onUploadComplete(data);
      setStatus("Upload and analysis complete.");
      setDenialFile(null);
      setMedicalFile(null);
    } catch (err: any) {
      setStatus(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-muted">
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>Upload denial letter & medical records</h2>
      <p style={{ fontSize: "0.8rem", opacity: 0.9, marginBottom: 10 }}>
        Supported: PDF, DOCX, images and more. Files are linked only to your account and used to power your private AI
        workspace.
      </p>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div>
          <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Denial letter</label>
          <input
            className="input"
            style={{ padding: 6 }}
            type="file"
            accept=".pdf,.doc,.docx,image/*,.txt"
            onChange={(e) => setDenialFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <div>
          <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Medical report / EHR</label>
          <input
            className="input"
            style={{ padding: 6 }}
            type="file"
            accept=".pdf,.doc,.docx,image/*,.txt"
            onChange={(e) => setMedicalFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Processing…" : "Upload & Analyze"}
        </button>
        {status && (
          <div style={{ fontSize: "0.8rem", opacity: 0.9, marginTop: 4 }}>
            {status}
          </div>
        )}
      </form>
    </div>
  );
}
