import { useAuth } from '../context/AuthContext';
import { RoleEnum } from '../types';
import { authService } from '../services/authService';

export const useRole = () => {
  const { user } = useAuth();

  const role = user?.role || null;

  const isOperator = role === RoleEnum.OPERATOR;
  const isSupervisor = role === RoleEnum.SUPERVISOR;
  const isAdmin = role === RoleEnum.ADMIN;

  const hasRole = (requiredRole: RoleEnum) => role === requiredRole;
  const hasAnyRole = (roles: RoleEnum[]) => role && roles.includes(role);

  const getHomeRoute = () => {
    if (!role) return '/login';
    return authService.getRoleHomeRoute(role);
  };

  const getAllowedRoutes = () => {
    if (!role) return [];

    const routes: string[] = [];

    if (isOperator) {
      routes.push('/operator', '/operator/jobcards', '/operator/dashboard');
    }

    if (isSupervisor) {
      routes.push(
        '/supervisor',
        '/supervisor/dashboard',
        '/supervisor/assignments',
        '/supervisor/validations',
        '/supervisor/reports'
      );
    }

    if (isAdmin) {
      routes.push(
        '/admin',
        '/admin/activity-codes',
        '/admin/machines',
        '/admin/employees',
        '/admin/work-orders'
      );
    }

    return routes;
  };

  return {
    role,
    isOperator,
    isSupervisor,
    isAdmin,
    hasRole,
    hasAnyRole,
    getHomeRoute,
    getAllowedRoutes,
  };
};
