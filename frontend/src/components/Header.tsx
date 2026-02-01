import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import logo from '../../CMTILogo.jpg';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const userInitials = useMemo(() => {
    if (!user?.name) return '';
    return user.name
      .split(' ')
      .filter(Boolean)
      .map((part) => part[0]?.toUpperCase())
      .slice(0, 2)
      .join('');
  }, [user?.name]);

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }, []);

  const moduleLabel = useMemo(() => {
    if (!user || user.role !== 'SUPERVISOR' || !user.supervisor_efficiency_module) return '';
    return user.supervisor_efficiency_module.replace(/_/g, ' ');
  }, [user]);

  return (
    <header className="sticky top-0 z-20 border-b border-[#E0E6ED] bg-white/90 backdrop-blur-sm shadow-md">
      <div className="flex items-center justify-between px-8 py-4">
        <div className="flex items-center gap-4">
          <img src={logo} alt="CMTI Logo" className="h-10 w-auto rounded-md shadow-sm" />
          <div>
            <h1 className="text-2xl font-semibold text-[#2C3E50]">
              {greeting}, {user?.name?.split(' ')[0] || 'there'}
            </h1>
            <p className="mt-1 text-sm text-[#6C7A89]">
              {user?.ec_number} • {user?.role}
              {moduleLabel && (
                <span className="ml-2 font-semibold text-[#2C3E50]">• {moduleLabel}</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#4A90E2]/10 text-[#4A90E2] font-semibold">
              {userInitials}
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-[#2C3E50]">{user?.name}</p>
              <p className="text-xs text-[#6C7A89]">
                {user?.role}
                {moduleLabel && (
                  <span className="ml-1 font-semibold text-[#2C3E50]">({moduleLabel})</span>
                )}
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="inline-flex items-center gap-2 rounded-full bg-[#E74C3C] px-4 py-2 text-sm font-semibold text-white shadow-md transition-transform duration-150 hover:-translate-y-0.5 hover:bg-[#C0392B] focus:outline-none focus:ring-2 focus:ring-[#E74C3C] focus:ring-offset-2">
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
