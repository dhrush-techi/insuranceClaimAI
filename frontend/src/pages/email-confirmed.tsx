export default function EmailConfirmed() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0f1f1f",
        color: "#fff",
      }}
    >
      <div
        style={{
          padding: 32,
          borderRadius: 14,
          background: "#132929",
          textAlign: "center",
          maxWidth: 420,
        }}
      >
        <h1>✅ Email Confirmed</h1>
        <p style={{ opacity: 0.9 }}>
          Your email has been successfully verified.
        </p>
        <p style={{ opacity: 0.7, fontSize: "0.85rem" }}>
          You may now return to the application and log in.
        </p>
      </div>
    </div>
  );
}
