import axios from 'axios';

// FORCE HTTPS URL
const backendUrl = "https://sweettrack-4.preview.emergentagent.com";

console.log("Using Backend URL:", backendUrl);

const api = axios.create({
  baseURL: backendUrl,
});

// Add interceptor to debug requests
api.interceptors.request.use(request => {
  console.log('Starting Request', request.url, request.baseURL);
  return request;
});

export const getStats = async () => (await api.get('/api/orders/stats')).data;
// Added trailing slash to avoid 307 Redirect to HTTP
export const getOrders = async (status) => (await api.get(`/api/orders/${status ? `?status=${status}` : ''}`)).data;
export const updateOrderStatus = async (id, status) => (await api.put(`/api/orders/${id}/status?status=${status}`)).data;
export const simulateOrder = async () => (await api.post('/api/orders/simulate')).data;

export const getIngredients = async () => (await api.get('/api/inventory/ingredients')).data;
export const getProducts = async () => (await api.get('/api/inventory/products')).data;
export const seedInventory = async () => (await api.post('/api/inventory/seed')).data;

export default api;
