import React, { useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { login } from '../api/api';

const AuthCallback = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const processed = useRef(false);

    useEffect(() => {
        if (processed.current) return;
        
        const hash = location.hash;
        if (hash && hash.includes('session_id=')) {
            processed.current = true;
            const sessionId = hash.split('session_id=')[1].split('&')[0];
            
            // Exchange session_id for user session
            login(sessionId)
                .then(user => {
                    navigate('/', { state: { user } });
                })
                .catch(err => {
                    console.error("Auth failed", err);
                    navigate('/login');
                });
        }
    }, [location, navigate]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-background text-primary font-serif animate-pulse">
            Autenticazione in corso...
        </div>
    );
};

export default AuthCallback;
