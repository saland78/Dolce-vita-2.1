import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getDailySlots, getDailyIngredients, updateOrderStatus, downloadProductionSheet } from '../api/api';
import { 
    Calendar, Clock, Printer, ChevronDown, ChevronUp, 
    AlertTriangle, CheckCircle, Circle, RefreshCw 
} from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';
import { toast } from 'sonner';

const OrderItem = ({ item }) => {
    const meta = item.meta || {};
    return (
        <div className="flex justify-between items-start py-2 border-b border-dashed border-border last:border-0">
            <div>
                <div className="font-medium text-foreground flex items-center gap-2">
                    <span className="bg-secondary/50 px-2 rounded text-xs font-bold">{item.quantity}x</span>
                    {item.product_name}
                </div>
                {/* Details Badges */}
                <div className="flex flex-wrap gap-1 mt-1">
                    {meta.flavor && (
                        <span className="text-[10px] bg-blue-50 text-blue-700 px-1.5 rounded border border-blue-100">
                            Gusto: {meta.flavor}
                        </span>
                    )}
                    {meta.weight_kg && (
                        <span className="text-[10px] bg-gray-100 text-gray-700 px-1.5 rounded border border-gray-200">
                            {meta.weight_kg} kg
                        </span>
                    )}
                    {meta.writing && (
                        <span className="text-[10px] bg-purple-50 text-purple-700 px-1.5 rounded border border-purple-100 italic">
                            "{meta.writing}"
                        </span>
                    )}
                </div>
            </div>
            {meta.allergens_note && (
                <div className="flex items-center gap-1 text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-bold animate-pulse">
                    <AlertTriangle size={10} />
                    {meta.allergens_note}
                </div>
            )}
        </div>
    );
};

const OrderCard = ({ order, onStatusChange }) => {
    const isCompleted = order.status === 'ready' || order.status === 'delivered';
    const [loadingPdf, setLoadingPdf] = useState(false);

    const handlePrint = async () => {
        setLoadingPdf(true);
        try {
            await downloadProductionSheet(order._id);
            toast.success("PDF scaricato");
        } catch (e) {
            toast.error("Errore download PDF");
        } finally {
            setLoadingPdf(false);
        }
    };

    return (
        <div className={`border rounded-lg p-4 mb-3 transition-all ${isCompleted ? 'bg-green-50 border-green-200' : 'bg-white border-border shadow-sm'}`}>
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h4 className="font-bold text-primary">{order.customer_name}</h4>
                    <p className="text-xs text-muted-foreground">{order.customer.phone || "No telefono"}</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={handlePrint}
                        disabled={loadingPdf}
                        className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors" 
                        title="Stampa Scheda"
                    >
                        <Printer size={16} />
                    </button>
                    <select 
                        value={order.status}
                        onChange={(e) => onStatusChange(order._id, e.target.value)}
                        className={`text-xs font-medium rounded-md border px-2 py-1 outline-none cursor-pointer
                            ${order.status === 'received' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' : 
                              order.status === 'in_production' ? 'bg-orange-100 text-orange-800 border-orange-200' :
                              order.status === 'ready' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                              'bg-green-100 text-green-800 border-green-200'}`}
                    >
                        <option value="received">Da Fare</option>
                        <option value="in_production">In Lav.</option>
                        <option value="ready">Pronto</option>
                        <option value="delivered">Ritirato</option>
                    </select>
                </div>
            </div>

            {/* Items */}
            <div className="space-y-1">
                {order.items.map((item, idx) => (
                    <OrderItem key={idx} item={item} />
                ))}
            </div>
            
            {order.notes && (
                <div className="mt-3 text-xs bg-yellow-50 text-yellow-800 p-2 rounded border border-yellow-100">
                    <strong>Note:</strong> {order.notes}
                </div>
            )}
        </div>
    );
};

