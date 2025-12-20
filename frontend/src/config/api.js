/**
 * API konfigurácia
 * Automaticky používa HTTPS, ak je dostupný (pre lokálny vývoj s SSL)
 */

// Detekcia, či používame HTTPS
const isHTTPS = window.location.protocol === "https:";

// API URL - automaticky používa HTTPS, ak je frontend na HTTPS
const getApiUrl = () => {
  // Vite používa import.meta.env namiesto process.env
  const apiUrl = import.meta.env.VITE_API_URL;

  if (apiUrl) {
    return apiUrl;
  }

  // Ak je frontend na HTTPS, použij HTTPS aj pre backend
  if (isHTTPS) {
    return "https://localhost:8000";
  }

  // Inak použij HTTP
  return "http://localhost:8000";
};

export const API_URL = getApiUrl();

// Export pre použitie v komponentoch
export default API_URL;
