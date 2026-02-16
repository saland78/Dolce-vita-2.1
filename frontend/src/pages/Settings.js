import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getSettings, updateSettings } from '../api/api';
import { Save, CheckCircle, Store, Link as LinkIcon, Key } from 'lucide-react';
import { toast } from 'sonner';

const SettingsPage = () => {
    const [formData, setFormData] = useState({
        name: "",
        wc_url: "",
        wc_consumer_key: "",
        wc_consumer_secret: ""
    });
    const [status, setStatus] = useState({ has_keys: false });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getSettings()
            .then(data => {
                setFormData(prev => ({
                    ...prev,
                    name: data.name,
                    wc_url: data.wc_url || ""
                }));
                setStatus({ has_keys: data.has_keys });
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await updateSettings(formData);
            toast.success("Impostazioni salvate con successo!");
            setStatus(prev => ({ ...prev, has_keys: !!(formData.wc_consumer_key && formData.wc_consumer_secret) || prev.has_keys }));
            // Clear secrets for security (UI only)
            setFormData(prev => ({ ...prev, wc_consumer_key: "", wc_consumer_secret: "" }));
        } catch (err) {
            toast.error("Errore nel salvataggio");
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center text-primary font-serif">Caricamento...</div>;

    return (
        <Layout>
            <div className="max-w-2xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-serif text-primary mb-2">Impostazioni Pasticceria</h1>
                    <p className="text-muted-foreground">Configura il tuo negozio e il collegamento WooCommerce.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* General Info */}
                    <div className="bg-white p-6 rounded-xl border border-border shadow-sm">
                        <div className="flex items-center gap-3 mb-4 text-primary">
                            <Store size={20} />
                            <h2 className="font-serif text-lg font-bold">Dati Attività</h2>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-1">Nome Pasticceria</label>
                                <input 
                                    type="text" 
                                    className="w-full p-2 rounded-lg border border-border focus:ring-2 focus:ring-accent outline-none"
                                    value={formData.name}
                                    onChange={e => setFormData({...formData, name: e.target.value})}
                                    required
                                />
                            </div>
                        </div>
                    </div>

                    {/* WooCommerce Config */}
                    <div className="bg-white p-6 rounded-xl border border-border shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3 text-primary">
                                <LinkIcon size={20} />
                                <h2 className="font-serif text-lg font-bold">Collegamento Sito</h2>
                            </div>
                            {status.has_keys && (
                                <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">
                                    <CheckCircle size={12} /> Collegato
                                </span>
                            )}
                        </div>
                        
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-muted-foreground mb-1">URL Sito Web</label>
                                <input 
                                    type="url" 
                                    placeholder="https://miapasticceria.it"
                                    className="w-full p-2 rounded-lg border border-border focus:ring-2 focus:ring-accent outline-none"
                                    value={formData.wc_url}
                                    onChange={e => setFormData({...formData, wc_url: e.target.value})}
                                />
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Consumer Key (CK)</label>
                                    <div className="relative">
                                        <Key size={16} className="absolute left-3 top-3 text-muted-foreground" />
                                        <input 
                                            type="password" 
                                            placeholder={status.has_keys ? "••••••••••••" : "ck_..."}
                                            className="w-full pl-9 p-2 rounded-lg border border-border focus:ring-2 focus:ring-accent outline-none"
                                            value={formData.wc_consumer_key}
                                            onChange={e => setFormData({...formData, wc_consumer_key: e.target.value})}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Consumer Secret (CS)</label>
                                    <div className="relative">
                                        <Key size={16} className="absolute left-3 top-3 text-muted-foreground" />
                                        <input 
                                            type="password" 
                                            placeholder={status.has_keys ? "••••••••••••" : "cs_..."}
                                            className="w-full pl-9 p-2 rounded-lg border border-border focus:ring-2 focus:ring-accent outline-none"
                                            value={formData.wc_consumer_secret}
                                            onChange={e => setFormData({...formData, wc_consumer_secret: e.target.value})}
                                        />
                                    </div>
                                </div>
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">
                                Trova queste chiavi nel tuo WordPress in: WooCommerce {'>'} Impostazioni {'>'} Avanzate {'>'} REST API.
                            </p>
                        </div>
                    </div>

                    <button 
                        type="submit" 
                        className="w-full bg-primary text-white font-medium py-3 rounded-xl hover:bg-primary/90 transition-all flex items-center justify-center gap-2 shadow-md active:scale-95"
                    >
                        <Save size={20} /> Salva Configurazione
                    </button>
                </form>
            </div>
        </Layout>
    );
};

export default SettingsPage;
