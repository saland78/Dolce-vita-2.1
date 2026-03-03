import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getProductionPlan, toggleProductionStatus } from '../api/api';
import { CheckCircle, Calendar, CakeSlice } from 'lucide-react';
import { format } from 'date-fns';

const Production = () => {
    const [plan, setPlan] = useState([]);
    const [loading, setLoading] = useState(true);
    const today = format(new Date(), 'yyyy-MM-dd');

    const fetchPlan = async () => {
        try {
            const data = await getProductionPlan(today);
            setPlan(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPlan();
        const interval = setInterval(fetchPlan, 10000); 
        return () => clearInterval(interval);
    }, []);

    const handleToggle = async (product_id, currentStatus) => {
        // Optimistic UI update
        setPlan(prev => prev.map(item => 
            item._id === product_id ? { ...item, completed: !currentStatus } : item
        ));

        try {
            await toggleProductionStatus({
                product_id: product_id, // Use ID
                date: today,
                completed: !currentStatus
            });
        } catch (e) {
            console.error("Failed to toggle status", e);
            fetchPlan();
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Calcolo Produzione...</div>;

    return (
        <Layout>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Piano di Produzione</h1>
                    <p className="text-muted-foreground">Cosa sfornare oggi per evadere gli ordini aperti.</p>
                </div>
                <div className="bg-white px-4 py-2 rounded-full border border-border flex items-center gap-2">
                    <Calendar size={18} className="text-accent" />
                    <span className="font-medium text-primary">Oggi ({today})</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {plan.length === 0 ? (
                    <div className="col-span-2 text-center py-20 bg-white rounded-xl border border-border">
                        <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
                        <h3 className="text-xl font-serif text-primary">Tutto completato!</h3>
                        <p className="text-muted-foreground">Nessun ordine in attesa di produzione.</p>
                    </div>
                ) : (
                    plan.map((item, idx) => (
                        <div 
                            key={idx} 
                            className={`bg-white p-6 rounded-xl border transition-all cursor-pointer group flex gap-4
                                ${item.completed ? 'border-green-200 bg-green-50 opacity-75' : 'border-border shadow-sm hover:border-accent'}`}
                            onClick={() => handleToggle(item._id, item.completed)}
                        >
                            {/* Image */}
                            <div className="w-20 h-20 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                                {item.image_url ? (
                                    <img src={item.image_url} alt={item.product_name} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                                        <CakeSlice size={24} />
                                    </div>
                                )}
                            </div>

                            <div className="flex-1">
                                <div className="flex justify-between items-start mb-2">
                                    <h2 className={`text-xl font-serif font-bold ${item.completed ? 'text-green-800 line-through' : 'text-primary'}`}>
                                        {item.product_name}
                                    </h2>
                                    <span className="text-3xl font-bold text-accent">{item.total_quantity}</span>
                                </div>
                                
                                <div className="space-y-1">
                                    {item.orders.map((ord, oIdx) => (
                                        <div key={oIdx} className="text-sm flex justify-between items-center text-muted-foreground border-b border-dashed border-border last:border-0 pb-1">
                                            <span>{ord.qty}x {ord.customer}</span>
                                            {ord.notes && <span className="bg-yellow-100 text-yellow-800 text-[10px] px-1.5 rounded ml-2">{ord.notes}</span>}
                                        </div>
                                    ))}
                                </div>
                            </div>
                            
                            <div className="flex items-center">
                                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors
                                    ${item.completed ? 'bg-green-500 border-green-500 text-white' : 'border-gray-300 group-hover:border-accent'}`}>
                                    {item.completed && <CheckCircle size={16} />}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </Layout>
    );
};

export default Production;
