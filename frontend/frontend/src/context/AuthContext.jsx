/**
 * AuthContext - React Context for global authentication state
 * Provides authentication methods and state to all components
 */

import { createContext, useContext } from "react";
import useAuth from "../hooks/useAuth";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const auth = useAuth();

  return (
    <AuthContext.Provider value={auth}>
      {/* Don't render children until auth check is complete */}
      {!auth.loading && children}
    </AuthContext.Provider>
  );
};

/**
 * Hook to use AuthContext anywhere in the app
 * Usage: const auth = useAuthContext();
 */
export const useAuthContext = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }

  return context;
};

export default AuthContext;
