import { Navigate, Outlet } from 'react-router-dom';
import type { UserRole } from '../types/auth';
import { getAccessToken, getStoredUser } from '../utils/authStorage';

type ProtectedRouteProps = {
  allowedRoles?: UserRole[];
};

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const token = getAccessToken();
  const user = getStoredUser();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && (!user || !allowedRoles.includes(user.role))) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
