import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Orders from "./pages/Orders";
import Inventory from "./pages/Inventory";
import Products from "./pages/Products";
import Login from "./pages/Login";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthCallback from "./components/AuthCallback";
import { Toaster } from 'sonner';

// Wrapper to handle hash routing for auth
const AppRouter = () => {
    const location = useLocation();

    // Intercept auth callback from hash
    if (location.hash && location.hash.includes('session_id=')) {
        return <AuthCallback />;
    }

    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route element={<ProtectedRoute />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/orders" element={<Orders />} />
                <Route path="/inventory" element={<Inventory />} />
                <Route path="/products" element={<Products />} />
            </Route>
        </Routes>
    );
};

function App() {
  return (
    <>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </>
  );
}

export default App;
