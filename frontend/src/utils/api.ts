import type { AxiosRequestConfig } from 'axios';
import { axiosInstance } from './axiosInstance';

export const api = {
  get<TResponse>(url: string, config?: AxiosRequestConfig) {
    return axiosInstance.get<TResponse>(url, config).then((response) => response.data);
  },

  post<TResponse, TBody = unknown>(url: string, body?: TBody, config?: AxiosRequestConfig) {
    return axiosInstance.post<TResponse>(url, body, config).then((response) => response.data);
  },

  put<TResponse, TBody = unknown>(url: string, body?: TBody, config?: AxiosRequestConfig) {
    return axiosInstance.put<TResponse>(url, body, config).then((response) => response.data);
  },

  patch<TResponse, TBody = unknown>(url: string, body?: TBody, config?: AxiosRequestConfig) {
    return axiosInstance.patch<TResponse>(url, body, config).then((response) => response.data);
  },

  delete<TResponse>(url: string, config?: AxiosRequestConfig) {
    return axiosInstance.delete<TResponse>(url, config).then((response) => response.data);
  },
};
