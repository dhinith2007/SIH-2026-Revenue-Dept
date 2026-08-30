import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User, RoleType, PermissionType, AuthState } from '../types/auth';
import { apiService } from '../services/api';

interface AuthContextType extends AuthState {
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  reauthenticate: (password: string) => Promise<boolean>;
  hasPermission: (permission: PermissionType) => boolean;
  dismissWarning: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const WARNING_BEFORE_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes before expiration (at 25 min)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(apiService.getToken());
  const [role, setRole] = useState<RoleType | null>(null);
  const [permissions, setPermissions] = useState<PermissionType[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [sessionWarning, setSessionWarning] = useState<boolean>(false);

  // Inactivity tracking
  const [lastActivity, setLastActivity] = useState<number>(Date.now());

  const logout = useCallback(async () => {
    try {
      await apiService.logout();
    } catch (err) {
      console.warn('Logout request failed:', err);
    } finally {
      setUser(null);
      setToken(null);
      setRole(null);
      setPermissions([]);
      setSessionWarning(false);
      apiService.setToken(null);
    }
  }, []);

  // Initialize session on mount if token exists
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = apiService.getToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await apiService.getCurrentUser();
        setUser(currentUser);
        setRole(currentUser.role);
        setToken(storedToken);
      } catch (error) {
        console.warn('Session expired or token invalid on startup:', error);
        apiService.setToken(null);
        setToken(null);
        setUser(null);
        setRole(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // Activity listeners
  useEffect(() => {
    const recordActivity = () => {
      setLastActivity(Date.now());
      if (sessionWarning) {
        setSessionWarning(false);
      }
    };

    window.addEventListener('mousemove', recordActivity);
    window.addEventListener('keydown', recordActivity);
    window.addEventListener('click', recordActivity);
    window.addEventListener('scroll', recordActivity);

    return () => {
      window.removeEventListener('mousemove', recordActivity);
      window.removeEventListener('keydown', recordActivity);
      window.removeEventListener('click', recordActivity);
      window.removeEventListener('scroll', recordActivity);
    };
  }, [sessionWarning]);

  // Inactivity checker timer
  useEffect(() => {
    if (!token || !user) return;

    const timer = setInterval(() => {
      const inactiveFor = Date.now() - lastActivity;

      if (inactiveFor >= INACTIVITY_TIMEOUT_MS) {
        console.warn('Session terminated due to 30 min of inactivity.');
        logout();
      } else if (inactiveFor >= INACTIVITY_TIMEOUT_MS - WARNING_BEFORE_TIMEOUT_MS) {
        setSessionWarning(true);
      }
    }, 15000);

    return () => clearInterval(timer);
  }, [token, user, lastActivity, logout]);

  const login = async (identifier: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await apiService.login(identifier, password);
      setUser(result.user);
      setRole(result.user.role);
      setPermissions(result.permissions);
      setToken(result.access_token);
      setLastActivity(Date.now());
      setSessionWarning(false);
    } finally {
      setIsLoading(false);
    }
  };

  const reauthenticate = async (password: string): Promise<boolean> => {
    const ok = await apiService.reauthenticate(password);
    if (ok) {
      setLastActivity(Date.now());
    }
    return ok;
  };

  const hasPermission = (permission: PermissionType): boolean => {
    if (!permissions || permissions.length === 0) {
      // Fallback check based on role if permissions array not populated
      if (role === 'DEPARTMENT_ADMINISTRATOR') {
        return ['USER_MANAGE', 'SERVICE_METADATA_CONFIGURE', 'SYSTEM_HEALTH_VIEW'].includes(permission);
      }
      if (role === 'REVENUE_OFFICER') {
        return ['APPLICATION_VIEW_ASSIGNED', 'DOCUMENT_VERIFY', 'APPLICATION_APPROVE', 'APPLICATION_REJECT', 'REQUEST_INFORMATION'].includes(permission);
      }
      if (role === 'SENIOR_REVENUE_OFFICER') {
        return ['APPLICATION_VIEW_ASSIGNED', 'APPLICATION_VIEW_ALL', 'DOCUMENT_VERIFY', 'APPLICATION_APPROVE', 'APPLICATION_REJECT', 'REQUEST_INFORMATION', 'ESCALATED_CASE_REVIEW', 'EXCEPTION_OVERRIDE'].includes(permission);
      }
      if (role === 'READ_ONLY_AUDITOR') {
        return ['AUDIT_VIEW', 'APPLICATION_VIEW_ALL'].includes(permission);
      }
    }
    return permissions.includes(permission);
  };

  const dismissWarning = () => {
    setLastActivity(Date.now());
    setSessionWarning(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role,
        permissions,
        isAuthenticated: !!token && !!user,
        isLoading,
        sessionWarning,
        login,
        logout,
        reauthenticate,
        hasPermission,
        dismissWarning,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