const SlotGroup = ({ date, time, orders, onStatusChange }) => {
    const [expanded, setExpanded] = useState(true);
    
    // Quick stats
    const totalItems = orders.reduce((acc, o) => acc + o.items.length, 0);
    const hasAllergens = orders.some(o => o.items.some(i => i.meta?.allergens_note));

    return (
        <div className="mb-6">
            <button 
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between p-3 bg-secondary/20 rounded-lg hover:bg-secondary/30 transition-colors mb-2"
            >
                <div className="flex items-center gap-3">
                    <div className="bg-white p-2 rounded-md shadow-sm text-primary font-bold font-mono">
                        {time}
                    </div>
                    <div className="text-left">
                        <h3 className="font-serif font-bold text-primary">
                            {orders.length} Ordini ({totalItems} articoli)
                        </h3>
                        {hasAllergens && (
                            <span className="text-[10px] text-red-600 font-bold flex items-center gap-1">
                                <AlertTriangle size={10} /> ATTENZIONE ALLERGENI
                            </span>
                        )}
                    </div>
                </div>
                {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>

            {expanded && (
                <div className="pl-2 border-l-2 border-secondary/20 ml-4 space-y-3">
                    {orders.map(order => (
                        <OrderCard key={order._id} order={order} onStatusChange={onStatusChange} />
                    ))}
                </div>
            )}
        </div>
    );
};

const Production = () => {
    const [slots, setSlots] = useState({});
    const [ingredients, setIngredients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'));

    const fetchData = async () => {
        try {
            // Note: In real app, pass date to getDailySlots filter
            const [slotsData, ingData] = await Promise.all([
                getDailySlots(), 
                getDailyIngredients(date)
            ]);
            setSlots(slotsData);
            setIngredients(ingData);
        } catch (e) {
            toast.error("Errore caricamento dati");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, [date]);

    const handleStatusChange = async (id, status) => {
        await updateOrderStatus(id, status);
        fetchData(); // Refresh to move if needed or just update UI
        toast.success("Stato aggiornato");
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento Produzione...</div>;

    // Filter slots by selected date (Client side grouping was done in backend but returns all active dates)
    // Actually backend returns { "YYYY-MM-DD": { "HH:MM": [] } }
    const daySlots = slots[date] || {};
    const sortedTimes = Object.keys(daySlots).sort();

    return (
        <Layout>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Produzione Giornaliera</h1>
                    <p className="text-muted-foreground">Organizzazione lavoro per orario di ritiro.</p>
                </div>
                <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-border shadow-sm">
                    <Calendar size={20} className="text-accent" />
                    <input 
                        type="date" 
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        className="outline-none text-primary font-medium bg-transparent"
                    />
                    <button onClick={fetchData} className="ml-2 p-1 hover:bg-muted rounded-full"><RefreshCw size={16} /></button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT: SLOTS TIMELINE */}
                <div className="lg:col-span-2">
                    {sortedTimes.length === 0 ? (
                        <div className="text-center py-20 bg-white rounded-xl border border-border">
                            <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
                            <h3 className="text-xl font-serif text-primary">Nessun ritiro previsto</h3>
                            <p className="text-muted-foreground">Seleziona un'altra data o attendi ordini.</p>
                        </div>
                    ) : (
                        sortedTimes.map(time => (
                            <SlotGroup 
                                key={time} 
                                date={date} 
                                time={time} 
                                orders={daySlots[time]} 
                                onStatusChange={handleStatusChange} 
                            />
                        ))
                    )}
                </div>

                {/* RIGHT: INGREDIENTS SUMMARY */}
                <div>
                    <div className="bg-white p-6 rounded-xl border border-border shadow-sm sticky top-4">
                        <h3 className="font-serif text-xl font-bold text-primary mb-4 flex items-center gap-2">
                            <ShoppingBag size={20} /> Fabbisogno Oggi
                        </h3>
                        {ingredients.length === 0 ? (
                            <p className="text-sm text-muted-foreground">Nessuna ricetta configurata o nessun ordine.</p>
                        ) : (
                            <ul className="space-y-2">
                                {ingredients.map((ing, idx) => (
                                    <li key={idx} className="flex justify-between items-center text-sm border-b border-dashed border-border pb-2 last:border-0">
                                        <span>{ing.name}</span>
                                        <span className="font-bold font-mono bg-secondary/30 px-2 rounded">
                                            {ing.quantity.toFixed(2)} {ing.unit}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                        <div className="mt-6 pt-4 border-t border-border">
                            <button className="w-full text-center text-xs text-accent hover:underline">
                                Scarica lista spesa (CSV)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

// Fix imports
import { ShoppingBag } from 'lucide-react';

export default Production;
