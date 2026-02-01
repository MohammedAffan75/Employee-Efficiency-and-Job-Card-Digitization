import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Calendar, BarChart3, Download } from 'lucide-react';

interface MonthlyMetrics {
  month: string;
  time_efficiency: number;
  quantity_efficiency: number;
  task_efficiency: number;
  awc_pct: number;
}

interface ActivityDistribution {
  activity_type: string;
  count: number;
  hours: number;
}

const AnalyticsPage = () => {
  const { user } = useAuth();
  const [monthlyData, setMonthlyData] = useState<MonthlyMetrics[]>([]);
  const [activityDist, setActivityDist] = useState<ActivityDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().setMonth(new Date().getMonth() - 6)).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange, user]);

  const fetchAnalytics = async () => {
    if (!user?.id) return;

    setLoading(true);
    try {
      const [monthlyRes, distRes] = await Promise.all([
        api.get(`/reporting/monthly-trend?employee_id=${user.id}&start=${dateRange.start}&end=${dateRange.end}`),
        api.get(`/reporting/activity-distribution?employee_id=${user.id}&start=${dateRange.start}&end=${dateRange.end}`),
      ]);

      setMonthlyData(monthlyRes.data);
      setActivityDist(distRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    toast.success('Report download feature - Coming soon!');
  };

  const COLORS = ['#627d98', '#38b2ac', '#f59e0b', '#ef4444', '#22c55e'];

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
          <h1 className="text-3xl font-bold text-secondary-900">My Analytics</h1>
          <p className="text-secondary-600 mt-1">Personal performance trends and insights</p>
        </div>
        <button
          onClick={downloadReport}
          className="flex items-center space-x-2 px-4 py-2 bg-accent-600 text-white rounded-md hover:bg-accent-700 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export Data</span>
        </button>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center space-x-4">
          <Calendar className="w-5 h-5 text-secondary-600" />
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-secondary-700">From:</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="px-3 py-1 border border-secondary-300 rounded-md text-sm"
            />
          </div>
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-secondary-700">To:</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="px-3 py-1 border border-secondary-300 rounded-md text-sm"
            />
          </div>
        </div>
      </div>

      {/* Efficiency Trend Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-secondary-900">Efficiency Trends (Last 6 Months)</h2>
        </div>
        {monthlyData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis label={{ value: 'Efficiency %', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="time_efficiency" stroke="#627d98" strokeWidth={2} name="Time Efficiency" />
              <Line type="monotone" dataKey="quantity_efficiency" stroke="#38b2ac" strokeWidth={2} name="Quantity Efficiency" />
              <Line type="monotone" dataKey="task_efficiency" stroke="#f59e0b" strokeWidth={2} name="Task Efficiency" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-secondary-500">
            <p>No trend data available for the selected period</p>
          </div>
        )}
      </div>

      {/* Activity Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-2 mb-4">
            <BarChart3 className="w-5 h-5 text-accent-600" />
            <h2 className="text-lg font-semibold text-secondary-900">Activity Type Distribution</h2>
          </div>
          {activityDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={activityDist}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.activity_type}: ${entry.count}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {activityDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-secondary-500">
              <p>No activity data available</p>
            </div>
          )}
        </div>

        {/* Activity Table */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">Activity Breakdown</h2>
          {activityDist.length > 0 ? (
            <div className="space-y-3">
              {activityDist.map((activity, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-secondary-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                    ></div>
                    <span className="font-medium text-secondary-900">{activity.activity_type}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-secondary-900">{activity.count} tasks</p>
                    <p className="text-xs text-secondary-600">{activity.hours.toFixed(1)} hours</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-secondary-500">
              <p>No activity data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Performance Insights */}
      <div className="bg-gradient-to-r from-primary-50 to-accent-50 border border-primary-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">📊 Performance Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Best Month</p>
            <p className="text-xl font-bold text-success-600">
              {monthlyData.length > 0
                ? monthlyData.reduce((max, curr) =>
                    curr.time_efficiency > max.time_efficiency ? curr : max
                  ).month
                : 'N/A'}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Average Efficiency</p>
            <p className="text-xl font-bold text-primary-600">
              {monthlyData.length > 0
                ? (
                    monthlyData.reduce((sum, curr) => sum + curr.time_efficiency, 0) /
                    monthlyData.length
                  ).toFixed(1)
                : 'N/A'}
              %
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Most Common Activity</p>
            <p className="text-xl font-bold text-accent-600">
              {activityDist.length > 0
                ? activityDist.reduce((max, curr) => (curr.count > max.count ? curr : max))
                    .activity_type
                : 'N/A'}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Total Hours Tracked</p>
            <p className="text-xl font-bold text-warning-600">
              {activityDist.length > 0
                ? activityDist.reduce((sum, curr) => sum + curr.hours, 0).toFixed(1)
                : '0'}
              {' hrs'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
