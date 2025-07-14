import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, AuthResponse, User } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      if (token) {
        try {
          const userData = await api.getCurrentUser(token);
          setUser(userData);
        } catch (error) {
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, [token]);

  const login = async (email: string, password: string) => {
    const response: AuthResponse = await api.login(email, password);
    localStorage.setItem('token', response.access_token);
    if (response.refresh_token) {
      localStorage.setItem('refresh_token', response.refresh_token);
    }
    setToken(response.access_token);
    const userData = await api.getCurrentUser(response.access_token);
    setUser(userData);
  };

  const register = async (email: string, password: string, role: string) => {
    const response: AuthResponse = await api.register(email, password, role);
    localStorage.setItem('token', response.access_token);
    if (response.refresh_token) {
      localStorage.setItem('refresh_token', response.refresh_token);
    }
    setToken(response.access_token);
    const userData = await api.getCurrentUser(response.access_token);
    setUser(userData);
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await api.logout(refreshToken);
      } catch (e) {
        // Ignore logout errors
      }
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  };

  // Token refresh logic
  useEffect(() => {
    let refreshTimeout: NodeJS.Timeout;
    const scheduleRefresh = (exp: number) => {
      const now = Math.floor(Date.now() / 1000);
      const delay = (exp - now - 60) * 1000; // 1 min before expiry
      if (delay > 0) {
        refreshTimeout = setTimeout(refreshAccessToken, delay);
      }
    };
    const parseJwt = (token: string) => {
      try {
        return JSON.parse(atob(token.split('.')[1]));
      } catch {
        return null;
      }
    };
    const refreshAccessToken = async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await api.refreshToken(refreshToken);
          localStorage.setItem('token', response.access_token);
          setToken(response.access_token);
          scheduleRefresh(parseJwt(response.access_token).exp);
        } catch {
          await logout();
        }
      }
    };
    if (token) {
      const payload = parseJwt(token);
      if (payload && payload.exp) {
        scheduleRefresh(payload.exp);
      }
    }
    return () => {
      if (refreshTimeout) clearTimeout(refreshTimeout);
    };
  }, [token]);

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 