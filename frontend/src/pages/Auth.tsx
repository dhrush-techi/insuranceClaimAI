import { FormEvent, useState } from "react";
import { supabase } from "../supabaseClient";
import { useNavigate } from "react-router-dom";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
      }
      navigate("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <section className="card" style={{ maxWidth: 480, margin: "0 auto" }}>
        <h1 style={{ fontSize: "1.5rem", marginBottom: 12 }}>
          {isLogin ? "Login to Lighthouse AI" : "Create your Lighthouse AI account"}
        </h1>
        <p style={{ fontSize: "0.9rem", opacity: 0.85, marginBottom: 16 }}>
          Securely store your denial letters and medical records. Each account has its own isolated AI workspace.
        </p>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Email</label>
            <input
              className="input"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Password</label>
            <input
              className="input"
              type="password"
              autoComplete={isLogin ? "current-password" : "new-password"}
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          {errorMsg && (
            <div
              style={{
                fontSize: "0.8rem",
                color: "#ffffff",
                background: "rgba(128, 0, 0, 0.3)",
                borderRadius: 12,
                padding: "8px 10px",
              }}
            >
              {errorMsg}
            </div>
          )}
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "Processing..." : isLogin ? "Login" : "Register"}
          </button>
        </form>
        <div style={{ marginTop: 12, fontSize: "0.8rem" }}>
          {isLogin ? (
            <>
              New here?{" "}
              <button
                type="button"
                className="btn btn-ghost"
                style={{ padding: "2px 10px", fontSize: "0.8rem" }}
                onClick={() => setIsLogin(false)}
              >
                Create an account
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                type="button"
                className="btn btn-ghost"
                style={{ padding: "2px 10px", fontSize: "0.8rem" }}
                onClick={() => setIsLogin(true)}
              >
                Login
              </button>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
