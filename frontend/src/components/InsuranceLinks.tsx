const LINKS = [
  {
    name: "IRDAI Health Insurance",
    url: "https://irdai.gov.in",
    note: "Official regulator (India) – understand your rights.",
  },
  {
    name: "Star Health Insurance",
    url: "https://www.starhealth.in",
    note: "Apply or manage retail health plans.",
  },
  {
    name: "HDFC ERGO Health",
    url: "https://www.hdfcergo.com/health-insurance",
    note: "Health plans & online claim services.",
  },
  {
    name: "Niva Bupa",
    url: "https://www.nivabupa.com",
    note: "Individual and family health coverage options.",
  },
];

export default function InsuranceLinks() {
  return (
    <div className="card-muted">
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>Health insurance options</h2>
      <p style={{ fontSize: "0.8rem", opacity: 0.9, marginBottom: 8 }}>
        Explore health insurance portals. Lighthouse AI does not submit claims for you, but you can use our appeal
        letters when you re-apply or appeal.
      </p>
      <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
        {LINKS.map((link) => (
          <li
            key={link.url}
            style={{
              padding: "8px 10px",
              borderRadius: 12,
              background: "rgba(0, 20, 20, 0.9)",
              border: "1px solid rgba(0,128,128,0.5)",
            }}
          >
            <a
              href={link.url}
              target="_blank"
              rel="noreferrer"
              style={{ color: "#ffffff", textDecoration: "none", fontSize: "0.85rem" }}
            >
              <div style={{ fontWeight: 500 }}>{link.name}</div>
              <div style={{ fontSize: "0.8rem", opacity: 0.9 }}>{link.note}</div>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
