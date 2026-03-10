import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getProducts, getIngredients } from '../api/api';
import { Plus, X, Check, BookOpen, ChefHat, TrendingUp, Euro } from 'lucide-react';
import { toast } from 'sonner';
import api from '../api/api';


// Converte tutto in kg/litri per confronto uniforme
const toBaseUnit = (quantity, unit) => {
    if (unit === 'gr') return quantity / 1000;
    if (unit === 'litri') return quantity;
    if (unit === 'kg') return quantity;
    return quantity; // pz rimane pz
};

const calculateRecipeCost = (recipe, ingredientsMap) => {
    if (!recipe || !recipe.ingredients?.length) return null;
    let total = 0;
    const breakdown = [];
    for (const ing of recipe.ingredients) {
        const master = ingredientsMap[ing.name];
        if (!master || !master.cost_per_unit) continue;
        // Quantità nella ricetta convertita in unità base
        const qtyBase = toBaseUnit(ing.quantity_per_unit, ing.unit);
        // Costo dell'ingrediente nel magazzino è per 1 unità (kg/litri/pz)
        const cost = qtyBase * master.cost_per_unit;
        total += cost;
        breakdown.push({ name: ing.name, qty: ing.quantity_per_unit, unit: ing.unit, cost });
    }
    return { total, breakdown };
};

