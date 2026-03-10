import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock, User } from 'lucide-react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, isSameDay, isToday, addMonths, subMonths } from 'date-fns';
import { it } from 'date-fns/locale';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

const statusColors = {
    received: { bg: 'bg-yellow-400', text: 'text-yellow-900', light: 'bg-yellow-50 border-yellow-200' },
    in_production: { bg: 'bg-blue-400', text: 'text-blue-900', light: 'bg-blue-50 border-blue-200' },
    ready: { bg: 'bg-green-400', text: 'text-green-900', light: 'bg-green-50 border-green-200' },
    delivered: { bg: 'bg-gray-400', text: 'text-gray-700', light: 'bg-gray-50 border-gray-200' },
    cancelled: { bg: 'bg-red-400', text: 'text-red-900', light: 'bg-red-50 border-red-200' },
};

const DAYS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'];

const Calendar = () => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDay, setSelectedDay] = useState(null);
    const [selectedOrders, setSelectedOrders] = useState([]);

    useEffect(() => {
        fetchOrders();
    }, []);

    const fetchOrders = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_BASE}/api/orders/`, {
                headers: { 'Authorization': `Bearer ${token}` },
                credentials: 'include'
            });
            const data = await res.json();
            setOrders(Array.isArray(data) ? data : []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const getOrdersForDay = (date) => {
        return orders.filter(order => {
            if (!order.pickup_date) return false;
            try {
                const pickup = new Date(order.pickup_date);
                return isSameDay(pickup, date);
            } catch {
                return false;
            }
        });
    };

    const handleDayClick = (date) => {
        setSelectedDay(date);
        setSelectedOrders(getOrdersForDay(date));
    };

    // Costruisci la griglia del mese
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

    // Offset lunedì = 0
    const startOffset = (getDay(monthStart) + 6) % 7;
    const blanks = Array(startOffset).fill(null);

    if (loading) return (
        <Layout>
            <div className="flex h-64 items-center justify-center text-primary font-serif">
                Caricamento Calendario...
            </div>
        </Layout>
    );

    return (
        <Layout>
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Calendario Ordini</h1>
                    <p className="text-muted-foreground">Visualizza le consegne e i ritiri per data.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setCurrentDate(subMonths(currentDate, 1))}
                        className="p-2 rounded-lg hover:bg-white border border-border transition"
                    >
                        <ChevronLeft size={18} />
                    </button>
                    <span className="font-serif text-lg text-primary min-w-[160px] text-center capitalize">
                        {format(currentDate, 'MMMM yyyy', { locale: it })}
                    </span>
                    <button
                        onClick={() => setCurrentDate(addMonths(currentDate, 1))}
                        className="p-2 rounded-lg hover:bg-white border border-border transition"
                    >
                        <ChevronRight size={18} />
                    </button>
                    <button
                        onClick={() => setCurrentDate(new Date())}
                        className="ml-2 px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:opacity-90 transition"
                    >
                        Oggi
                    </button>
                </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
                {/* Griglia calendario */}
                <div className="flex-1 bg-white rounded-xl border border-border shadow-sm overflow-hidden">
                    {/* Intestazione giorni */}
                    <div className="grid grid-cols-7 border-b border-border">
                        {DAYS.map(d => (
                            <div key={d} className="py-3 text-center text-xs font-bold text-muted-foreground uppercase tracking-wide">
                                {d}
                            </div>
                        ))}
                    </div>

                    {/* Celle giorni */}
                    <div className="grid grid-cols-7">
                        {blanks.map((_, i) => (
                            <div key={`blank-${i}`} className="h-24 border-b border-r border-border/50 bg-muted/20" />
                        ))}
                        {days.map((day) => {
                            const dayOrders = getOrdersForDay(day);
                            const isSelected = selectedDay && isSameDay(day, selectedDay);
                            const today = isToday(day);

                            return (
                                <div
                                    key={day.toISOString()}
                                    onClick={() => handleDayClick(day)}
                                    className={`h-24 border-b border-r border-border/50 p-1.5 cursor-pointer transition-all hover:bg-secondary/30
                                        ${isSelected ? 'bg-secondary/50 ring-2 ring-inset ring-primary/30' : ''}
                                        ${today ? 'bg-amber-50' : ''}
                                    `}
                                >
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium mb-1
                                        ${today ? 'bg-primary text-white' : 'text-foreground'}
                                    `}>
                                        {format(day, 'd')}
                                    </div>
                                    <div className="flex flex-col gap-0.5 overflow-hidden">
                                        {dayOrders.slice(0, 2).map((order, i) => {
                                            const colors = statusColors[order.status] || statusColors.received;
                                            return (
                                                <div key={i} className={`text-xs px-1 py-0.5 rounded truncate font-medium ${colors.bg} ${colors.text}`}>
                                                    {order.customer_name?.split(' ')[0] || 'Cliente'}
                                                </div>
                                            );
                                        })}
                                        {dayOrders.length > 2 && (
                                            <div className="text-xs text-muted-foreground pl-1">
                                                +{dayOrders.length - 2} altri
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Pannello laterale dettaglio giorno */}
                <div className="w-full lg:w-72 lg:shrink-0">
                    {selectedDay ? (
                        <div className="bg-white rounded-xl border border-border shadow-sm p-4">
                            <div className="flex items-center gap-2 mb-4">
                                <CalendarIcon size={16} className="text-primary" />
                                <h3 className="font-serif font-bold text-primary capitalize">
                                    {format(selectedDay, "EEEE d MMMM", { locale: it })}
                                </h3>
                            </div>
                            {selectedOrders.length === 0 ? (
                                <p className="text-sm text-muted-foreground">Nessun ordine in questa data.</p>
                            ) : (
                                <div className="flex flex-col gap-3">
                                    {selectedOrders.map((order, i) => {
                                        const colors = statusColors[order.status] || statusColors.received;
                                        return (
                                            <div key={i} className={`rounded-lg border p-3 ${colors.light}`}>
                                                <div className="flex items-center justify-between mb-1">
                                                    <div className="flex items-center gap-1.5">
                                                        <User size={13} className="text-primary" />
                                                        <span className="text-sm font-medium">{order.customer_name}</span>
                                                    </div>
                                                    <span className="font-bold text-accent text-sm">€{order.total_amount?.toFixed(2)}</span>
                                                </div>
                                                {order.pickup_time && (
                                                    <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
                                                        <Clock size={11} />
                                                        <span>{order.pickup_time}</span>
                                                    </div>
                                                )}
                                                <ul className="text-xs text-muted-foreground mt-1">
                                                    {order.items?.slice(0, 3).map((item, j) => (
                                                        <li key={j}>• {item.quantity}x {item.product_name}</li>
                                                    ))}
                                                    {order.items?.length > 3 && <li>+{order.items.length - 3} altri</li>}
                                                </ul>
                                                <div className={`mt-2 inline-block text-xs px-2 py-0.5 rounded-full font-medium ${colors.bg} ${colors.text}`}>
                                                    {order.status}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="bg-white rounded-xl border border-border shadow-sm p-4 text-center">
                            <CalendarIcon size={32} className="text-muted-foreground mx-auto mb-2 opacity-40" />
                            <p className="text-sm text-muted-foreground">Clicca su un giorno per vedere i dettagli degli ordini.</p>
                        </div>
                    )}

                    {/* Legenda */}
                    <div className="mt-4 bg-white rounded-xl border border-border shadow-sm p-4">
                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-wide mb-3">Legenda</p>
                        <div className="flex flex-col gap-2">
                            {Object.entries(statusColors).map(([status, colors]) => (
                                <div key={status} className="flex items-center gap-2">
                                    <div className={`w-3 h-3 rounded-full ${colors.bg}`} />
                                    <span className="text-xs text-muted-foreground capitalize">{status.replace('_', ' ')}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Calendar;
