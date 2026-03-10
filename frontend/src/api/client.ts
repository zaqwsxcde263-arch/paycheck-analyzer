import axios from "axios";
import { useAuth } from "../state/AuthContext";

export const api = axios.create({
  baseURL: "/api/v1"
});

export const useAuthorizedApi = () => {
  const { token } = useAuth();

  api.interceptors.request.use((config) => {
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  return api;
};

