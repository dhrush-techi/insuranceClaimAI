import type { ReactNode } from "react";
import { NavBar } from "./NavBar";
import type { AppUser } from "../types";

interface LayoutProps {
  children: ReactNode;
  user: AppUser | null;
}

export function Layout({ children, user }: LayoutProps) {
  return (
    <div className="app-shell">
      <NavBar user={user} />
      {children}
    </div>
  );
}
