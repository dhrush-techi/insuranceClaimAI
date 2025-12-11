import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../supabaseClient";
import type { AppUser } from "../types";

interface Props {
  user: AppUser | null;
}

export function NavBar({ user }: Props) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/");
  };

  return (
    <header className="navbar">
      <div className="nav-left">
        <div className="nav-logo" />
        <div>
          <div className="nav-title-main">Lighthouse AI</div>
          <div className="nav-title-sub">Health Insurance Denial Companion</div>
        </div>
      </div>
      <div className="nav-actions">
        {!user && (
          <>
            <Link to="/auth">
              <button className="btn btn-ghost">Login</button>
            </Link>
          </>
        )}
        {user && (
          <>
            <span style={{ fontSize: "0.8rem", opacity: 0.8 }}>Hi, {user.email}</span>
            <button className="btn btn-ghost" onClick={handleLogout}>
              Logout
            </button>
          </>
        )}
      </div>
    </header>
  );
}
