import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getStats, getOrders } from '../api/api';
import { ArrowUpRight, Clock, CheckCircle, Truck, Package, ChefHat } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [recentOrders, setRecentOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [statsData, ordersData] = await Promise.all([getStats(), getOrders()]);
            setStats(statsData);
            setRecentOrders(ordersData.slice(0, 5));
        } catch (error) {
            console.error("Failed to fetch dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Polling every 5s
        return () => clearInterval(interval);
    }, []);

    // Mock chart data
    const chartData = [
        { name: 'Lun', sales: 400 },
        { name: 'Mar', sales: 300 },
        { name: 'Mer', sales: 200 },
        { name: 'Gio', sales: 278 },
        { name: 'Ven', sales: 189 },
        { name: 'Sab', sales: 639 },
        { name: 'Dom', sales: 349 },
    ];

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento Pasticceria...</div>;

    return (
        <Layout>
            <div className="mb-8">
                <h1 className="text-4xl font-serif text-primary mb-2">Buongiorno, Chef.</h1>
                <p className="text-muted-foreground">Ecco la situazione della pasticceria oggi.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard 
                    title="Ordini Totali" 
                    value={stats?.total_orders || 0} 
                    icon={Package} 
                    color="bg-blue-100 text-blue-600" 
                />
                <StatCard 
                    title="In Attesa" 
                    value={stats?.pending || 0} 
                    icon={Clock} 
                    color="bg-yellow-100 text-yellow-600" 
                />
                <StatCard 
                    title="In Produzione" 
                    value={stats?.production || 0} 
                    icon={ChefHat} 
                    color="bg-orange-100 text-orange-600" 
                />
                 <StatCard 
                    title="Incasso Oggi" 
                    value={stats?.today_revenue || 0} 
                    icon={ArrowUpRight} 
                    color="bg-green-100 text-green-600" 
                    isCurrency={true}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Chart Section */}
                <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-border shadow-sm">
                    <h3 className="font-serif text-xl mb-6 text-primary">Andamento Vendite</h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E6DCC8" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#8D7B68'}} />
                                <YAxis axisLine={false} tickLine={false} tick={{fill: '#8D7B68'}} />
                                <Tooltip 
                                    contentStyle={{backgroundColor: '#FFF', borderRadius: '12px', border: '1px solid #E6DCC8', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}} 
                                    itemStyle={{color: '#3E2723'}}
                                />
                                <Bar dataKey="sales" fill="#C5A059" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Recent Orders */}
                <div className="bg-white p-6 rounded-2xl border border-border shadow-sm">
                    <h3 className="font-serif text-xl mb-4 text-primary">Ordini Recenti</h3>
                    <div className="space-y-4">
                        {recentOrders.map((order) => (
                            <div key={order._id} className="flex items-center justify-between p-3 hover:bg-muted/50 rounded-lg transition-colors border-b border-dashed border-border last:border-0">
                                <div>
                                    <p className="font-medium text-primary">{order.customer_name}</p>
                                    <p className="text-xs text-muted-foreground">{order.items.length} articoli • {formatCurrency(order.total_amount)}</p>
                                </div>
                                <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide
                                    ${order.status === 'received' ? 'bg-yellow-100 text-yellow-700' : 
                                      order.status === 'ready' ? 'bg-green-100 text-green-700' : 
                                      'bg-gray-100 text-gray-600'}`}>
                                    {order.status}
                                </span>
                            </div>
                        ))}
                        {recentOrders.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">Nessun ordine recente</p>}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Dashboard;
