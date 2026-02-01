import { RoleEnum } from '../types';

interface JWTPayload {
  sub: string;
  role: RoleEnum;
  exp: number;
  employee_id: number;
}

export const decodeJWT = (token: string): JWTPayload | null => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
};

export const isTokenExpired = (token: string): boolean => {
  const decoded = decodeJWT(token);
  if (!decoded) return true;
  return decoded.exp * 1000 < Date.now();
};

export const getRoleFromToken = (token: string): RoleEnum | null => {
  const decoded = decodeJWT(token);
  return decoded?.role || null;
};
