import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getOrders, updateOrderStatus, archiveOrder, downloadProductionSheet } from '../api/api';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Archive, AlertTriangle, FileText } from 'lucide-react';
import { toast } from 'sonner';

const OrderCard = ({ order, onUpdateStatus, onArchive, onDownloadPDF }) => {
    const statusColors = {
        received: 'border-yellow-400 bg-yellow-50/50',
        in_production: 'border-orange-400 bg-orange-50/50',
        ready: 'border-blue-400 bg-blue-50/50',
        delivered: 'border-green-400 bg-green-50/50',
    };

    const hasAllergens = order.items.some(i => i.meta?.allergens_note);

    return (
        <div className={`bg-white p-4 rounded-xl border-l-4 shadow-sm hover:shadow-md transition-all mb-4 ${statusColors[order.status] || 'border-gray-200'}`}>
            <div className="flex justify-between items-start mb-2">
                <div>
                    <h4 className="font-bold text-primary flex items-center gap-2">
                        {order.customer_name}
                        {hasAllergens && (
                            <span title="Contiene Allergeni" className="text-red-600 animate-pulse">
                                <AlertTriangle size={16} />
                            </span>
                        )}
                    </h4>
                    <p className="text-xs text-muted-foreground">{format(new Date(order.created_at), "d MMM HH:mm", { locale: it })}</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="font-serif font-bold text-accent">€{order.total_amount?.toFixed(2)}</span>
                    <button
                        onClick={() => onDownloadPDF(order._id)}
                        title="Scarica scheda di produzione PDF"
                        className="p-1.5 rounded-lg bg-gray-100 text-gray-500 hover:bg-primary hover:text-white transition-colors"
                    >
                        <FileText size={15} />
                    </button>
                </div>
            </div>

            <div className="space-y-1 mb-4">
                {order.items.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-sm text-foreground/80">
                        <span>{item.quantity}x {item.product_name}</span>
                        {item.meta?.allergens_note && (
                            <span className="text-xs text-red-500 italic">{item.meta.allergens_note}</span>
                        )}
                    </div>
                ))}
            </div>

            {order.notes && (
                <p className="text-xs text-muted-foreground italic bg-muted/30 rounded px-2 py-1 mb-3">📝 {order.notes}</p>
            )}

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
                            ✓ COMPLETATO
                        </div>
                        {onArchive && (
                            <button
                                onClick={() => onArchive(order._id)}
                                title="Archivia ordine"
                                className="px-2 rounded-lg bg-gray-200 text-gray-600 hover:bg-gray-300"
                            >
                                <Archive size={15} />
                            </button>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const KanbanColumn = ({ title, orders, onUpdateStatus, onArchive, onDownloadPDF, color }) => (
    <div className="flex-1 min-w-[260px]">
        <div className={`flex items-center gap-2 mb-4 px-4 py-2 rounded-xl ${color}`}>
            <h3 className="font-serif font-semibold text-primary">{title}</h3>
            <span className="ml-auto bg-white/60 text-primary text-xs font-bold px-2 py-0.5 rounded-full">{orders.length}</span>
        </div>
        <div>
            {orders.length === 0 && (
                <div className="text-center text-muted-foreground text-sm py-8 border-2 border-dashed border-border rounded-xl">
                    Nessun ordine
                </div>
            )}
            {orders.map(order => (
                <OrderCard
                    key={order._id}
                    order={order}
                    onUpdateStatus={onUpdateStatus}
                    onArchive={onArchive}
                    onDownloadPDF={onDownloadPDF}
                />
            ))}
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
    }, [showArchived]);

    const handleUpdateStatus = async (id, status) => {
        try {
            await updateOrderStatus(id, status);
            toast.success("Stato aggiornato");
            fetchOrders();
        } catch (e) {
            toast.error("Errore aggiornamento stato");
        }
    };

    const handleArchive = async (id) => {
        try {
            await archiveOrder(id);
            toast.success("Ordine archiviato");
            fetchOrders();
        } catch (e) {
            toast.error("Errore archiviazione");
        }
    };

    const handleDownloadPDF = async (id) => {
        try {
            toast.info("Generazione PDF...");
            await downloadProductionSheet(id);
            toast.success("PDF scaricato!");
        } catch (e) {
            toast.error("Errore generazione PDF");
        }
    };

    const columns = [
        { key: 'received', title: '📥 Ricevuti', color: 'bg-yellow-50 border border-yellow-200' },
        { key: 'in_production', title: '👨‍🍳 In Produzione', color: 'bg-orange-50 border border-orange-200' },
        { key: 'ready', title: '✅ Pronti', color: 'bg-blue-50 border border-blue-200' },
        { key: 'delivered', title: '🎁 Consegnati', color: 'bg-green-50 border border-green-200' },
    ];

    return (
        <Layout>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Gestione Ordini</h1>
                    <p className="text-muted-foreground">Kanban in tempo reale • aggiornamento ogni 5 secondi</p>
                </div>
                <button
                    onClick={() => setShowArchived(v => !v)}
                    className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${showArchived ? 'bg-primary text-white border-primary' : 'bg-white text-muted-foreground border-border hover:bg-muted'}`}
                >
                    {showArchived ? 'Vedi Attivi' : 'Vedi Archiviati'}
                </button>
            </div>

            <div className="flex gap-4 overflow-x-auto pb-4">
                {columns.map(col => (
                    <KanbanColumn
                        key={col.key}
                        title={col.title}
                        color={col.color}
                        orders={orders.filter(o => o.status === col.key)}
                        onUpdateStatus={handleUpdateStatus}
                        onArchive={handleArchive}
                        onDownloadPDF={handleDownloadPDF}
                    />
                ))}
            </div>
        </Layout>
    );
};

export default Orders;
