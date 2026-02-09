import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getProducts, getProductOrders } from '../api/api';
import { Search, User, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { it } from 'date-fns/locale';

const Products = () => {
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [productOrders, setProductOrders] = useState([]);

    useEffect(() => {
        getProducts().then(setProducts);
    }, []);

    const handleProductClick = async (product) => {
        setSelectedProduct(product);
        setProductOrders([]); // Clear previous
        try {
            const orders = await getProductOrders(product._id);
            setProductOrders(orders);
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <Layout>
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-serif text-primary">Prodotti Finiti</h1>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map(product => (
                    <div 
                        key={product._id} 
                        onClick={() => handleProductClick(product)}
                        className="bg-white rounded-xl border border-border shadow-sm overflow-hidden cursor-pointer hover:shadow-md hover:border-accent transition-all group"
                    >
                        <div className="h-48 bg-muted relative overflow-hidden">
                            {product.image_url ? (
                                <img src={product.image_url} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-muted-foreground">No Image</div>
                            )}
                        </div>
                        <div className="p-4">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="font-serif font-bold text-lg text-primary">{product.name}</h3>
                                <span className="text-accent font-bold">€{product.price}</span>
                            </div>
                            <p className="text-sm text-muted-foreground mb-3">{product.description}</p>
                            <span className="text-xs bg-secondary/50 text-primary px-2 py-1 rounded-full uppercase tracking-wider font-bold">{product.category}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal / Drawer for Product Details */}
            {selectedProduct && (
                <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-end" onClick={() => setSelectedProduct(null)}>
                    <div 
                        className="w-full max-w-md h-full bg-white shadow-2xl p-6 overflow-y-auto animate-in slide-in-from-right duration-300"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="mb-6 pb-6 border-b border-border">
                            <h2 className="text-2xl font-serif text-primary mb-1">{selectedProduct.name}</h2>
                            <p className="text-muted-foreground text-sm">Storico Ordini Clienti</p>
                        </div>

                        {productOrders.length === 0 ? (
                            <p className="text-center text-muted-foreground py-10">Nessun ordine recente per questo prodotto.</p>
                        ) : (
                            <div className="space-y-4">
                                {productOrders.map((po, idx) => (
                                    <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/20 border border-border/50">
                                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary mt-1">
                                            <User size={14} />
                                        </div>
                                        <div>
                                            <p className="font-medium text-foreground">{po.customer_name}</p>
                                            <p className="text-xs text-muted-foreground mb-1">{po.customer_email || 'No email'}</p>
                                            <div className="flex items-center gap-2 text-xs text-primary/70">
                                                <span className="font-bold bg-white px-1.5 rounded border border-border">x{po.quantity}</span>
                                                <span className="flex items-center gap-1"><Calendar size={10} /> {format(new Date(po.created_at), "d MMM", { locale: it })}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </Layout>
    );
};

export default Products;
