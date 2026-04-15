import type { AuthUser, LoginRequest, LoginResponse, RefreshRequest, RefreshResponse, UserRole } from '../types/auth';
import { api } from '../utils/api';
import { clearAuthStorage, getRefreshToken, getStoredUser, setAuthStorage, updateAccessToken } from '../utils/authStorage';
import { isJwtExpired } from '../utils/jwt';

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

  async restoreSession() {
    const refreshToken = getRefreshToken();

    if (!refreshToken || isJwtExpired(refreshToken)) {
      clearAuthStorage();
      return null;
    }

    const response = await this.refresh(refreshToken);
    updateAccessToken(response.access);

    return {
      access: response.access,
      user: getStoredUser(),
    };
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
