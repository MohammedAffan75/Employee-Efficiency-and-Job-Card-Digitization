import api from './api';
import { LoginResponse, Employee, RoleEnum } from '../types';
import { decodeJWT, isTokenExpired, getRoleFromToken } from '../utils/jwt';

export const authService = {
  /**
   * Login with EC number and password
   */
  async login(ecNumber: string, password: string): Promise<LoginResponse> {
    // Backend expects JSON: { ec_number, password }
    const response = await api.post<LoginResponse>(
      '/auth/login',
      { ec_number: ecNumber, password },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    // Store token and user info
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.employee));
      
      // Decode and store role
      const role = getRoleFromToken(response.data.access_token);
      if (role) {
        localStorage.setItem('role', role);
      }
    }

    return response.data;
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<Employee> {
    const response = await api.get<Employee>('/auth/me');
    return response.data;
  },

  /**
   * Logout
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('role');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    if (!token) return false;
    return !isTokenExpired(token);
  },

  /**
   * Get stored user
   */
  getStoredUser(): Employee | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Get user role
   */
  getRole(): RoleEnum | null {
    const role = localStorage.getItem('role');
    return role as RoleEnum | null;
  },

  /**
   * Get role-based home route
   */
  getRoleHomeRoute(role: RoleEnum): string {
    switch (role) {
      case RoleEnum.OPERATOR:
        return '/operator';
      case RoleEnum.SUPERVISOR:
        return '/supervisor';
      case RoleEnum.ADMIN:
        return '/admin';
      default:
        return '/';
    }
  },
};
