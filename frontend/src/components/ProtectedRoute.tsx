import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RoleEnum } from '../types';
import { authService } from '../services/authService';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: RoleEnum[];
}

const ProtectedRoute = ({ children, allowedRoles }: ProtectedRouteProps) => {
  const { isAuthenticated, user, loading } = useAuth();

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check role-based access
  if (allowedRoles && user) {
    // Admin has access to everything
    if (user.role === RoleEnum.ADMIN) {
      return <>{children}</>;
    }
    
    if (!allowedRoles.includes(user.role)) {
      // Redirect to role-appropriate home
      const homeRoute = authService.getRoleHomeRoute(user.role);
      return <Navigate to={homeRoute} replace />;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
