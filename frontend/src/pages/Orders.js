import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getOrders, updateOrderStatus, archiveOrder, downloadProductionSheet } from '../api/api';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { Archive, AlertTriangle, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';

const statusColors = {
    received: 'border-yellow-400 bg-yellow-50/50',
    in_production: 'border-orange-400 bg-orange-50/50',
    ready: 'border-blue-400 bg-blue-50/50',
    delivered: 'border-green-400 bg-green-50/50',
};

const OrderCard = ({ order, onUpdateStatus, onArchive, onDownloadPDF }) => {
    const [expanded, setExpanded] = useState(false);
    const hasAllergens = order.items.some(i => i.meta?.allergens_note);

    return (
        <div className={`bg-white rounded-xl border-l-4 shadow-sm hover:shadow-md transition-all mb-3 ${statusColors[order.status] || 'border-gray-200'}`}>
            {/* Header sempre visibile */}
            <div
                className="flex justify-between items-center p-4 cursor-pointer"
                onClick={() => setExpanded(v => !v)}
            >
                <div className="flex-1 min-w-0">
                    <h4 className="font-bold text-primary flex items-center gap-2 truncate">
                        {order.customer_name}
                        {hasAllergens && <AlertTriangle size={14} className="text-red-600 flex-shrink-0 animate-pulse" />}
                    </h4>
                    <p className="text-xs text-muted-foreground">
                        {format(new Date(order.created_at), "d MMM HH:mm", { locale: it })}
                        {order.pickup_date && <span className="ml-2">• Ritiro: {order.pickup_date}</span>}
                    </p>
                </div>
                <div className="flex items-center gap-2 ml-2 flex-shrink-0">
                    <span className="font-serif font-bold text-accent">€{order.total_amount?.toFixed(2)}</span>
                    <button
                        onClick={e => { e.stopPropagation(); onDownloadPDF(order._id); }}
                        title="Scheda PDF"
                        className="p-1.5 rounded-lg bg-gray-100 text-gray-500 hover:bg-primary hover:text-white transition-colors"
                    >
                        <FileText size={14} />
                    </button>
                    {expanded ? <ChevronUp size={16} className="text-muted-foreground" /> : <ChevronDown size={16} className="text-muted-foreground" />}
                </div>
            </div>

            {/* Dettagli espandibili */}
            {expanded && (
                <div className="px-4 pb-4 border-t border-border/50 pt-3">
                    <div className="space-y-1 mb-3">
                        {order.items.map((item, idx) => (
                            <div key={idx} className="flex justify-between text-sm text-foreground/80">
                                <span>{item.quantity}x {item.product_name}</span>
                                {item.meta?.allergens_note && (
                                    <span className="text-xs text-red-500 italic ml-2">{item.meta.allergens_note}</span>
                                )}
                            </div>
                        ))}
                    </div>
                    {order.notes && (
                        <p className="text-xs text-muted-foreground italic bg-muted/30 rounded px-2 py-1 mb-3">📝 {order.notes}</p>
                    )}
                    <div className="flex gap-2">
                        {order.status === 'received' && (
                            <button onClick={() => onUpdateStatus(order._id, 'in_production')}
                                className="flex-1 py-2 rounded-lg bg-orange-500 text-white text-xs font-medium hover:bg-orange-600">
                                Inizia Produzione
                            </button>
                        )}
                        {order.status === 'in_production' && (
                            <button onClick={() => onUpdateStatus(order._id, 'ready')}
                                className="flex-1 py-2 rounded-lg bg-blue-500 text-white text-xs font-medium hover:bg-blue-600">
                                Pronto per Ritiro
                            </button>
                        )}
                        {order.status === 'ready' && (
                            <button onClick={() => onUpdateStatus(order._id, 'delivered')}
                                className="flex-1 py-2 rounded-lg bg-green-600 text-white text-xs font-medium hover:bg-green-700">
                                Consegna & Incassa
                            </button>
                        )}
                        {order.status === 'delivered' && (
                            <div className="flex gap-2 w-full">
                                <div className="flex-1 text-center text-xs font-bold text-green-700 bg-green-100 py-2 rounded-lg flex items-center justify-center gap-1">
                                    ✓ COMPLETATO
                                </div>
                                {onArchive && (
                                    <button onClick={() => onArchive(order._id)}
                                        className="px-3 rounded-lg bg-gray-200 text-gray-600 hover:bg-gray-300">
                                        <Archive size={14} />
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

/* ── Desktop: colonna kanban ── */
const KanbanColumn = ({ title, orders, onUpdateStatus, onArchive, onDownloadPDF, color }) => (
    <div className="flex-1 min-w-[260px]">
        <div className={`flex items-center gap-2 mb-4 px-4 py-2 rounded-xl ${color}`}>
            <h3 className="font-serif font-semibold text-primary">{title}</h3>
            <span className="ml-auto bg-white/60 text-primary text-xs font-bold px-2 py-0.5 rounded-full">{orders.length}</span>
        </div>
        {orders.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-8 border-2 border-dashed border-border rounded-xl">
                Nessun ordine
            </div>
        ) : orders.map(order => (
            <OrderCard key={order._id} order={order}
                onUpdateStatus={onUpdateStatus} onArchive={onArchive} onDownloadPDF={onDownloadPDF} />
        ))}
    </div>
);

/* ── Mobile: lista per stato con tab ── */
const COLUMNS = [
    { key: 'received',    title: '📥 Ricevuti',      color: 'bg-yellow-50 border border-yellow-200' },
    { key: 'in_production', title: '👨‍🍳 In Prod.',   color: 'bg-orange-50 border border-orange-200' },
    { key: 'ready',       title: '✅ Pronti',         color: 'bg-blue-50 border border-blue-200' },
    { key: 'delivered',   title: '🎁 Consegnati',     color: 'bg-green-50 border border-green-200' },
];

const Orders = () => {
    const [orders, setOrders] = useState([]);
    const [showArchived, setShowArchived] = useState(false);
    const [mobileTab, setMobileTab] = useState('received');

    const fetchOrders = async () => {
        try {
            const data = await getOrders(null, showArchived);
            setOrders(data);
        } catch (e) {
            console.error('Error fetching orders', e);
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
            toast.success('Stato aggiornato');
            fetchOrders();
        } catch (e) {
            toast.error('Errore aggiornamento stato');
        }
    };

    const handleArchive = async (id) => {
        try {
            await archiveOrder(id);
            toast.success('Ordine archiviato');
            fetchOrders();
        } catch (e) {
            toast.error('Errore archiviazione');
        }
    };

    const handleDownloadPDF = async (id) => {
        try {
            toast.info('Generazione PDF...');
            await downloadProductionSheet(id);
            toast.success('PDF scaricato!');
        } catch (e) {
            toast.error('Errore generazione PDF');
        }
    };

    return (
        <Layout>
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h1 className="text-2xl md:text-3xl font-serif text-primary">Gestione Ordini</h1>
                    <p className="text-muted-foreground text-sm">Kanban • aggiornamento ogni 5s</p>
                </div>
                <button
                    onClick={() => setShowArchived(v => !v)}
                    className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-all ${showArchived ? 'bg-primary text-white border-primary' : 'bg-white text-muted-foreground border-border hover:bg-muted'}`}
                >
                    {showArchived ? 'Attivi' : 'Archiviati'}
                </button>
            </div>

            {/* Desktop: kanban orizzontale */}
            <div className="hidden md:flex gap-4 overflow-x-auto pb-4">
                {COLUMNS.map(col => (
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

            {/* Mobile: tab + lista */}
            <div className="md:hidden">
                {/* Tab bar */}
                <div className="flex overflow-x-auto gap-1 mb-4 bg-white rounded-xl border border-border p-1">
                    {COLUMNS.map(col => {
                        const count = orders.filter(o => o.status === col.key).length;
                        return (
                            <button
                                key={col.key}
                                onClick={() => setMobileTab(col.key)}
                                className={`flex-1 min-w-0 py-2 px-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap
                                    ${mobileTab === col.key ? 'bg-primary text-white' : 'text-muted-foreground hover:bg-muted'}`}
                            >
                                {col.title} {count > 0 && <span className="ml-1 bg-white/20 px-1 rounded-full">{count}</span>}
                            </button>
                        );
                    })}
                </div>
                {/* Lista ordini tab attivo */}
                {orders.filter(o => o.status === mobileTab).length === 0 ? (
                    <div className="text-center text-muted-foreground text-sm py-12 border-2 border-dashed border-border rounded-xl">
                        Nessun ordine
                    </div>
                ) : (
                    orders.filter(o => o.status === mobileTab).map(order => (
                        <OrderCard key={order._id} order={order}
                            onUpdateStatus={handleUpdateStatus}
                            onArchive={handleArchive}
                            onDownloadPDF={handleDownloadPDF}
                        />
                    ))
                )}
            </div>
        </Layout>
    );
};

export default Orders;