const Recipes = () => {
    const [products, setProducts] = useState([]);
    const [ingredients, setIngredients] = useState([]);
    const [recipes, setRecipes] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [baseWeight, setBaseWeight] = useState(1.0);
    const [recipeIngredients, setRecipeIngredients] = useState([{ name: '', quantity_per_unit: '', unit: 'kg' }]);
    const [loading, setLoading] = useState(true);

    const fetchAll = async () => {
        try {
            const [prods, ings, recs] = await Promise.all([
                getProducts(),
                getIngredients(),
                api.get('/production/recipes').then(r => r.data).catch(() => []),
            ]);
            setProducts(prods);
            setIngredients(ings);
            setRecipes(recs);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAll(); }, []);

    const openModal = (product) => {
        setSelectedProduct(product);
        const existing = recipes.find(r => r.product_id === product._id);
        if (existing) {
            setBaseWeight(existing.base_weight_kg || 1.0);
            setRecipeIngredients(existing.ingredients.map(i => ({
                name: i.name,
                quantity_per_unit: i.quantity_per_unit,
                unit: i.unit,
            })));
        } else {
            setBaseWeight(1.0);
            setRecipeIngredients([{ name: '', quantity_per_unit: '', unit: 'kg' }]);
        }
        setIsModalOpen(true);
    };

    const addRow = () => setRecipeIngredients(prev => [...prev, { name: '', quantity_per_unit: '', unit: 'kg' }]);
    const removeRow = (idx) => setRecipeIngredients(prev => prev.filter((_, i) => i !== idx));
    const updateRow = (idx, field, value) => {
        setRecipeIngredients(prev => prev.map((row, i) => i === idx ? { ...row, [field]: value } : row));
    };

    const handleSave = async () => {
        const valid = recipeIngredients.filter(r => r.name && r.quantity_per_unit);
        if (valid.length === 0) { toast.error("Aggiungi almeno un ingrediente"); return; }
        try {
            await api.post('/production/recipes', {
                product_id: selectedProduct._id,
                product_name: selectedProduct.name,
                base_weight_kg: parseFloat(baseWeight),
                ingredients: valid.map(r => ({
                    name: r.name,
                    quantity_per_unit: parseFloat(r.quantity_per_unit),
                    unit: r.unit,
                })),
            });
            toast.success("Ricetta salvata!");
            setIsModalOpen(false);
            fetchAll();
        } catch (e) {
            toast.error("Errore nel salvataggio");
        }
    };

    const getRecipeForProduct = (pid) => recipes.find(r => r.product_id === pid);

    // Mappa nome → ingrediente per calcolo costi
    const ingredientsMap = Object.fromEntries(ingredients.map(i => [i.name, i]));

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento...</div>;

    return (
        <Layout>
            <div className="mb-6">
                <h1 className="text-3xl font-serif text-primary">Ricette & Ingredienti</h1>
                <p className="text-muted-foreground">Collega ogni prodotto agli ingredienti necessari per la produzione.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {products.map(product => {
                    const recipe = getRecipeForProduct(product._id);
                    return (
                        <div key={product._id} className="bg-white rounded-2xl border border-border shadow-sm p-5 hover:shadow-md transition-all">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3">
                                    {product.image_url ? (
                                        <img src={product.image_url} alt={product.name} className="w-12 h-12 rounded-xl object-cover" />
                                    ) : (
                                        <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
                                            <ChefHat size={20} className="text-muted-foreground" />
                                        </div>
                                    )}
                                    <div>
                                        <h3 className="font-semibold text-primary">{product.name}</h3>
                                        <p className="text-xs text-muted-foreground">€{product.price?.toFixed(2) || '—'}</p>
                                    </div>
                                </div>
                                {recipe && (
                                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">✓ Ricetta</span>
                                )}
                            </div>

                            {recipe ? (() => {
                                const costData = calculateRecipeCost(recipe, ingredientsMap);
                                const margin = costData && product.price ? ((product.price - costData.total) / product.price * 100) : null;
                                return (
                                    <div className="mb-4">
                                        <div className="space-y-1 mb-3">
                                            {recipe.ingredients.map((ing, i) => {
                                                const master = ingredientsMap[ing.name];
                                                const ingCost = master?.cost_per_unit
                                                    ? toBaseUnit(ing.quantity_per_unit, ing.unit) * master.cost_per_unit
                                                    : null;
                                                return (
                                                    <div key={i} className="flex justify-between text-sm text-foreground/80 bg-muted/30 rounded px-2 py-1">
                                                        <span>{ing.name}</span>
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-mono text-xs text-muted-foreground">{ing.quantity_per_unit} {ing.unit}</span>
                                                            {ingCost !== null && (
                                                                <span className="font-mono text-xs text-accent">€{ingCost.toFixed(3)}</span>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                        {costData && (
                                            <div className="rounded-xl border border-border bg-gradient-to-r from-amber-50 to-white p-3 mt-2">
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                                                        <Euro size={12} /> Costo produzione
                                                    </span>
                                                    <span className="font-bold text-sm text-primary">€{costData.total.toFixed(3)}</span>
                                                </div>
                                                {product.price > 0 && (
                                                    <>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-xs text-muted-foreground">Prezzo vendita</span>
                                                            <span className="text-sm font-medium">€{product.price.toFixed(2)}</span>
                                                        </div>
                                                        <div className="flex justify-between items-center">
                                                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                                <TrendingUp size={12} /> Margine
                                                            </span>
                                                            <span className={`text-sm font-bold ${margin >= 50 ? 'text-green-600' : margin >= 20 ? 'text-yellow-600' : 'text-red-600'}`}>
                                                                {margin !== null ? `${margin.toFixed(1)}%` : '—'}
                                                            </span>
                                                        </div>
                                                        <div className="mt-2 h-1.5 rounded-full bg-muted overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full transition-all ${margin >= 50 ? 'bg-green-500' : margin >= 20 ? 'bg-yellow-400' : 'bg-red-500'}`}
                                                                style={{ width: `${Math.min(Math.max(margin || 0, 0), 100)}%` }}
                                                            />
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                );
                            })() : (
                                <p className="text-sm text-muted-foreground italic mb-4">Nessuna ricetta configurata</p>
                            )}

                            <button
                                onClick={() => openModal(product)}
                                className="w-full py-2 rounded-xl border border-primary text-primary text-sm font-medium hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2"
                            >
                                <BookOpen size={15} />
                                {recipe ? 'Modifica Ricetta' : 'Aggiungi Ricetta'}
                            </button>
                        </div>
                    );
                })}
            </div>

            {products.length === 0 && (
                <div className="text-center py-16 text-muted-foreground">
                    <ChefHat size={48} className="mx-auto mb-4 opacity-30" />
                    <p>Nessun prodotto trovato. Sincronizza prima i prodotti da WooCommerce.</p>
                </div>
            )}

            {/* Modal ricetta */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-5">
                            <h2 className="text-2xl font-serif text-primary">Ricetta: {selectedProduct?.name}</h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-muted-foreground hover:text-destructive"><X size={24} /></button>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm font-medium text-muted-foreground mb-1">Peso base ricetta (kg)</label>
                            <input
                                type="number" step="0.1" min="0.1"
                                className="w-full p-2 rounded-lg border border-border bg-muted/20 focus:ring-2 focus:ring-accent outline-none"
                                value={baseWeight}
                                onChange={e => setBaseWeight(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground mt-1">Le quantità ingredienti si riferiscono a questo peso base</p>
                        </div>

                        <div className="mb-4">
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-sm font-medium text-muted-foreground">Ingredienti</label>
                                <button onClick={addRow} className="text-xs text-primary flex items-center gap-1 hover:underline">
                                    <Plus size={14} /> Aggiungi
                                </button>
                            </div>
                            <div className="space-y-2">
                                {recipeIngredients.map((row, idx) => (
                                    <div key={idx} className="flex gap-2 items-center">
                                        <select
                                            className="flex-1 p-2 rounded-lg border border-border bg-muted/20 text-sm outline-none"
                                            value={row.name}
                                            onChange={e => updateRow(idx, 'name', e.target.value)}
                                        >
                                            <option value="">Seleziona ingrediente</option>
                                            {ingredients.map(ing => (
                                                <option key={ing._id} value={ing.name}>{ing.name}</option>
                                            ))}
                                        </select>
                                        <input
                                            type="number" step="0.01" placeholder="Qtà"
                                            className="w-20 p-2 rounded-lg border border-border bg-muted/20 text-sm outline-none"
                                            value={row.quantity_per_unit}
                                            onChange={e => updateRow(idx, 'quantity_per_unit', e.target.value)}
                                        />
                                        <select
                                            className="w-16 p-2 rounded-lg border border-border bg-muted/20 text-sm outline-none"
                                            value={row.unit}
                                            onChange={e => updateRow(idx, 'unit', e.target.value)}
                                        >
                                            <option value="kg">kg</option>
                                            <option value="gr">gr</option>
                                            <option value="litri">l</option>
                                            <option value="pz">pz</option>
                                        </select>
                                        <button onClick={() => removeRow(idx)} className="text-red-400 hover:text-red-600">
                                            <X size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={handleSave}
                            className="w-full bg-primary text-white font-medium py-3 rounded-xl hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
                        >
                            <Check size={20} /> Salva Ricetta
                        </button>
                    </div>
                </div>
            )}
        </Layout>
    );
};

export default Recipes;
