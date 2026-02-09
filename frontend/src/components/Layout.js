import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, ShoppingBag, Box, Settings, ChefHat, LogOut, PlusCircle } from 'lucide-react';
import { simulateOrder } from '../api/api';
import { toast } from 'sonner';

const SidebarItem = ({ icon: Icon, label, to, active }) => (
  <Link
    to={to}
    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300 ${
      active 
        ? 'bg-secondary text-primary font-medium shadow-sm' 
        : 'text-muted-foreground hover:bg-white/50 hover:text-primary'
    }`}
  >
    <Icon size={20} />
    <span>{label}</span>
  </Link>
);

const Layout = ({ children }) => {
  const location = useLocation();
  const [simulating, setSimulating] = useState(false);

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      await simulateOrder();
      toast.success("Nuovo ordine ricevuto da WooCommerce!");
      // Trigger a refresh event if needed, or rely on polling
    } catch (e) {
      toast.error("Errore nella simulazione");
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-64 fixed h-full bg-white border-r border-border p-6 hidden md:flex flex-col z-20 shadow-sm">
        <div className="mb-10 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-secondary">
                <ChefHat size={24} />
            </div>
            <div>
                <h1 className="font-serif text-2xl font-bold text-primary">DolceVita</h1>
                <p className="text-xs text-muted-foreground">Bakery Manager</p>
            </div>
        </div>

        <nav className="space-y-2 flex-1">
          <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" active={location.pathname === '/'} />
          <SidebarItem icon={ShoppingBag} label="Ordini" to="/orders" active={location.pathname === '/orders'} />
          <SidebarItem icon={Box} label="Magazzino" to="/inventory" active={location.pathname === '/inventory'} />
          <SidebarItem icon={Settings} label="Prodotti" to="/products" active={location.pathname === '/products'} />
        </nav>

        <div className="pt-6 border-t border-border space-y-4">
             <button 
                onClick={handleSimulate}
                disabled={simulating}
                className="w-full flex items-center justify-center gap-2 bg-accent text-white py-2 px-4 rounded-full text-sm font-medium hover:bg-accent/90 transition-all shadow-md active:scale-95"
            >
                <PlusCircle size={16} />
                {simulating ? "Simulazione..." : "Simula Ordine WP"}
            </button>
            <div className="flex items-center gap-3 px-4 py-2">
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-primary font-bold">A</div>
                <div className="flex-1">
                    <p className="text-sm font-medium">Admin User</p>
                    <p className="text-xs text-muted-foreground">Proprietario</p>
                </div>
                <LogOut size={16} className="text-muted-foreground cursor-pointer hover:text-destructive" />
            </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 md:ml-64 p-4 md:p-8 overflow-auto">
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
            {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
