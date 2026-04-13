import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';
import type { RefreshResponse } from '../types/auth';
import { clearAuthStorage, getAccessToken, getRefreshToken, updateAccessToken } from './authStorage';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8080';
const LOGIN_URL = '/api/auth/login/';
const REFRESH_URL = '/api/auth/refresh/';

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let refreshPromise: Promise<string> | null = null;

function setAuthorizationHeader(config: AxiosRequestConfig, token: string) {
  config.headers = config.headers ?? {};

  if (typeof config.headers.set === 'function') {
    config.headers.set('Authorization', `Bearer ${token}`);
    return;
  }

  Object.assign(config.headers, {
    Authorization: `Bearer ${token}`,
  });
}

async function requestTokenRefresh() {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    throw new Error('Refresh token is missing');
  }

  const response = await refreshClient.post<RefreshResponse>(REFRESH_URL, {
    refresh: refreshToken,
  });

  updateAccessToken(response.data.access);
  return response.data.access;
}

axiosInstance.interceptors.request.use((config) => {
  const accessToken = getAccessToken();

  if (accessToken) {
    setAuthorizationHeader(config, accessToken);
  }

  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const originalRequest = error.config as RetriableRequestConfig | undefined;
    const requestUrl = originalRequest?.url ?? '';
    const isAuthRequest = requestUrl.includes(LOGIN_URL) || requestUrl.includes(REFRESH_URL);

    if (!originalRequest || status !== 401 || originalRequest._retry || isAuthRequest) {
      if (isAuthRequest && status === 401 && requestUrl.includes(REFRESH_URL)) {
        clearAuthStorage();
      }

      throw error;
    }

    try {
      originalRequest._retry = true;

      if (!refreshPromise) {
        refreshPromise = requestTokenRefresh();
      }

      const nextAccessToken = await refreshPromise;
      setAuthorizationHeader(originalRequest, nextAccessToken);

      return axiosInstance(originalRequest);
    } catch (refreshError) {
      clearAuthStorage();
      window.location.href = '/unauthorized';
      throw refreshError;
    } finally {
      refreshPromise = null;
    }
  },
);
