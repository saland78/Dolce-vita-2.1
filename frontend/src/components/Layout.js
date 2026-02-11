import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, ShoppingBag, Box, Settings, ChefHat, LogOut, PlusCircle, CakeSlice, Users, ClipboardList } from 'lucide-react';
import { logout, getCurrentUser } from '../api/api';
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
  const navigate = useNavigate();
  const [user, setUser] = useState({ name: "Caricamento...", email: "" });

  useEffect(() => {
      getCurrentUser().then(setUser).catch(console.error);
  }, []);

  const handleLogout = async () => {
      try {
          await logout();
          navigate('/login');
      } catch (e) {
          console.error(e);
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
          <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" active={location.pathname === '/' || location.pathname === '/dashboard'} />
          <SidebarItem icon={ClipboardList} label="Piano Produzione" to="/production" active={location.pathname === '/production'} />
          <SidebarItem icon={ShoppingBag} label="Ordini" to="/orders" active={location.pathname === '/orders'} />
          <SidebarItem icon={Users} label="Clienti" to="/clients" active={location.pathname === '/clients'} />
          <div className="my-4 border-t border-border mx-2"></div>
          <p className="px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Catalogo</p>
          <SidebarItem icon={CakeSlice} label="Prodotti Finiti" to="/products" active={location.pathname === '/products'} />
          <SidebarItem icon={Box} label="Materie Prime" to="/inventory" active={location.pathname === '/inventory'} />
        </nav>

        <div className="pt-6 border-t border-border space-y-4">
            <div className="flex items-center gap-3 px-4 py-2">
                {user.picture ? (
                    <img src={user.picture} alt="Avatar" className="w-8 h-8 rounded-full border border-border" />
                ) : (
                    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-primary font-bold">
                        {user.name ? user.name[0].toUpperCase() : "U"}
                    </div>
                )}
                <div className="flex-1 overflow-hidden">
                    <p className="text-sm font-medium truncate">{user.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
                <button onClick={handleLogout} title="Esci">
                    <LogOut size={16} className="text-muted-foreground cursor-pointer hover:text-destructive" />
                </button>
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
