import axios from 'axios';

// PREVIEW COMPATIBLE URL
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
export const createIngredient = async (data) => (await api.post('/inventory/ingredients', data)).data;
export const updateIngredient = async (id, data) => (await api.put(`/inventory/ingredients/${id}`, data)).data; // NEW
export const deleteIngredient = async (id) => (await api.delete(`/inventory/ingredients/${id}`)).data; // NEW

export const getProducts = async () => (await api.get('/inventory/products')).data;
export const getProductOrders = async (productId) => (await api.get(`/inventory/products/${productId}/orders`)).data;
export const seedInventory = async () => (await api.post('/inventory/seed')).data;

// Customers
export const getCustomers = async () => (await api.get('/customers')).data;

// PDF
export const downloadProductionSheet = async (orderId) => {
    const response = await api.get(`/orders/${orderId}/production-sheet`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `scheda_${orderId}.pdf`);
    document.body.appendChild(link);
    link.click();
};

export const getDailySlots = async () => (await api.get('/orders/daily-slots')).data;
export const getDailyIngredients = async (date) => (await api.get(`/production/ingredients${date ? `?date=${date}` : ''}`)).data;

export default api;
