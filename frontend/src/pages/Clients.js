import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getCustomers } from '../api/api';
import { User, Mail, ShoppingBag, Calendar, ChevronDown, ChevronUp, FileText, Download } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

const statusColors = {
    processing: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
    pending: 'bg-gray-100 text-gray-700',
    'on-hold': 'bg-blue-100 text-blue-800',
};

const Clients = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(null);
    const [customerOrders, setCustomerOrders] = useState({});
    const [loadingOrders, setLoadingOrders] = useState({});
    const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
    const [reportYear, setReportYear] = useState(new Date().getFullYear());
    const [downloadingReport, setDownloadingReport] = useState(false);

    useEffect(() => {
        getCustomers()
            .then(setCustomers)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const toggleCustomer = async (email) => {
        if (expanded === email) {
            setExpanded(null);
            return;
        }
        setExpanded(email);
        if (customerOrders[email]) return;

        setLoadingOrders(prev => ({ ...prev, [email]: true }));
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(email)}/orders`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setCustomerOrders(prev => ({ ...prev, [email]: data }));
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingOrders(prev => ({ ...prev, [email]: false }));
        }
    };

    const downloadReport = async () => {
        setDownloadingReport(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(
                `${API_BASE}/api/customers/report/monthly/pdf?month=${reportMonth}&year=${reportYear}`,
                { headers: { 'Authorization': `Bearer ${token}` } }
            );
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${reportMonth}_${reportYear}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            console.error(e);
        } finally {
            setDownloadingReport(false);
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento Clienti...</div>;

    const months = [
        'Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
        'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'
    ];

    return (
        <Layout>
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Clienti</h1>
                    <p className="text-muted-foreground">Sincronizzati con gli ordini e il sito web.</p>
                </div>
                <div className="flex items-center gap-2 bg-white border border-border rounded-xl p-3 shadow-sm">
                    <FileText size={16} className="text-primary" />
                    <select
                        value={reportMonth}
                        onChange={e => setReportMonth(Number(e.target.value))}
                        className="text-sm border-none outline-none bg-transparent"
                    >
                        {months.map((m, i) => <option key={i} value={i+1}>{m}</option>)}
                    </select>
                    <select
                        value={reportYear}
                        onChange={e => setReportYear(Number(e.target.value))}
                        className="text-sm border-none outline-none bg-transparent"
                    >
                        {[2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                    <button
                        onClick={downloadReport}
                        disabled={downloadingReport}
                        className="flex items-center gap-1 bg-primary text-white text-sm px-3 py-1.5 rounded-lg hover:opacity-90 transition disabled:opacity-50"
                    >
                        <Download size={14} />
                        {downloadingReport ? 'Generando...' : 'Report PDF'}
                    </button>
                </div>
            </div>

            {/* Totale */}
            <div className="mb-4 text-sm text-muted-foreground">
                Totale: <strong>{customers.length}</strong> clienti
            </div>

            {/* Lista clienti */}
            <div className="flex flex-col gap-4">
                {customers.map((customer, idx) => (
                    <div key={idx} className="bg-white rounded-xl border border-border shadow-sm overflow-hidden">
                        {/* Card cliente */}
                        <div
                            className="flex items-center justify-between p-5 cursor-pointer hover:bg-muted/30 transition"
                            onClick={() => toggleCustomer(customer.email)}
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-11 h-11 rounded-full bg-secondary/50 flex items-center justify-center text-primary">
                                    <User size={22} />
                                </div>
                                <div>
                                    <h3 className="font-serif font-bold text-primary">{customer.name}</h3>
                                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                                        <Mail size={12} />
                                        <span>{customer.email || 'Nessuna email'}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-6">
                                <div className="text-right hidden sm:block">
                                    <div className="text-xs text-muted-foreground">Ordini</div>
                                    <div className="font-bold text-primary">{customer.orders_count || 0}</div>
                                </div>
                                <div className="text-right hidden sm:block">
                                    <div className="text-xs text-muted-foreground">Ultimo ordine</div>
                                    <div className="text-sm font-medium flex items-center gap-1">
                                        <Calendar size={12} />
                                        {customer.last_order_date
                                            ? format(new Date(customer.last_order_date), "d MMM yyyy", { locale: it })
                                            : '-'}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs text-muted-foreground">Totale speso</div>
                                    <div className="font-bold text-accent">€{customer.total_spent?.toFixed(2) || '0.00'}</div>
                                </div>
                                <div className="text-muted-foreground">
                                    {expanded === customer.email ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                                </div>
                            </div>
                        </div>

                        {/* Storico ordini espandibile */}
                        {expanded === customer.email && (
                            <div className="border-t border-border bg-muted/20 p-5">
                                <h4 className="font-serif text-sm font-bold text-primary mb-3">Storico Ordini</h4>
                                {loadingOrders[customer.email] ? (
                                    <p className="text-sm text-muted-foreground">Caricamento...</p>
                                ) : !customerOrders[customer.email]?.length ? (
                                    <p className="text-sm text-muted-foreground">Nessun ordine trovato.</p>
                                ) : (
                                    <div className="flex flex-col gap-2">
                                        {customerOrders[customer.email].map((order, i) => (
                                            <div key={i} className="bg-white rounded-lg border border-border p-4">
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        <ShoppingBag size={14} className="text-primary" />
                                                        <span className="text-sm font-medium">
                                                            {order.created_at
                                                                ? format(new Date(order.created_at), "d MMM yyyy", { locale: it })
                                                                : '-'}
                                                        </span>
                                                        {order.pickup_date && (
                                                            <span className="text-xs text-muted-foreground">
                                                                • Ritiro: {order.pickup_date}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[order.status] || 'bg-gray-100 text-gray-600'}`}>
                                                            {order.status}
                                                        </span>
                                                        <span className="font-bold text-accent text-sm">
                                                            €{order.total_amount?.toFixed(2) || '0.00'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <ul className="text-xs text-muted-foreground pl-2">
                                                    {order.items?.map((item, j) => (
                                                        <li key={j}>• {item.quantity}x {item.product_name}</li>
                                                    ))}
                                                </ul>
                                                {order.notes && (
                                                    <p className="text-xs text-muted-foreground mt-1 italic">Note: {order.notes}</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </Layout>
    );
};

export default Clients;
