import axios from 'axios';

// FORCE HTTPS URL
const backendUrl = "https://sweettrack-4.preview.emergentagent.com";

const api = axios.create({
  baseURL: backendUrl,
  withCredentials: true,
});

// Auth
export const login = async (sessionId) => (await api.post('/api/auth/session', { session_id: sessionId })).data;
export const getCurrentUser = async () => (await api.get('/api/auth/me')).data;
export const logout = async () => (await api.post('/api/auth/logout')).data;

// Orders
export const getStats = async () => (await api.get('/api/orders/stats')).data;
export const getSalesHistory = async (range) => (await api.get(`/api/orders/sales-history?range=${range || '7d'}`)).data;
export const getOrders = async (status) => (await api.get(`/api/orders/${status ? `?status=${status}` : ''}`)).data;
export const updateOrderStatus = async (id, status) => (await api.put(`/api/orders/${id}/status?status=${status}`)).data;
export const simulateOrder = async () => (await api.post('/api/orders/simulate')).data;
export const getProductionPlan = async (date) => (await api.get('/api/orders/production-plan')).data;

// Inventory & Products
export const getIngredients = async () => (await api.get('/api/inventory/ingredients')).data;
export const getProducts = async () => (await api.get('/api/inventory/products')).data;
export const getProductOrders = async (productId) => (await api.get(`/api/inventory/products/${productId}/orders`)).data;
export const seedInventory = async () => (await api.post('/api/inventory/seed')).data;

// Customers
export const getCustomers = async () => (await api.get('/api/customers')).data;

export default api;
