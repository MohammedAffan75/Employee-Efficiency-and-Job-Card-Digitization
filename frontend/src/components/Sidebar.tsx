import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Settings,
  ClipboardList,
  AlertCircle,
  BarChart3,
  Database,
  Package
} from 'lucide-react';
import { useRole } from '../hooks/useRole';

const Sidebar = () => {
  const location = useLocation();
  const { isOperator, isSupervisor, isAdmin } = useRole();

  const isActive = (path: string) => location.pathname.startsWith(path);

  const operatorLinks = [
    { to: '/operator/jobcards', icon: ClipboardList, label: 'Job Cards' },
    { to: '/operator/assigned', icon: ClipboardList, label: 'Assigned Tasks' },
    { to: '/operator/analytics', icon: BarChart3, label: 'Analytics' },
  ];

  const supervisorLinks = [
    { to: '/supervisor/assignments', icon: Users, label: 'Assign Work' },
    { to: '/supervisor/validations', icon: AlertCircle, label: 'Job Card Review' },
    { to: '/supervisor/employees', icon: Users, label: 'Employees' },
    { to: '/supervisor/activity-codes', icon: Database, label: 'Activity Codes' },
    { to: '/supervisor/machines', icon: Settings, label: 'Machines' },
    { to: '/supervisor/work-orders', icon: Package, label: 'Work Orders' },
  ];

  const adminLinks = [
    { to: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
  ];

  let links: Array<{ to: string; icon: any; label: string }> = [];
  if (isOperator) links = operatorLinks;
  if (isSupervisor) links = supervisorLinks;
  if (isAdmin) links = adminLinks;

  return (
    <aside className="fixed left-0 top-0 flex h-screen w-72 flex-col bg-white shadow-xl rounded-r-3xl p-6 z-40">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-[#2C3E50]">Employee Efficiency Suite</h1>
      </div>

      <nav className="mt-8 flex-1 space-y-1">
        {links.map((link) => {
          const Icon = link.icon;
          const active = isActive(link.to);

          return (
            <Link
              key={link.to}
              to={link.to}
              className={`group flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-150 ${
                active
                  ? 'bg-[#4A90E2] text-white shadow-lg'
                  : 'text-[#6C7A89] hover:bg-[#E8F1FD] hover:text-[#2C3E50]'
              }`}
            >
              <Icon
                className={`h-5 w-5 transition-colors ${
                  active ? 'text-white' : 'text-[#4A90E2] group-hover:text-[#4A90E2]'
                }`}
              />
              <span>{link.label}</span>
            </Link>
          );
        })}
      </nav>

    </aside>
  );
};

export default Sidebar;
