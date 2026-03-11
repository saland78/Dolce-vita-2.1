import React, { useEffect, useState, useRef } from 'react';
import Layout from '../components/Layout';
import { getStats, getOrders, getSalesHistory, getCurrentUser, getIngredients } from '../api/api';
import { ArrowUpRight, Clock, ChefHat, Package, AlertTriangle, Bell, BellOff } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';

const formatCurrency = (value) => {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(value);
};

const StatCard = ({ title, value, icon: Icon, color, isCurrency }) => (
    <div className="bg-white p-6 rounded-2xl border border-border shadow-sm flex items-start justify-between hover:shadow-md transition-all">
        <div>
            <p className="text-sm text-muted-foreground font-medium mb-1">{title}</p>
            <h3 className="text-3xl font-serif font-bold text-primary">
                {isCurrency ? formatCurrency(value) : value}
            </h3>
        </div>
        <div className={`p-3 rounded-full ${color}`}>
            <Icon size={24} />
        </div>
    </div>
);

const STATUS_LABELS = {
    received: 'Ricevuto',
    in_production: 'In Produzione',
    ready: 'Pronto',
    delivered: 'Consegnato',
};

const Dashboard = () => {
    const [user, setUser] = useState(null);
    const [stats, setStats] = useState(null);
    const [recentOrders, setRecentOrders] = useState([]);
    const [debugInfo, setDebugInfo] = useState(null);
    const [productPrices, setProductPrices] = useState({});
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [range, setRange] = useState("7d");
    const [lowStockIngredients, setLowStockIngredients] = useState([]);
    const [notificationsEnabled, setNotificationsEnabled] = useState(true);

    const prevOrderIdsRef = useRef(null);
    const audioCtxRef = useRef(null);

    const playNotificationSound = () => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            audioCtxRef.current = ctx;
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, ctx.currentTime);
            oscillator.frequency.setValueAtTime(660, ctx.currentTime + 0.15);
            gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.5);
        } catch (e) {
            console.log('Audio not available');
        }
    };

    const fetchData = async () => {
        try {
            // Ogni chiamata indipendente — un errore non blocca le altre
            const [userData, statsData, ordersData, historyData, ingredientsData, productsData] = await Promise.all([
                getCurrentUser().catch(e => { console.error("getCurrentUser failed:", e); return null; }),
                getStats().catch(e => { console.error("getStats failed:", e); return null; }),
                getOrders().catch(e => { console.error("getOrders failed:", e); return []; }),
                getSalesHistory(range).catch(e => { console.error("getSalesHistory failed:", e); return []; }),
                getIngredients().catch(e => { console.error("getIngredients failed:", e); return []; }),
                getProducts().catch(e => { console.error("getProducts failed:", e); return []; }),
            ]);

            if (userData) setUser(userData);
            if (statsData) setStats(statsData);
            if (historyData) setChartData(historyData);

            // Mappa id → prezzo aggiornato
            const priceMap = {};
            (productsData || []).forEach(p => { priceMap[p._id] = p.price; });
            setProductPrices(priceMap);

            // --- Avvisi scorte basse ---
            if (ingredientsData?.length) {
                const low = ingredientsData.filter(ing => ing.reorder_threshold > 0 && ing.quantity <= ing.reorder_threshold);
                setLowStockIngredients(low);
            }

            // --- Notifiche nuovi ordini ---
            // DEBUG
            setDebugInfo({
                userData: userData ? {name: userData.name, bakery_id: userData.bakery_id} : null,
                statsData: statsData,
                ordersCount: ordersData ? ordersData.length : 'null',
            });

            if (ordersData) {
                const currentIds = new Set(ordersData.map(o => o._id));
                if (prevOrderIdsRef.current !== null) {
                    const newOrders = ordersData.filter(o => !prevOrderIdsRef.current.has(o._id));
                    if (newOrders.length > 0 && notificationsEnabled) {
                        newOrders.forEach(o => {
                            toast.success(`🔔 Nuovo ordine da ${o.customer_name}!`, {
                                description: `${o.items.length} articoli • ${formatCurrency(o.total_amount)}`,
                                duration: 8000,
                            });
                        });
                        playNotificationSound();
                    }
                }
                prevOrderIdsRef.current = currentIds;
                setRecentOrders(ordersData.slice(0, 5));
            }
        } catch (error) {
            console.error("fetchData unexpected error:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [range, notificationsEnabled]);

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento...</div>;

    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Buongiorno' : hour < 18 ? 'Buon pomeriggio' : 'Buonasera';

    return (
        <Layout>
            {debugInfo && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs font-mono">
                    <strong>DEBUG:</strong> user={JSON.stringify(debugInfo.userData)} | stats={JSON.stringify(debugInfo.statsData)} | orders={debugInfo.ordersCount}
                </div>
            )}
            <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-serif text-primary mb-2">
                        {greeting}, {user?.name?.split(' ')[0] || 'Chef'}.
                    </h1>
                    <p className="text-muted-foreground">Ecco la situazione della pasticceria oggi.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setNotificationsEnabled(v => !v)}
                        className={`p-2 rounded-lg border transition-all ${notificationsEnabled ? 'bg-primary text-white border-primary' : 'bg-white text-muted-foreground border-border'}`}
                        title={notificationsEnabled ? 'Notifiche attive' : 'Notifiche disattivate'}
                    >
                        {notificationsEnabled ? <Bell size={18} /> : <BellOff size={18} />}
                    </button>
                    <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-border overflow-x-auto max-w-full">
                        {[
                            { label: 'Oggi', value: 'today' },
                            { label: '7 Giorni', value: '7d' },
                            { label: 'Mese', value: '30d' },
                            { label: '6 Mesi', value: '6m' },
                            { label: 'Anno', value: '1y' }
                        ].map(opt => (
                            <button
                                key={opt.value}
                                onClick={() => setRange(opt.value)}
                                className={`px-2 py-1 text-xs md:text-sm md:px-3 md:py-1.5 font-medium rounded-md transition-all whitespace-nowrap ${
                                    range === opt.value
                                    ? 'bg-primary text-white shadow-sm'
                                    : 'text-muted-foreground hover:bg-muted'
                                }`}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Avvisi scorte basse */}
            {lowStockIngredients.length > 0 && (
                <div className="mb-6 bg-red-50 border border-red-200 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle size={20} className="text-red-600" />
                        <h3 className="font-semibold text-red-700">Scorte in Esaurimento ({lowStockIngredients.length})</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {lowStockIngredients.map(ing => (
                            <span key={ing._id} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm bg-red-100 text-red-700 border border-red-200">
                                <AlertTriangle size={12} />
                                <strong>{ing.name}</strong>: {ing.quantity} {ing.unit} (min. {ing.reorder_threshold})
                            </span>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard title="Ordini Totali" value={stats?.total_orders || 0} icon={Package} color="bg-blue-100 text-blue-600" />
                <StatCard title="In Attesa" value={stats?.pending || 0} icon={Clock} color="bg-yellow-100 text-yellow-600" />
                <StatCard title="In Produzione" value={stats?.production || 0} icon={ChefHat} color="bg-orange-100 text-orange-600" />
                <StatCard title="Incasso Oggi" value={stats?.today_revenue || 0} icon={ArrowUpRight} color="bg-green-100 text-green-600" isCurrency={true} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-border shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-serif text-xl text-primary">Andamento Vendite</h3>
                        <span className="text-xs text-muted-foreground font-mono bg-muted px-2 py-1 rounded">
                            {range === 'today' ? 'Oggi' : `Ultimi ${range}`}
                        </span>
                    </div>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E6DCC8" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#8D7B68'}} />
                                <YAxis axisLine={false} tickLine={false} tick={{fill: '#8D7B68'}} />
                                <Tooltip
                                    contentStyle={{backgroundColor: '#FFF', borderRadius: '12px', border: '1px solid #E6DCC8', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                                    itemStyle={{color: '#3E2723'}}
                                    formatter={(value) => formatCurrency(value)}
                                />
                                <Bar dataKey="sales" fill="#C5A059" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border border-border shadow-sm">
                    <h3 className="font-serif text-xl mb-4 text-primary">Ordini Recenti</h3>
                    <div className="space-y-4">
                        {recentOrders.map((order) => (
                            <div key={order._id} className="flex items-center justify-between p-3 hover:bg-muted/50 rounded-lg transition-colors border-b border-dashed border-border last:border-0">
                                <div>
                                    <p className="font-medium text-primary">{order.customer_name}</p>
                                    <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                                        {order.items.map(i => `${i.quantity > 1 ? i.quantity + 'x ' : ''}${i.product_name}`).join(', ')}
                                    </p>
                                    <p className="text-xs font-medium text-accent">
                                        {formatCurrency(
                                            order.items.reduce((sum, i) => {
                                                const price = productPrices[i.product_id] ?? i.price ?? 0;
                                                return sum + price * i.quantity;
                                            }, 0) || order.total_amount
                                        )}
                                    </p>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide
                                        ${order.status === 'received' ? 'bg-yellow-100 text-yellow-700' :
                                        order.status === 'in_production' ? 'bg-orange-100 text-orange-700' :
                                        order.status === 'ready' ? 'bg-green-100 text-green-700' :
                                        'bg-gray-100 text-gray-600'}`}>
                                        {STATUS_LABELS[order.status] || order.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                        {recentOrders.length === 0 && (
                            <p className="text-center text-muted-foreground text-sm py-8">Nessun ordine recente</p>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Dashboard;
