import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { EfficiencyMetrics, JobCard } from '../../types';
import { TrendingUp, TrendingDown, Clock, Target, BarChart3, AlertCircle, Plus } from 'lucide-react';
import toast from 'react-hot-toast';

interface KPICardProps {
  title: string;
  value: number | null | undefined;
  unit?: string;
  icon: React.ElementType;
  color: string;
}

const KPICard = ({ title, value, unit = '%', icon: Icon, color }: KPICardProps) => {
  const displayValue = value !== null && value !== undefined ? value.toFixed(1) : 'N/A';
  const isGood = value !== null && value !== undefined && value >= 80;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-secondary-600">{title}</p>
          <div className="flex items-baseline mt-2">
            <p className="text-3xl font-bold text-secondary-900">
              {displayValue !== 'N/A' ? displayValue : 'N/A'}
            </p>
            {displayValue !== 'N/A' && <span className="ml-1 text-lg text-secondary-600">{unit}</span>}
          </div>
        </div>
        <div className={`p-3 rounded-full`} style={{ backgroundColor: `${color}20` }}>
          <Icon className="w-6 h-6" style={{ color }} />
        </div>
      </div>
      {value !== null && value !== undefined && (
        <div className="mt-3 flex items-center text-sm">
          {isGood ? (
            <TrendingUp className="w-4 h-4 text-success-600 mr-1" />
          ) : (
            <TrendingDown className="w-4 h-4 text-danger-600 mr-1" />
          )}
          <span className={isGood ? 'text-success-600' : 'text-danger-600'}>
            {isGood ? 'Good' : 'Needs Improvement'}
          </span>
        </div>
      )}
    </div>
  );
};

const OperatorDashboard = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<EfficiencyMetrics | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [user]);

  const fetchDashboardData = async () => {
    if (!user?.id) return;

    setLoading(true);
    try {
      const end = new Date().toISOString().split('T')[0];
      const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      const [effResponse, jobsResponse] = await Promise.all([
        api.get(`/efficiency/${user.id}?start=${start}&end=${end}`),
        api.get(`/jobcards?employee_id=${user.id}&limit=5`),
      ]);

      setMetrics(effResponse.data);
      setRecentJobs(jobsResponse.data);
    } catch (error: any) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    return status === 'C' ? (
      <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">
        Complete
      </span>
    ) : (
      <span className="px-2 py-1 text-xs font-medium rounded-full bg-warning-100 text-warning-800">
        Incomplete
      </span>
    );
  };

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Dashboard</h1>
          <p className="text-secondary-600 mt-1">
            {user?.name} ({user?.ec_number}) - Last 30 Days Performance
          </p>
        </div>
        <Link
          to="/operator/jobcards/new"
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>New Job Card</span>
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <KPICard
          title="Time Efficiency"
          value={metrics?.time_efficiency}
          icon={Clock}
          color="#627d98"
        />
        <KPICard
          title="Quantity Efficiency"
          value={metrics?.quantity_efficiency}
          icon={BarChart3}
          color="#38b2ac"
        />
        <KPICard
          title="Task Efficiency"
          value={metrics?.task_efficiency}
          icon={Target}
          color="#f59e0b"
        />
      </div>

      {/* Performance Summary removed as requested */}

      {/* Recent Job Cards */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-secondary-900">Recent Job Cards</h2>
          <Link
            to="/operator/jobcards"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            View All →
          </Link>
        </div>

        {recentJobs.length === 0 ? (
          <div className="text-center py-8 text-secondary-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-2 text-secondary-400" />
            <p>No job cards found</p>
            <Link
              to="/operator/jobcards/new"
              className="text-primary-600 hover:text-primary-700 text-sm mt-2 inline-block"
            >
              Create your first job card
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary-200">
              <thead className="bg-secondary-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Activity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Hours
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-secondary-200">
                {recentJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-secondary-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-secondary-900">
                      {new Date(job.entry_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-secondary-900">{job.activity_desc}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-secondary-900">
                      {job.qty}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-secondary-900">
                      {job.actual_hours}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {getStatusBadge(job.status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default OperatorDashboard;
