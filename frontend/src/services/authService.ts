import type { AuthUser, LoginRequest, LoginResponse, RefreshRequest, RefreshResponse, UserRole } from '../types/auth';
import { api } from '../utils/api';
import { clearAuthStorage, getStoredUser, setAuthStorage } from '../utils/authStorage';

const LOGIN_URL = '/api/auth/login/';
const REFRESH_URL = '/api/auth/refresh/';

export const authService = {
  login(payload: LoginRequest) {
    return api.post<LoginResponse, LoginRequest>(LOGIN_URL, payload).then((response) => {
      setAuthStorage(response);
      return response;
    });
  },

  refresh(refresh: string) {
    const payload: RefreshRequest = { refresh };
    return api.post<RefreshResponse, RefreshRequest>(REFRESH_URL, payload);
  },

  logout() {
    clearAuthStorage();
  },

  getCurrentUser() {
    return getStoredUser();
  },

  hasRole(user: AuthUser | null, roles: UserRole[]) {
    if (!user) {
      return false;
    }

    return roles.includes(user.role);
  },
};
