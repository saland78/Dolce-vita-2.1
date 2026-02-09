import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getIngredients, seedInventory } from '../api/api';
import { AlertTriangle, Plus } from 'lucide-react';
import { toast } from 'sonner';

const Inventory = () => {
    const [ingredients, setIngredients] = useState([]);

    const fetchIngredients = async () => {
        const data = await getIngredients();
        setIngredients(data);
    };

    useEffect(() => {
        fetchIngredients();
        // Auto-seed if empty for demo
        seedInventory().then(() => fetchIngredients());
    }, []);

    return (
        <Layout>
             <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-serif text-primary">Magazzino Ingredienti</h1>
                <button className="bg-primary text-primary-foreground px-4 py-2 rounded-full flex items-center gap-2 hover:bg-primary/90">
                    <Plus size={18} /> Nuovo Ingrediente
                </button>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-border overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-secondary/30 text-primary font-serif">
                        <tr>
                            <th className="p-4 font-semibold">Ingrediente</th>
                            <th className="p-4 font-semibold">Quantità</th>
                            <th className="p-4 font-semibold">Soglia Minima</th>
                            <th className="p-4 font-semibold">Stato</th>
                            <th className="p-4 font-semibold text-right">Azioni</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {ingredients.map((ing) => {
                            const isLow = ing.quantity <= ing.reorder_threshold;
                            return (
                                <tr key={ing._id} className="hover:bg-muted/20 transition-colors">
                                    <td className="p-4 font-medium text-foreground">{ing.name}</td>
                                    <td className="p-4">
                                        <span className="font-mono text-lg font-semibold">{ing.quantity}</span> 
                                        <span className="text-muted-foreground ml-1 text-sm">{ing.unit}</span>
                                    </td>
                                    <td className="p-4 text-muted-foreground">{ing.reorder_threshold} {ing.unit}</td>
                                    <td className="p-4">
                                        {isLow ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                                <AlertTriangle size={12} /> In Esaurimento
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                                OK
                                            </span>
                                        )}
                                    </td>
                                    <td className="p-4 text-right">
                                        <button className="text-sm font-medium text-accent hover:text-accent/80 hover:underline">Modifica</button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </Layout>
    );
};

export default Inventory;
