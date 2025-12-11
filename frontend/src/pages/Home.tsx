import { Link } from "react-router-dom";
import type { AppUser } from "../types";

interface Props {
  user: AppUser | null;
}

export default function Home({ user }: Props) {
  return (
    <main>
      <section className="card">
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
            <div style={{ maxWidth: 520 }}>
              <h1 style={{ fontSize: "2rem", marginBottom: 8 }}>Turn Denials into Approvals.</h1>
              <p style={{ fontSize: "0.95rem", opacity: 0.9, lineHeight: 1.5 }}>
                Lighthouse AI ingests your denial letters and medical records, analyzes why your claim was rejected,
                finds supporting medical evidence, reasons about appeal viability, and drafts a structured appeal letter
                you can submit back to your insurer.
              </p>
              <div style={{ marginTop: 16, display: "flex", gap: 10, flexWrap: "wrap" }}>
                <span className="pill-label">
                  <span>🔍</span> Denial Analyzer
                </span>
                <span className="pill-label">
                  <span>📑</span> Evidence Investigator
                </span>
                <span className="pill-label">
                  <span>⚖️</span> Reasoning Engine
                </span>
                <span className="pill-label">
                  <span>✉️</span> Appeal Advocate
                </span>
              </div>
              <div style={{ marginTop: 20, display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Link to={user ? "/dashboard" : "/auth"}>
                  <button className="btn btn-primary">
                    {user ? "Go to Dashboard" : "Login / Register"}
                  </button>
                </Link>
                <a href="#creators">
                  <button className="btn btn-ghost">Meet the creators</button>
                </a>
              </div>
            </div>
            <div className="card-muted" style={{ flex: 1, minWidth: 260 }}>
              <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>How Lighthouse AI works</h2>
              <ol style={{ fontSize: "0.88rem", opacity: 0.95, lineHeight: 1.5, paddingLeft: 18 }}>
                <li>Upload your denial letter and medical records.</li>
                <li>AI extracts denial reasons and supporting clinical evidence.</li>
                <li>Reasoning engine checks if an appeal is strong enough.</li>
                <li>You receive a draft appeal letter + evidence summary.</li>
              </ol>
            </div>
          </div>

          <div id="creators" className="card-muted" style={{ marginTop: 8 }}>
            <h2 style={{ fontSize: "1rem", marginBottom: 6 }}>Creators</h2>
            <p style={{ fontSize: "0.85rem", opacity: 0.9, marginBottom: 8 }}>
              Lighthouse AI was built by a small team of developers and AI enthusiasts focused on making complex health
              insurance workflows simpler:
            </p>
            <ul style={{ fontSize: "0.85rem", opacity: 0.95, lineHeight: 1.6, paddingLeft: 18 }}>
              <li>🏥 Domain: Health insurance, claim denials, medical documentation.</li>
              <li>🤖 Stack: TypeScript, Supabase, Python, and modern AI/ML pipelines.</li>
              <li>🔐 Focus: Data privacy, per-user document isolation, explainable decisions.</li>
            </ul>
          </div>
        </div>
      </section>
    </main>
  );
}
