import React, { useEffect, useState, useCallback } from 'react';
import Layout from '../components/Layout';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { TrendingUp, ShoppingBag, Euro, Calendar, RefreshCw } from 'lucide-react';
import api from '../api/api';

const PERIODS = [
    { label: '7 giorni', value: '7d' },
    { label: '30 giorni', value: '30d' },
    { label: '3 mesi', value: '90d' },
    { label: '1 anno', value: '365d' },
];

const COLORS = ['#3d1a0e', '#7c3626', '#b85c38', '#e8986a', '#f5c99a', '#f5e6d0'];

const StatCard = ({ icon: Icon, label, value, sub }) => (
    <div className="bg-white rounded-xl border border-border shadow-sm p-5 flex items-start gap-4">
        <div className="p-2 rounded-lg bg-primary/10">
            <Icon size={20} className="text-primary" />
        </div>
        <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold text-primary">{value}</p>
            {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
        </div>
    </div>
);

const Reports = () => {
    const [period, setPeriod] = useState('30d');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchReport = useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.get(`/orders/sales-report?period=${period}`);
            setData(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [period]);

    useEffect(() => { fetchReport(); }, [fetchReport]);

    const avgOrder = data && data.total_orders > 0
        ? (data.total_revenue / data.total_orders).toFixed(2)
        : '0.00';

    return (
        <Layout>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Report Vendite</h1>
                    <p className="text-muted-foreground">Analisi fatturato e prodotti più venduti.</p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex bg-white border border-border rounded-lg overflow-hidden">
                        {PERIODS.map(p => (
                            <button
                                key={p.value}
                                onClick={() => setPeriod(p.value)}
                                className={`px-3 py-2 text-xs font-medium transition ${period === p.value ? 'bg-primary text-white' : 'text-muted-foreground hover:bg-muted'}`}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                    <button onClick={fetchReport} className="p-2 rounded-lg border border-border bg-white hover:bg-muted transition">
                        <RefreshCw size={16} className={loading ? 'animate-spin text-primary' : 'text-muted-foreground'} />
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex h-64 items-center justify-center text-primary font-serif">Caricamento...</div>
            ) : data ? (
                <div className="space-y-6">
                    {/* KPI cards */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard icon={Euro} label="Fatturato" value={`€${data.total_revenue.toFixed(2)}`} sub={`ultimi ${PERIODS.find(p=>p.value===period)?.label}`} />
                        <StatCard icon={ShoppingBag} label="Ordini" value={data.total_orders} sub="completati o in corso" />
                        <StatCard icon={TrendingUp} label="Scontrino medio" value={`€${avgOrder}`} sub="per ordine" />
                        <StatCard icon={Calendar} label="Prodotti diversi" value={data.top_products?.length || 0} sub="nel periodo" />
                    </div>

                    {/* Grafico fatturato giornaliero */}
                    <div className="bg-white rounded-xl border border-border shadow-sm p-5">
                        <h2 className="font-serif text-lg text-primary mb-4">Fatturato giornaliero</h2>
                        {data.revenue_by_day?.length > 0 ? (
                            <ResponsiveContainer width="100%" height={220}>
                                <LineChart data={data.revenue_by_day} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0e8e0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                                    <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `€${v}`} width={55} />
                                    <Tooltip formatter={(v) => [`€${v}`, 'Fatturato']} labelFormatter={l => `Data: ${l}`} />
                                    <Line type="monotone" dataKey="revenue" stroke="#3d1a0e" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="text-muted-foreground text-sm text-center py-8">Nessun dato per questo periodo.</p>
                        )}
                    </div>

                    {/* Top prodotti */}
                    <div className="bg-white rounded-xl border border-border shadow-sm p-5">
                        <h2 className="font-serif text-lg text-primary mb-4">Prodotti più venduti</h2>
                        {data.top_products?.length > 0 ? (
                            <div className="flex flex-col lg:flex-row gap-6">
                                <ResponsiveContainer width="100%" height={260}>
                                    <BarChart data={data.top_products} layout="vertical" margin={{ left: 10, right: 20 }}>
                                        <XAxis type="number" tick={{ fontSize: 11 }} />
                                        <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={140} />
                                        <Tooltip formatter={(v) => [v, 'Pezzi venduti']} />
                                        <Bar dataKey="qty" radius={[0, 6, 6, 0]}>
                                            {data.top_products.map((_, i) => (
                                                <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                                <div className="lg:w-64 shrink-0">
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wide mb-3">Fatturato per prodotto</p>
                                    <div className="space-y-2">
                                        {data.top_products.map((p, i) => (
                                            <div key={i} className="flex justify-between items-center text-sm">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                                                    <span className="truncate max-w-[130px]">{p.name}</span>
                                                </div>
                                                <span className="font-medium text-primary">€{p.revenue.toFixed(2)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-muted-foreground text-sm text-center py-8">Nessun prodotto venduto in questo periodo.</p>
                        )}
                    </div>

                    {/* Ordini per stato */}
                    {data.by_status && Object.keys(data.by_status).length > 0 && (
                        <div className="bg-white rounded-xl border border-border shadow-sm p-5">
                            <h2 className="font-serif text-lg text-primary mb-4">Ordini per stato</h2>
                            <div className="flex flex-wrap gap-3">
                                {Object.entries(data.by_status).map(([status, count]) => (
                                    <div key={status} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/40 border border-border">
                                        <span className="text-sm font-medium capitalize">{status.replace('_', ' ')}</span>
                                        <span className="text-lg font-bold text-primary">{count}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <p className="text-muted-foreground text-center py-16">Errore nel caricamento dati.</p>
            )}
        </Layout>
    );
};

export default Reports;
