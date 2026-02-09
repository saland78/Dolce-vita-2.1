import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getCustomers } from '../api/api';
import { User, Mail, ShoppingBag, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const Clients = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getCustomers()
            .then(setCustomers)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento Clienti...</div>;

    return (
        <Layout>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Clienti</h1>
                    <p className="text-muted-foreground">Sincronizzati con gli ordini e il sito web.</p>
                </div>
                <div className="bg-white px-4 py-2 rounded-full border border-border text-sm text-muted-foreground">
                    Totale: <strong>{customers.length}</strong>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {customers.map((customer, idx) => (
                    <div key={idx} className="bg-white p-6 rounded-xl border border-border shadow-sm hover:shadow-md transition-all group">
                        <div className="flex items-start justify-between mb-4">
                            <div className="w-12 h-12 rounded-full bg-secondary/50 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-secondary transition-colors">
                                <User size={24} />
                            </div>
                            <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-1 rounded">
                                {customer.source === 'woocommerce' ? 'WP' : 'Manual'}
                            </span>
                        </div>
                        
                        <h3 className="font-serif font-bold text-lg text-primary mb-1">{customer.name}</h3>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                            <Mail size={14} />
                            <span className="truncate">{customer.email || 'Nessuna email'}</span>
                        </div>

                        <div className="pt-4 border-t border-border flex justify-between items-center text-sm">
                            <div className="flex flex-col">
                                <span className="text-xs text-muted-foreground">Ultimo Ordine</span>
                                <span className="font-medium flex items-center gap-1">
                                    <Calendar size={12} />
                                    {customer.last_order_date ? format(new Date(customer.last_order_date), "d MMM yyyy", { locale: it }) : '-'}
                                </span>
                            </div>
                            <div className="flex flex-col items-end">
                                <span className="text-xs text-muted-foreground">Totale Speso</span>
                                <span className="font-bold text-accent">€{customer.total_spent?.toFixed(2) || '0.00'}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </Layout>
    );
};

export default Clients;
