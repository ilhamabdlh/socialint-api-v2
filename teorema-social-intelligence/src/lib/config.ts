/**
 * Application Configuration
 * 
 * To change the API URL, create a .env.local file with:
 * VITE_API_URL=https://api.staging.teoremaintelligence.com
 * VITE_API_PREFIX=/api/v1
 */

// API Configuration dengan validasi
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = import.meta.env.VITE_API_PREFIX || '/api/v1';

// Export constants untuk digunakan di seluruh aplikasi
export const API_CONFIG = {
  baseUrl: API_BASE_URL,
  prefix: API_PREFIX,
  fullUrl: `${API_BASE_URL}${API_PREFIX}`,
};

// Export individual untuk backward compatibility
export const API_BASE_URL_EXPORT = API_BASE_URL;
export const API_PREFIX_EXPORT = API_PREFIX;

// App config (optional)
export const config = {
  apiUrl: API_BASE_URL,
  apiPrefix: API_PREFIX,
  appName: import.meta.env.VITE_APP_NAME || 'Social Intelligence Dashboard',
  appVersion: import.meta.env.VITE_APP_VERSION || '2.1.0',
};

export default config;

