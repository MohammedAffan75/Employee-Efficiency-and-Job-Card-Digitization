import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '../services/authService';
import { Employee } from '../types';

interface AuthContextType {
  user: Employee | null;
  token: string | null;
  login: (ecNumber: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<Employee | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const hydrateUser = async () => {
      if (!authService.isAuthenticated()) {
        setLoading(false);
        return;
      }

      const storedUser = authService.getStoredUser();
      if (storedUser) {
        setUser(storedUser);
        setToken(localStorage.getItem('access_token'));
      }

      try {
        const freshUser = await authService.getCurrentUser();
        setUser(freshUser);
        localStorage.setItem('user', JSON.stringify(freshUser));
      } catch (error) {
        console.error('Failed to refresh user info:', error);
      } finally {
        setLoading(false);
      }
    };

    hydrateUser();
  }, []);

  const login = async (ecNumber: string, password: string) => {
    setLoading(true);
    try {
      const response = await authService.login(ecNumber, password);
      setUser(response.employee);
      setToken(response.access_token);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
  };

  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};
