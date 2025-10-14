/**
 * Application Configuration
 * 
 * To change the API URL, create a .env.local file with:
 * VITE_API_URL=http://localhost:8000
 */

export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'Social Intelligence Dashboard',
  appVersion: import.meta.env.VITE_APP_VERSION || '2.1.0',
};

export default config;

