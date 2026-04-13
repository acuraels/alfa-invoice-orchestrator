import { Navigate, Outlet } from 'react-router-dom';
import { getAccessToken } from '../utils/authStorage';

export function ProtectedRoute() {
  const token = getAccessToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
