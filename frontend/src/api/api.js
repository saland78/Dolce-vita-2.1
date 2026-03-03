import axios from 'axios';

// PREVIEW COMPATIBLE URL
// Use relative path so Nginx/Proxy handles it
const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

// Auth (Emergent Style)
export const login = async (sessionId) => (await api.post('/auth/session', { session_id: sessionId })).data;
export const getCurrentUser = async () => (await api.get('/auth/me')).data;
export const logout = async () => (await api.post('/auth/logout')).data;

// Settings
export const getSettings = async () => (await api.get('/settings')).data;
export const updateSettings = async (data) => (await api.put('/settings', data)).data;

// Orders
export const getStats = async () => (await api.get('/orders/stats')).data;
export const getSalesHistory = async (range) => (await api.get(`/orders/sales-history?range=${range || '7d'}`)).data;
export const getOrders = async (status, archived = false) => (await api.get(`/orders/?archived=${archived}${status ? `&status=${status}` : ''}`)).data;
export const updateOrderStatus = async (id, status) => (await api.put(`/orders/${id}/status?status=${status}`)).data;
export const archiveOrder = async (id) => (await api.put(`/orders/${id}/archive`)).data;
export const simulateOrder = async () => (await api.post('/orders/simulate')).data;

// Production Plan
export const getProductionPlan = async (date) => (await api.get(`/orders/production-plan?date=${date}`)).data;
export const toggleProductionStatus = async (data) => (await api.post('/orders/production-plan/toggle', data)).data;

// Inventory & Products
export const getIngredients = async () => (await api.get('/inventory/ingredients')).data;
export const getProducts = async () => (await api.get('/inventory/products')).data;
export const getProductOrders = async (productId) => (await api.get(`/inventory/products/${productId}/orders`)).data;
export const seedInventory = async () => (await api.post('/inventory/seed')).data;

// Customers
export const getCustomers = async () => (await api.get('/customers')).data;

export default api;
