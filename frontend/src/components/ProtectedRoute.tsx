import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import type { AppUser } from "../types";

interface Props {
  user: AppUser | null;
  children: ReactNode;
}

export function ProtectedRoute({ user, children }: Props) {
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  return <>{children}</>;
}
