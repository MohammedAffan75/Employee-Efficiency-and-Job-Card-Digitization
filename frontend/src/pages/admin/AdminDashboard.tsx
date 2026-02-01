import { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Users, Database, Activity, TrendingUp } from 'lucide-react';

interface SystemStats {
  total_employees: number;
  active_employees: number;
  total_machines: number;
  total_activity_codes: number;
  total_job_cards_month: number;
  total_validations_unresolved: number;
}

interface RoleDistribution {
  role: string;
  count: number;
}

interface TeamPerformance {
  employee_id: number;
  employee_name: string;
  ec_number: string;
  time_efficiency: number;
  quantity_efficiency: number;
  task_efficiency: number;
  total_hours: number;
}

const AdminDashboard = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [roleData, setRoleData] = useState<RoleDistribution[]>([]);
  const [teamData, setTeamData] = useState<TeamPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminDashboard();
  }, []);

  const fetchAdminDashboard = async () => {
    setLoading(true);
    try {
      const [statsRes, roleRes, employeeRes] = await Promise.all([
        api.get('/admin/dashboard/stats'),
        api.get('/admin/dashboard/role-distribution'),
        api.get('/admin/dashboard/employee-performance'),
      ]);

      setStats(statsRes.data);
      setRoleData(roleRes.data);
      setTeamData(employeeRes.data);
    } catch (error) {
      console.error('Failed to fetch admin dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#627d98', '#38b2ac', '#f59e0b'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Admin Dashboard</h1>
        <p className="text-secondary-600 mt-1">System overview and analytics</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-600">Total Employees</p>
                <p className="text-3xl font-bold text-secondary-900 mt-1">{stats.total_employees}</p>
                <p className="text-xs text-success-600 mt-1">{stats.active_employees} active</p>
              </div>
              <Users className="w-12 h-12 text-primary-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-600">Machines</p>
                <p className="text-3xl font-bold text-secondary-900 mt-1">{stats.total_machines}</p>
                <p className="text-xs text-secondary-500 mt-1">Total registered</p>
              </div>
              <Database className="w-12 h-12 text-accent-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-600">Activity Codes</p>
                <p className="text-3xl font-bold text-secondary-900 mt-1">{stats.total_activity_codes}</p>
                <p className="text-xs text-secondary-500 mt-1">Configured</p>
              </div>
              <Activity className="w-12 h-12 text-warning-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-600">Job Cards (This Month)</p>
                <p className="text-3xl font-bold text-secondary-900 mt-1">{stats.total_job_cards_month}</p>
                <p className="text-xs text-secondary-500 mt-1">Created</p>
              </div>
              <TrendingUp className="w-12 h-12 text-success-600" />
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Role Distribution Pie Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">Employee Role Distribution</h2>
          {roleData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={roleData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.role}: ${entry.count}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {roleData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-secondary-500">
              <p>No role data available</p>
            </div>
          )}
        </div>

        {/* Employee Performance Line Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">Employee Performance Overview</h2>
          {teamData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={teamData.sort((a, b) => a.time_efficiency - b.time_efficiency)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="employee_name" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80}
                    interval={0}
                  />
                  <YAxis label={{ value: 'Efficiency %', angle: -90, position: 'insideLeft' }} />
                  <Tooltip 
                    formatter={(value: any, name: string) => [`${value}%`, name]}
                    labelFormatter={(label) => `Employee: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="time_efficiency" 
                    stroke="#627d98" 
                    strokeWidth={2}
                    name="Time Efficiency" 
                    dot={{ fill: '#627d98', strokeWidth: 2, r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="quantity_efficiency" 
                    stroke="#38b2ac" 
                    strokeWidth={2}
                    name="Quantity Efficiency" 
                    dot={{ fill: '#38b2ac', strokeWidth: 2, r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="task_efficiency" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    name="Task Efficiency" 
                    dot={{ fill: '#f59e0b', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-secondary-500">
              <p>No employee data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/supervisor/employees"
            className="p-4 border-2 border-secondary-200 rounded-lg hover:border-primary-400 hover:bg-primary-50 transition-all"
          >
            <Users className="w-6 h-6 text-primary-600 mb-2" />
            <h3 className="font-semibold text-secondary-900">View Employees</h3>
            <p className="text-sm text-secondary-600 mt-1">View all employees list</p>
          </a>
          <a
            href="/supervisor/activity-codes"
            className="p-4 border-2 border-secondary-200 rounded-lg hover:border-accent-400 hover:bg-accent-50 transition-all"
          >
            <Activity className="w-6 h-6 text-accent-600 mb-2" />
            <h3 className="font-semibold text-secondary-900">View Activity Codes</h3>
            <p className="text-sm text-secondary-600 mt-1">View activity codes list</p>
          </a>
          <a
            href="/supervisor/machines"
            className="p-4 border-2 border-secondary-200 rounded-lg hover:border-warning-400 hover:bg-warning-50 transition-all"
          >
            <Database className="w-6 h-6 text-warning-600 mb-2" />
            <h3 className="font-semibold text-secondary-900">View Machines</h3>
            <p className="text-sm text-secondary-600 mt-1">View machines list</p>
          </a>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-gradient-to-r from-success-50 to-primary-50 border border-success-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">🎯 System Health</h2>
        <div className="grid grid-cols-1 gap-4">
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-2">Active Users Ratio</p>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-secondary-200 rounded-full h-3">
                <div
                  className="bg-success-600 h-3 rounded-full"
                  style={{
                    width: `${stats ? (stats.active_employees / stats.total_employees) * 100 : 0}%`,
                  }}
                ></div>
              </div>
              <span className="text-sm font-semibold text-secondary-900">
                {stats ? ((stats.active_employees / stats.total_employees) * 100).toFixed(0) : 0}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
