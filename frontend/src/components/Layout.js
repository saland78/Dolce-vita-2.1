import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, BarChart2, ShoppingBag, Box, Settings, ChefHat, LogOut, CakeSlice, Users, ClipboardList, BookOpen, Calendar, Menu, X } from 'lucide-react';
import { logout, getCurrentUser } from '../api/api';
import { toast } from 'sonner';

const SidebarItem = ({ icon: Icon, label, to, active, onClick }) => (
  <Link
    to={to}
    onClick={onClick}
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

const NavContent = ({ location, onItemClick, user, onLogout }) => (
  <>
    <div className="mb-8 flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-secondary flex-shrink-0">
        <ChefHat size={24} />
      </div>
      <div>
        <h1 className="font-serif text-2xl font-bold text-primary">DolceVita</h1>
        <p className="text-xs text-muted-foreground">Bakery Manager</p>
      </div>
    </div>

    <nav className="space-y-1 flex-1">
      <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" active={location.pathname === '/' || location.pathname === '/dashboard'} onClick={onItemClick} />
      <SidebarItem icon={ClipboardList} label="Piano Produzione" to="/production" active={location.pathname === '/production'} onClick={onItemClick} />
      <SidebarItem icon={ShoppingBag} label="Ordini" to="/orders" active={location.pathname === '/orders'} onClick={onItemClick} />
      <SidebarItem icon={Users} label="Clienti" to="/clients" active={location.pathname === '/clients'} onClick={onItemClick} />
      <SidebarItem icon={Calendar} label="Calendario" to="/calendar" active={location.pathname === '/calendar'} onClick={onItemClick} />
      <div className="my-3 border-t border-border mx-2" />
      <p className="px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">Catalogo</p>
      <SidebarItem icon={CakeSlice} label="Prodotti Finiti" to="/products" active={location.pathname === '/products'} onClick={onItemClick} />
      <SidebarItem icon={Box} label="Materie Prime" to="/inventory" active={location.pathname === '/inventory'} onClick={onItemClick} />
      <SidebarItem icon={BookOpen} label="Ricette" to="/recipes" active={location.pathname === '/recipes'} onClick={onItemClick} />
      <div className="my-3 border-t border-border mx-2" />
      <SidebarItem icon={Settings} label="Impostazioni" to="/settings" active={location.pathname === '/settings'} onClick={onItemClick} />
    </nav>

    <div className="pt-4 border-t border-border">
      <div className="flex items-center gap-3 px-4 py-2">
        {user?.picture ? (
          <img src={user.picture} alt="Avatar" className="w-8 h-8 rounded-full border border-border flex-shrink-0" />
        ) : (
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-primary font-bold flex-shrink-0">
            {user?.name ? user.name[0].toUpperCase() : 'U'}
          </div>
        )}
        <div className="flex-1 overflow-hidden">
          <p className="text-sm font-medium truncate">{user?.name}</p>
          <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
        </div>
        <button onClick={onLogout} title="Esci">
          <LogOut size={16} className="text-muted-foreground cursor-pointer hover:text-destructive" />
        </button>
      </div>
    </div>
  </>
);

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState({ name: 'Caricamento...', email: '' });
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    getCurrentUser().then(setUser).catch(console.error);
  }, []);

  // Chiudi menu mobile al cambio pagina
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

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

      {/* Sidebar desktop */}
      <aside className="w-64 fixed h-full bg-white border-r border-border p-6 hidden md:flex flex-col z-20 shadow-sm">
        <NavContent location={location} user={user} onLogout={handleLogout} />
      </aside>

      {/* Overlay mobile */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar mobile (drawer) */}
      <aside className={`fixed top-0 left-0 h-full w-72 bg-white border-r border-border p-6 flex flex-col z-40 shadow-xl transform transition-transform duration-300 md:hidden
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-muted text-muted-foreground"
        >
          <X size={22} />
        </button>
        <NavContent
          location={location}
          user={user}
          onLogout={handleLogout}
          onItemClick={() => setMobileOpen(false)}
        />
      </aside>

      {/* Topbar mobile */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-20 bg-white border-b border-border px-4 py-3 flex items-center gap-3 shadow-sm">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-1.5 rounded-lg hover:bg-muted text-primary"
        >
          <Menu size={22} />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-secondary">
            <ChefHat size={16} />
          </div>
          <span className="font-serif font-bold text-primary text-lg">DolceVita</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 md:ml-64 p-4 md:p-8 overflow-auto pt-16 md:pt-8">
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
