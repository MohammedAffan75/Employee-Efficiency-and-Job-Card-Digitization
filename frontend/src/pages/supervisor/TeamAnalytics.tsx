import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import toast from 'react-hot-toast';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, Users, Calendar, Download } from 'lucide-react';

interface TeamTrendData {
  month: string;
  avg_time_eff: number;
  avg_qty_eff: number;
  avg_task_eff: number;
  employee_count: number;
}

interface EmployeeComparison {
  employee_name: string;
  ec_number: string;
  current_month: number;
  last_month: number;
  trend: 'up' | 'down' | 'stable';
}

const TeamAnalytics = () => {
  const { user } = useAuth();
  const [trendData, setTrendData] = useState<TeamTrendData[]>([]);
  const [employeeComparison, setEmployeeComparison] = useState<EmployeeComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const supervisorModule = user?.supervisor_efficiency_module;

  useEffect(() => {
    fetchTeamAnalytics();
  }, [user]);

  const fetchTeamAnalytics = async () => {
    setLoading(true);
    try {
      const supervisorModule = user?.supervisor_efficiency_module;
      const params = supervisorModule ? `?efficiency_module=${supervisorModule}` : '';
      
      const [trendRes, comparisonRes] = await Promise.all([
        api.get(`/reporting/all-trend${params}`),
        api.get(`/reporting/employee-comparison${params}`),
      ]);

      setTrendData(trendRes.data);
      setEmployeeComparison(comparisonRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    try {
      // Prepare CSV data
      const csvRows: string[] = [];
      
      // Add header section
      csvRows.push(`Employee Analytics Report`);
      csvRows.push(`Generated: ${new Date().toLocaleString()}`);
      csvRows.push('');
      
      // Add 6-Month Trend Data
      csvRows.push('=== 6-MONTH PERFORMANCE TREND ===');
      csvRows.push('Month,Avg Time Efficiency %,Avg Quantity Efficiency %,Avg Task Efficiency %,Employee Count');
      trendData.forEach(row => {
        csvRows.push(
          `${row.month},${row.avg_time_eff.toFixed(2)},${row.avg_qty_eff.toFixed(2)},${row.avg_task_eff.toFixed(2)},${row.employee_count}`
        );
      });
      csvRows.push('');
      
      // Add Employee Comparison Data
      csvRows.push('=== MONTH-OVER-MONTH EMPLOYEE PERFORMANCE ===');
      csvRows.push('Employee Name,EC Number,Current Month %,Last Month %,Change %,Trend');
      employeeComparison.forEach(emp => {
        const change = (emp.current_month - emp.last_month).toFixed(2);
        csvRows.push(
          `"${emp.employee_name}",${emp.ec_number},${emp.current_month.toFixed(2)},${emp.last_month.toFixed(2)},${change},${emp.trend.toUpperCase()}`
        );
      });
      csvRows.push('');
      
      // Add Employee Insights
      csvRows.push('=== EMPLOYEE INSIGHTS ===');
      if (employeeComparison.length > 0) {
        const topPerformer = employeeComparison.reduce((max, curr) =>
          curr.current_month > max.current_month ? curr : max
        );
        const mostImproved = employeeComparison.reduce((max, curr) => {
          const maxChange = max.current_month - max.last_month;
          const currChange = curr.current_month - curr.last_month;
          return currChange > maxChange ? curr : max;
        });
        const employeeAverage = (
          employeeComparison.reduce((sum, curr) => sum + curr.current_month, 0) /
          employeeComparison.length
        ).toFixed(2);
        
        csvRows.push(`Top Performer,"${topPerformer.employee_name}",${topPerformer.current_month.toFixed(2)}%`);
        csvRows.push(`Most Improved,"${mostImproved.employee_name}",+${(mostImproved.current_month - mostImproved.last_month).toFixed(2)}%`);
        csvRows.push(`Employee Average,${employeeAverage}%`);
      }

      // Add Employee Job Card Summary (Accepted / Rejected / Pending)
      try {
        const supervisorModule = user?.supervisor_efficiency_module;
        const summaryParams = supervisorModule ? `?efficiency_module=${supervisorModule}` : '';
        const summaryRes = await api.get(`/reporting/employee-jobcard-summary${summaryParams}`);
        const summaryData = summaryRes.data as Array<{
          ec_number: string;
          name: string;
          total_jobcards: number;
          accepted_count: number;
          rejected_count: number;
          pending_count: number;
        }>;

        csvRows.push('');
        csvRows.push('=== EMPLOYEE JOBCARD SUMMARY (CURRENT PERIOD) ===');
        csvRows.push('EC Number,Employee Name,Total Job Cards,Accepted,Rejected,Pending');

        summaryData.forEach((emp) => {
          csvRows.push(
            `"${emp.ec_number}","${emp.name}",${emp.total_jobcards},${emp.accepted_count},${emp.rejected_count},${emp.pending_count}`
          );
        });
      } catch (error) {
        console.error('Failed to fetch jobcard summary for export:', error);
        csvRows.push('');
        csvRows.push('=== EMPLOYEE JOBCARD SUMMARY ===');
        csvRows.push('Failed to load jobcard summary data');
      }
      
      // Create CSV blob and download
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      link.setAttribute('href', url);
      link.setAttribute('download', `employee_analytics_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success('Analytics report exported successfully!');
    } catch (error) {
      console.error('Failed to export report:', error);
      toast.error('Failed to export analytics report');
    }
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-success-600" />;
    if (trend === 'down') return <TrendingUp className="w-4 h-4 text-danger-600 rotate-180" />;
    return <div className="w-4 h-4 bg-secondary-400 rounded-full"></div>;
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
          <h1 className="text-3xl font-bold text-secondary-900">Employee Analytics</h1>
          <p className="text-secondary-600 mt-1">
            Performance analysis for {user?.supervisor_efficiency_module?.replace(/_/g, ' ') || 'your'} efficiency module
          </p>
        </div>
        <button
          onClick={downloadReport}
          className="flex items-center space-x-2 px-4 py-2 bg-accent-600 text-white rounded-md hover:bg-accent-700 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export Analytics</span>
        </button>
      </div>

      {/* Team Trend Line Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">
          6-Month Employee Performance Trend
        </h2>
        {trendData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="colorEff" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#627d98" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#627d98" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis label={{ value: 'Efficiency %', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey={
                  supervisorModule === 'TIME_BASED'
                    ? 'avg_time_eff'
                    : supervisorModule === 'QUANTITY_BASED'
                    ? 'avg_qty_eff'
                    : 'avg_task_eff'
                }
                stroke="#627d98"
                fillOpacity={1}
                fill="url(#colorEff)"
                name={`${supervisorModule?.replace(/_/g, ' ') || 'Efficiency'}`}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-secondary-500">
            <p>No trend data available</p>
          </div>
        )}
      </div>

      {/* Employee Comparison */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Users className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-secondary-900">
            Month-over-Month Employee Performance
          </h2>
        </div>
        {employeeComparison.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary-200">
              <thead>
                <tr className="bg-secondary-50">
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase">
                    Employee
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase">
                    Current Month
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase">
                    Last Month
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase">
                    Change
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase">
                    Trend
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary-200">
                {employeeComparison.map((emp, idx) => {
                  const change = emp.current_month - emp.last_month;
                  return (
                    <tr key={idx} className="hover:bg-secondary-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="font-medium text-secondary-900">{emp.employee_name}</p>
                          <p className="text-sm text-secondary-500">{emp.ec_number}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-lg font-semibold text-secondary-900">
                          {emp.current_month.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-secondary-600">
                        {emp.last_month.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`font-semibold ${
                            change > 0
                              ? 'text-success-600'
                              : change < 0
                              ? 'text-danger-600'
                              : 'text-secondary-600'
                          }`}
                        >
                          {change > 0 ? '+' : ''}
                          {change.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">{getTrendIcon(emp.trend)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-secondary-500">
            <p>No comparison data available</p>
          </div>
        )}
      </div>

      {/* Employee Insights */}
      <div className="bg-gradient-to-r from-primary-50 to-accent-50 border border-primary-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">📈 Employee Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Top Performer</p>
            <p className="text-xl font-bold text-success-600">
              {employeeComparison.length > 0
                ? employeeComparison.reduce((max, curr) =>
                    curr.current_month > max.current_month ? curr : max
                  ).employee_name
                : 'N/A'}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Most Improved</p>
            <p className="text-xl font-bold text-primary-600">
              {employeeComparison.length > 0
                ? employeeComparison.reduce((max, curr) => {
                    const maxChange = max.current_month - max.last_month;
                    const currChange = curr.current_month - curr.last_month;
                    return currChange > maxChange ? curr : max;
                  }).employee_name
                : 'N/A'}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="text-sm text-secondary-600 mb-1">Employee Average</p>
            <p className="text-xl font-bold text-accent-600">
              {employeeComparison.length > 0
                ? (
                    employeeComparison.reduce((sum, curr) => sum + curr.current_month, 0) /
                    employeeComparison.length
                  ).toFixed(1)
                : '0'}
              %
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamAnalytics;
