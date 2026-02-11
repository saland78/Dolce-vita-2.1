import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getOrders, updateOrderStatus, archiveOrder } from '../api/api';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Archive, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';

const OrderCard = ({ order, onUpdateStatus, onArchive }) => {
    const statusColors = {
        received: 'border-yellow-400 bg-yellow-50/50',
        in_production: 'border-orange-400 bg-orange-50/50',
        ready: 'border-blue-400 bg-blue-50/50', 
        delivered: 'border-green-400 bg-green-50/50', 
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
                        className="w-full py-1.5 rounded-lg bg-orange-500 text-white text-xs font-medium hover:bg-orange-600"
                    >
                        Inizia Produzione
                    </button>
                )}
                {order.status === 'in_production' && (
                    <button 
                        onClick={() => onUpdateStatus(order._id, 'ready')}
                        className="w-full py-1.5 rounded-lg bg-blue-500 text-white text-xs font-medium hover:bg-blue-600"
                    >
                        Pronto per Ritiro
                    </button>
                )}
                {order.status === 'ready' && (
                    <button 
                        onClick={() => onUpdateStatus(order._id, 'delivered')}
                        className="w-full py-1.5 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700"
                    >
                        Consegna & Incassa
                    </button>
                )}
                {order.status === 'delivered' && (
                    <div className="flex gap-2 w-full">
                        <div className="flex-1 text-center text-xs font-bold text-green-700 bg-green-100 py-1.5 rounded-lg flex items-center justify-center gap-1">
                            COMPLETATO
                        </div>
                        {onArchive && (
                            <button 
                                onClick={() => onArchive(order._id)}
                                title="Archivia ordine"
                                className="px-2 rounded-lg bg-gray-200 text-gray-600 hover:bg-gray-300"
                            >
                                <Archive size={14} />
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const KanbanColumn = ({ title, orders, onUpdateStatus, onArchive }) => (
    <div className="flex-1 min-w-[300px] bg-muted/30 p-4 rounded-2xl">
        <h3 className="font-serif font-bold text-lg mb-4 text-primary flex items-center justify-between">
            {title}
            <span className="bg-white px-2 py-0.5 rounded-full text-xs shadow-sm text-muted-foreground">{orders.length}</span>
        </h3>
        <div className="space-y-3">
            {orders.map(order => (
                <OrderCard key={order._id} order={order} onUpdateStatus={onUpdateStatus} onArchive={onArchive} />
            ))}
            {orders.length === 0 && (
                <div className="h-20 border-2 border-dashed border-border rounded-xl flex items-center justify-center text-muted-foreground text-sm">
                    Vuoto
                </div>
            )}
        </div>
    </div>
);

const Orders = () => {
    const [orders, setOrders] = useState([]);
    const [showArchived, setShowArchived] = useState(false);

    const fetchOrders = async () => {
        try {
            const data = await getOrders(null, showArchived);
            setOrders(data);
        } catch (e) {
            console.error("Error fetching orders", e);
        }
    };

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 5000); 
        return () => clearInterval(interval);
    }, [showArchived]); // Refresh when toggling archive

    const handleUpdateStatus = async (id, status) => {
        await updateOrderStatus(id, status);
        fetchOrders();
    };

    const handleArchive = async (id) => {
        await archiveOrder(id);
        toast.success("Ordine archiviato");
        fetchOrders();
    };

    return (
        <Layout>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-serif text-primary">
                    {showArchived ? "Archivio Ordini" : "Gestione Ordini"}
                </h1>
                
                <div className="flex items-center gap-4">
                    <div className="text-sm text-muted-foreground">Sync: 5s</div>
                    <button 
                        onClick={() => setShowArchived(!showArchived)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                            showArchived 
                            ? 'bg-primary text-white' 
                            : 'bg-white border border-border text-gray-600 hover:bg-gray-50'
                        }`}
                    >
                        {showArchived ? <RotateCcw size={16} /> : <Archive size={16} />}
                        {showArchived ? "Torna a Lavagna" : "Vedi Archivio"}
                    </button>
                </div>
            </div>

            {showArchived ? (
                // Archive View (Simple List)
                <div className="space-y-4">
                    {orders.map(order => (
                        <div key={order._id} className="bg-white p-4 rounded-xl border border-border shadow-sm flex justify-between items-center opacity-75">
                            <div>
                                <h4 className="font-bold text-primary">{order.customer_name}</h4>
                                <p className="text-xs text-muted-foreground">{format(new Date(order.created_at), "d MMM yyyy", { locale: it })} • {order.items.length} articoli</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="font-serif font-bold text-accent">€{order.total_amount}</span>
                                <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-xs uppercase font-bold">
                                    {order.status}
                                </span>
                            </div>
                        </div>
                    ))}
                    {orders.length === 0 && <p className="text-center text-muted-foreground py-10">Archivio vuoto</p>}
                </div>
            ) : (
                // Kanban View
                <div className="flex gap-6 overflow-x-auto pb-6">
                    <KanbanColumn 
                        title="Ricevuti" 
                        orders={orders.filter(o => o.status === 'received')} 
                        onUpdateStatus={handleUpdateStatus} 
                    />
                    <KanbanColumn 
                        title="In Produzione" 
                        orders={orders.filter(o => o.status === 'in_production')} 
                        onUpdateStatus={handleUpdateStatus} 
                    />
                    <KanbanColumn 
                        title="Pronti" 
                        orders={orders.filter(o => o.status === 'ready')} 
                        onUpdateStatus={handleUpdateStatus} 
                    />
                    <KanbanColumn 
                        title="Completati" 
                        orders={orders.filter(o => o.status === 'delivered')} 
                        onUpdateStatus={handleUpdateStatus} 
                        onArchive={handleArchive}
                    />
                </div>
            )}
        </Layout>
    );
};

export default Orders;
