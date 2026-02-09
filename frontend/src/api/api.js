import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || "http://localhost:8001",
});

export const getStats = async () => (await api.get('/api/orders/stats')).data;
export const getOrders = async (status) => (await api.get(`/api/orders${status ? `?status=${status}` : ''}`)).data;
export const updateOrderStatus = async (id, status) => (await api.put(`/api/orders/${id}/status?status=${status}`)).data;
export const simulateOrder = async () => (await api.post('/api/orders/simulate')).data;

export const getIngredients = async () => (await api.get('/api/inventory/ingredients')).data;
export const getProducts = async () => (await api.get('/api/inventory/products')).data;
export const seedInventory = async () => (await api.post('/api/inventory/seed')).data;

export default api;
