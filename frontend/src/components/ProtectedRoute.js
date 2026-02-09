import React, { useEffect, useState } from 'react';
import { useLocation, Navigate, Outlet } from 'react-router-dom';
import { getCurrentUser } from '../api/api';

const ProtectedRoute = () => {
    const location = useLocation();
    const [isAuthenticated, setIsAuthenticated] = useState(location.state?.user ? true : null);

    useEffect(() => {
        if (isAuthenticated === true) return; // Already confirmed

        const checkAuth = async () => {
            try {
                await getCurrentUser();
                setIsAuthenticated(true);
            } catch (e) {
                setIsAuthenticated(false);
            }
        };
        checkAuth();
    }, [isAuthenticated]);

    if (isAuthenticated === null) {
        return <div className="min-h-screen flex items-center justify-center bg-background text-primary font-serif">Caricamento...</div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return <Outlet />;
};

export default ProtectedRoute;
