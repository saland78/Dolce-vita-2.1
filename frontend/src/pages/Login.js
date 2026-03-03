import React from 'react';
import { ChefHat } from 'lucide-react';

const Login = () => {
    const handleLogin = () => {
        // EMERGENT AUTH (Works in Preview)
        // Dynamic redirect URL based on current origin
        const redirectUrl = window.location.origin + '/dashboard';
        window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="bg-white p-8 rounded-2xl shadow-lg max-w-md w-full text-center border border-border">
                <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center text-secondary mx-auto mb-6">
                    <ChefHat size={32} />
                </div>
                
                <h1 className="text-4xl font-serif text-primary mb-2">DolceVita</h1>
                <p className="text-muted-foreground mb-8">Accesso Staff (Emergent Preview)</p>

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
            </div>
        </div>
    );
};

export default Login;
