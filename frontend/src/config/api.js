/**
 * API konfigurácia
 * Automaticky používa HTTPS, ak je dostupný (pre lokálny vývoj s SSL)
 */

// Detekcia, či používame HTTPS
const isHTTPS = window.location.protocol === "https:";

// API URL - automaticky používa HTTPS, ak je frontend na HTTPS
const getApiUrl = () => {
  // Vite používa import.meta.env namiesto process.env
  const apiUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL;

  if (apiUrl) {
    return apiUrl;
  }

  // Ak je frontend na HTTPS, použij HTTPS aj pre backend
  if (isHTTPS) {
    return "https://localhost:8000";
  }

  // Inak použij HTTP
  return "http://127.0.0.1:8000";
};

export const API_URL = getApiUrl();

if (import.meta.env.PROD && API_URL.includes("localhost")) {
  throw new Error("Invalid production API config: localhost API URL is not allowed");
}

export const ENDPOINTS = {
  SEARCH: {
    CZ: `${API_URL}/api/company`,
    SK: `${API_URL}/api/sk/company`,
    PL: `${API_URL}/api/pl/company`,
    HU: `${API_URL}/api/hu/company`,
    V4: `${API_URL}/api/v4/search`,
    AUTOCOMPLETE: `${API_URL}/api/sk/autocomplete`,
  },
  AUTH: {
    LOGIN: `${API_URL}/api/auth/login`,
    REGISTER: `${API_URL}/api/auth/register`,
    ME: `${API_URL}/api/auth/me`,
    LIMITS: `${API_URL}/api/auth/tier/limits`,
  },
  USER: {
    HISTORY: `${API_URL}/api/search/history`,
    FAVORITES: `${API_URL}/api/user/favorites`,
  }
};

export default API_URL;
