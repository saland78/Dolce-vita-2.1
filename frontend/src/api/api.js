import axios from 'axios';

// FORCE HTTPS URL - Explicit HTTPS configuration
const backendUrl = "https://sweettrack-4.preview.emergentagent.com";

console.log("Using Backend URL:", backendUrl);

const api = axios.create({
  baseURL: backendUrl,
  // Force HTTPS protocol
  httpsAgent: false,
  // Ensure no HTTP fallback
  maxRedirects: 0,
  // Add explicit headers
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add interceptor to debug and ensure HTTPS requests
api.interceptors.request.use(request => {
  // Force HTTPS in the final URL
  const fullUrl = `${request.baseURL}${request.url}`;
  if (fullUrl.startsWith('http://')) {
    console.error('BLOCKING HTTP REQUEST:', fullUrl);
    throw new Error('HTTP requests not allowed - HTTPS required');
  }
  console.log('Starting HTTPS Request', request.url, request.baseURL);
  console.log('Full URL:', fullUrl);
  return request;
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log('Response received from:', response.config.url);
    return response;
  },
  error => {
    console.error('API Error:', error.message);
    if (error.message.includes('Mixed Content')) {
      console.error('MIXED CONTENT ERROR - Check HTTPS configuration');
    }
    throw error;
  }
);

export const getStats = async () => (await api.get('/api/orders/stats')).data;
export const getOrders = async (status) => (await api.get(`/api/orders${status ? `?status=${status}` : ''}`)).data;
export const updateOrderStatus = async (id, status) => (await api.put(`/api/orders/${id}/status?status=${status}`)).data;
export const simulateOrder = async () => (await api.post('/api/orders/simulate')).data;

export const getIngredients = async () => (await api.get('/api/inventory/ingredients')).data;
export const getProducts = async () => (await api.get('/api/inventory/products')).data;
export const seedInventory = async () => (await api.post('/api/inventory/seed')).data;

export default api;
