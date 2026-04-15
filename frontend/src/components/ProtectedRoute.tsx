import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import type { UserRole } from '../types/auth';
import { authService } from '../services/authService';
import { clearAuthStorage, getAccessToken, getRefreshToken, getStoredUser } from '../utils/authStorage';
import { isJwtExpired } from '../utils/jwt';

type ProtectedRouteProps = {
  allowedRoles?: UserRole[];
};

type GuardState = 'checking' | 'authorized' | 'unauthorized' | 'forbidden';

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const [guardState, setGuardState] = useState<GuardState>('checking');

  useEffect(() => {
    let isMounted = true;

    const authorize = async () => {
      const accessToken = getAccessToken();
      const refreshToken = getRefreshToken();
      const user = getStoredUser();

      const hasAllowedRole = !allowedRoles || (user ? allowedRoles.includes(user.role) : false);

      if (accessToken && !isJwtExpired(accessToken)) {
        if (!user) {
          clearAuthStorage();
          if (isMounted) {
            setGuardState('unauthorized');
          }
          return;
        }

        if (isMounted) {
          setGuardState(hasAllowedRole ? 'authorized' : 'forbidden');
        }
        return;
      }

      if (!refreshToken || isJwtExpired(refreshToken)) {
        clearAuthStorage();
        if (isMounted) {
          setGuardState('unauthorized');
        }
        return;
      }

      try {
        await authService.restoreSession();
        const restoredUser = getStoredUser();
        const restoredHasAllowedRole = !allowedRoles || (restoredUser ? allowedRoles.includes(restoredUser.role) : false);

        if (!restoredUser) {
          clearAuthStorage();
          if (isMounted) {
            setGuardState('unauthorized');
          }
          return;
        }

        if (isMounted) {
          setGuardState(restoredHasAllowedRole ? 'authorized' : 'forbidden');
        }
      } catch {
        clearAuthStorage();
        if (isMounted) {
          setGuardState('unauthorized');
        }
      }
    };

    void authorize();

    return () => {
      isMounted = false;
    };
  }, [allowedRoles]);

  if (guardState === 'checking') {
    return null;
  }

  if (guardState === 'unauthorized') {
    return <Navigate to="/login" replace />;
  }

  if (guardState === 'forbidden') {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
