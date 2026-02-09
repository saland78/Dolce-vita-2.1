import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getOrders, updateOrderStatus } from '../api/api';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const OrderCard = ({ order, onUpdateStatus }) => {
    const statusColors = {
        received: 'border-yellow-400 bg-yellow-50/50',
        in_production: 'border-orange-400 bg-orange-50/50',
        ready: 'border-green-400 bg-green-50/50',
        delivered: 'border-gray-300 bg-gray-50/50',
    };

    return (
        <div className={`bg-white p-4 rounded-xl border-l-4 shadow-sm hover:shadow-md transition-all mb-4 ${statusColors[order.status] || 'border-gray-200'}`}>
            <div className="flex justify-between items-start mb-2">
                <div>
                    <h4 className="font-bold text-primary">{order.customer_name}</h4>
                    <p className="text-xs text-muted-foreground">{format(new Date(order.created_at), "d MMM HH:mm", { locale: it })}</p>
                </div>
                <span className="font-serif font-bold text-accent">€{order.total_amount}</span>
            </div>
            
            <div className="space-y-1 mb-4">
                {order.items.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-sm text-foreground/80">
                        <span>{item.quantity}x {item.product_name}</span>
                    </div>
                ))}
            </div>

            <div className="flex gap-2 mt-2">
                {order.status === 'received' && (
                    <button 
                        onClick={() => onUpdateStatus(order._id, 'in_production')}
                        className="w-full py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90"
                    >
                        Inizia Produzione
                    </button>
                )}
                {order.status === 'in_production' && (
                    <button 
                        onClick={() => onUpdateStatus(order._id, 'ready')}
                        className="w-full py-1.5 rounded-lg bg-accent text-white text-xs font-medium hover:bg-accent/90"
                    >
                        Segna Pronto
                    </button>
                )}
                {order.status === 'ready' && (
                    <button 
                        onClick={() => onUpdateStatus(order._id, 'delivered')}
                        className="w-full py-1.5 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700"
                    >
                        Consegna
                    </button>
                )}
            </div>
        </div>
    );
};

const KanbanColumn = ({ title, status, orders, onUpdateStatus }) => (
    <div className="flex-1 min-w-[300px] bg-muted/30 p-4 rounded-2xl">
        <h3 className="font-serif font-bold text-lg mb-4 text-primary flex items-center justify-between">
            {title}
            <span className="bg-white px-2 py-0.5 rounded-full text-xs shadow-sm text-muted-foreground">{orders.length}</span>
        </h3>
        <div className="space-y-3">
            {orders.map(order => (
                <OrderCard key={order._id} order={order} onUpdateStatus={onUpdateStatus} />
            ))}
            {orders.length === 0 && (
                <div className="h-20 border-2 border-dashed border-border rounded-xl flex items-center justify-center text-muted-foreground text-sm">
                    Nessun ordine
                </div>
            )}
        </div>
    </div>
);

const Orders = () => {
    const [orders, setOrders] = useState([]);

    const fetchOrders = async () => {
        const data = await getOrders();
        setOrders(data);
    };

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 3000); // Fast polling for orders
        return () => clearInterval(interval);
    }, []);

    const handleUpdateStatus = async (id, status) => {
        await updateOrderStatus(id, status);
        fetchOrders();
    };

    return (
        <Layout>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-serif text-primary">Gestione Ordini</h1>
                <div className="text-sm text-muted-foreground">Syncing: 3s</div>
            </div>

            <div className="flex gap-6 overflow-x-auto pb-6">
                <KanbanColumn 
                    title="Ricevuti" 
                    status="received" 
                    orders={orders.filter(o => o.status === 'received')} 
                    onUpdateStatus={handleUpdateStatus} 
                />
                <KanbanColumn 
                    title="In Produzione" 
                    status="in_production" 
                    orders={orders.filter(o => o.status === 'in_production')} 
                    onUpdateStatus={handleUpdateStatus} 
                />
                <KanbanColumn 
                    title="Pronti" 
                    status="ready" 
                    orders={orders.filter(o => o.status === 'ready')} 
                    onUpdateStatus={handleUpdateStatus} 
                />
                <KanbanColumn 
                    title="Completati" 
                    status="delivered" 
                    orders={orders.filter(o => o.status === 'delivered')} 
                    onUpdateStatus={handleUpdateStatus} 
                />
            </div>
        </Layout>
    );
};

export default Orders;
