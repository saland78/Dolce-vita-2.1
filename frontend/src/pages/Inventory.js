import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getIngredients, createIngredient, updateIngredient, deleteIngredient } from '../api/api';
import { AlertTriangle, Plus, X, Check, Trash2, Edit2 } from 'lucide-react';
import { toast } from 'sonner';

const Inventory = () => {
    const [ingredients, setIngredients] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [currentId, setCurrentId] = useState(null);
    
    // Form State
    const [formData, setFormData] = useState({
        name: "",
        quantity: "",
        unit: "kg",
        reorder_threshold: "",
        cost_per_unit: ""
    });

    const fetchIngredients = async () => {
        try {
            const data = await getIngredients();
            setIngredients(data);
        } catch (e) {
            console.error("Failed to fetch ingredients", e);
        }
    };

    useEffect(() => {
        fetchIngredients();
    }, []);

    const openCreate = () => {
        setEditMode(false);
        setFormData({ name: "", quantity: "", unit: "kg", reorder_threshold: "", cost_per_unit: "" });
        setIsModalOpen(true);
    };

    const openEdit = (ing) => {
        setEditMode(true);
        setCurrentId(ing._id);
        setFormData({
            name: ing.name,
            quantity: ing.quantity,
            unit: ing.unit,
            reorder_threshold: ing.reorder_threshold,
            cost_per_unit: ing.cost_per_unit
        });
        setIsModalOpen(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                name: formData.name,
                unit: formData.unit,
                quantity: parseFloat(formData.quantity) || 0,
                reorder_threshold: parseFloat(formData.reorder_threshold) || 0,
                cost_per_unit: parseFloat(formData.cost_per_unit) || 0
            };

            if (editMode) {
                await updateIngredient(currentId, payload);
                toast.success("Ingrediente aggiornato!");
            } else {
                await createIngredient(payload);
                toast.success("Ingrediente aggiunto!");
            }
            
            setIsModalOpen(false);
            fetchIngredients();
        } catch (err) {
            toast.error("Errore nel salvataggio");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Sei sicuro di voler eliminare questo ingrediente?")) return;
        try {
            await deleteIngredient(id);
            toast.success("Eliminato");
            fetchIngredients();
        } catch (e) {
            toast.error("Errore eliminazione");
        }
    };

    return (
        <Layout>
             <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-6">
                <div>
                    <h1 className="text-3xl font-serif text-primary">Magazzino Materie Prime</h1>
                    <p className="text-muted-foreground">Gestione scorte interne (Farina, Zucchero, etc.)</p>
                </div>
                <button 
                    onClick={openCreate}
                    className="bg-primary text-primary-foreground px-4 py-2 rounded-full flex items-center gap-2 hover:bg-primary/90 transition-all shadow-sm"
                >
                    <Plus size={18} /> Nuovo Ingrediente
                </button>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-border overflow-x-auto">
                <table className="w-full min-w-[600px] text-left border-collapse">
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
                        {ingredients.length === 0 && (
                            <tr>
                                <td colSpan={5} className="p-8 text-center text-muted-foreground">
                                    Nessun ingrediente in magazzino.
                                </td>
                            </tr>
                        )}
                        {ingredients.map((ing) => {
                            const isLow = ing.quantity <= ing.reorder_threshold;
                            return (
                                <tr key={ing._id} className="hover:bg-muted/20 transition-colors">
                                    <td className="p-4 font-medium text-foreground">{ing.name}</td>
                                    <td className="p-4">
                                        <span className={`font-mono text-lg font-semibold ${isLow ? 'text-red-600' : ''}`}>
                                            {ing.quantity}
                                        </span> 
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
                                    <td className="p-4 text-right flex justify-end gap-2">
                                        <button 
                                            onClick={() => openEdit(ing)}
                                            className="p-1 hover:bg-secondary/50 rounded-md text-accent transition-colors"
                                            title="Modifica"
                                        >
                                            <Edit2 size={16} />
                                        </button>
                                        <button 
                                            onClick={() => handleDelete(ing._id)}
                                            className="p-1 hover:bg-red-50 rounded-md text-red-500 transition-colors"
                                            title="Elimina"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Modal Dialog */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-in zoom-in-95 duration-200">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-6">
                            <h2 className="text-2xl font-serif text-primary">
                                {editMode ? "Modifica Ingrediente" : "Nuovo Ingrediente"}
                            </h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-muted-foreground hover:text-destructive">
                                <X size={24} />
                            </button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-1">Nome</label>
                                <input 
                                    required
                                    type="text" 
                                    className="w-full p-2 rounded-lg border border-border bg-muted/20 focus:ring-2 focus:ring-accent outline-none"
                                    placeholder="Es. Farina 00"
                                    value={formData.name}
                                    onChange={e => setFormData({...formData, name: e.target.value})}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Quantità</label>
                                    <input 
                                        type="number" 
                                        step="0.01"
                                        className="w-full p-2 rounded-lg border border-border bg-muted/20 focus:ring-2 focus:ring-accent outline-none"
                                        placeholder="0.00"
                                        value={formData.quantity}
                                        onChange={e => setFormData({...formData, quantity: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Unità</label>
                                    <select 
                                        className="w-full p-2 rounded-lg border border-border bg-muted/20 focus:ring-2 focus:ring-accent outline-none"
                                        value={formData.unit}
                                        onChange={e => setFormData({...formData, unit: e.target.value})}
                                    >
                                        <option value="kg">kg</option>
                                        <option value="litri">litri</option>
                                        <option value="pz">pz</option>
                                        <option value="gr">gr</option>
                                    </select>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Soglia Minima</label>
                                    <input 
                                        type="number" 
                                        step="0.01"
                                        className="w-full p-2 rounded-lg border border-border bg-muted/20 focus:ring-2 focus:ring-accent outline-none"
                                        placeholder="10"
                                        value={formData.reorder_threshold}
                                        onChange={e => setFormData({...formData, reorder_threshold: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Costo (€/unità)</label>
                                    <input 
                                        type="number" 
                                        step="0.01"
                                        className="w-full p-2 rounded-lg border border-border bg-muted/20 focus:ring-2 focus:ring-accent outline-none"
                                        placeholder="1.50"
                                        value={formData.cost_per_unit}
                                        onChange={e => setFormData({...formData, cost_per_unit: e.target.value})}
                                    />
                                </div>
                            </div>

                            <button 
                                type="submit"
                                className="w-full bg-primary text-white font-medium py-3 rounded-xl hover:bg-primary/90 transition-all flex items-center justify-center gap-2 mt-4"
                            >
                                <Check size={20} /> 
                                {editMode ? "Salva Modifiche" : "Crea Ingrediente"}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </Layout>
    );
};

export default Inventory;
