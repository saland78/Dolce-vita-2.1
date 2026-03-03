import React, { useEffect, useState } from 'react';
import { ChefHat, AlertCircle, RefreshCw } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

const Login = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [errorMsg, setErrorMsg] = useState(null);

    useEffect(() => {
        // Parse error params from URL (e.g. ?error=invalid_state)
        const params = new URLSearchParams(location.search);
        const error = params.get('error');
        if (error) {
            if (error === 'invalid_state') setErrorMsg("Sessione scaduta o non valida. Riprova.");
            else if (error === 'oauth_failed') setErrorMsg("Errore di comunicazione con Google.");
            else setErrorMsg("Errore di login. Riprova.");
            
            // Clean URL
            navigate('/login', { replace: true });
        }
    }, [location, navigate]);

    const handleLogin = () => {
        const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
        // Force full reload to clear any client-side debris
        window.location.href = `${backendUrl}/api/auth/login`;
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="bg-white p-8 rounded-2xl shadow-lg max-w-md w-full text-center border border-border">
                <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center text-secondary mx-auto mb-6">
                    <ChefHat size={32} />
                </div>
                
                <h1 className="text-4xl font-serif text-primary mb-2">DolceVita</h1>
                <p className="text-muted-foreground mb-8">Gestionale Pasticceria 2.0</p>

                {errorMsg && (
                    <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2 text-left animate-in slide-in-from-top-2">
                        <AlertCircle size={16} className="flex-shrink-0" />
                        {errorMsg}
                    </div>
                )}

                <button 
                    onClick={handleLogin}
                    className="w-full bg-white border border-gray-300 text-gray-700 font-medium py-3 px-4 rounded-lg flex items-center justify-center gap-3 hover:bg-gray-50 transition-all shadow-sm group"
                >
                    <img 
                        src="https://www.google.com/favicon.ico" 
                        alt="Google" 
                        className="w-5 h-5 opacity-80 group-hover:opacity-100 transition-opacity" 
                    />
                    Accedi con Google
                </button>
                
                <div className="mt-8 text-xs text-muted-foreground">
                    <p>Problemi di accesso? Contatta l'assistenza tecnica.</p>
                </div>
            </div>
        </div>
    );
};

export default Login;
