const host = typeof window !== 'undefined' && window.location.hostname ? window.location.hostname : 'localhost';

export const environment = {
  production: false,
  apiBaseUrl: `http://${host}:8090`,
};