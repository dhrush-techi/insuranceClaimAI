import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { Layout } from "./components/Layout";
import Home from "./pages/Home";
import AuthPage from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import EvaluationPage from "./pages/evaluation";
import EmailConfirmed from "./pages/email-confirmed";
import Creators from "./pages/creators"; 
import { ProtectedRoute } from "./components/ProtectedRoute";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="app-shell">
        <div className="card">
          <p>Loading Lighthouse AI…</p>
        </div>
      </div>
    );
  }

  return (
    <Layout user={user}>
      <Routes>
        <Route path="/" element={<Home user={user} />} />
        <Route
          path="/auth"
          element={user ? <Navigate to="/dashboard" replace /> : <AuthPage />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute user={user}>
              <Dashboard user={user!} />
            </ProtectedRoute>
          }
        />

        <Route
          path="/evaluate"
          element={
            <ProtectedRoute user={user}>
              <EvaluationPage />
            </ProtectedRoute>
          }
        />

        <Route path="/email-confirmed" element={<EmailConfirmed />} />
        
        <Route path="/creators" element={<Creators />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}