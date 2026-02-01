import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { DashboardSummary, EfficiencyMetrics } from '../../types';
import { Users, TrendingUp, Clock, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface TeamMemberMetrics extends EfficiencyMetrics {
  employee_name?: string;
  ec_number?: string;
}

const SupervisorDashboard = () => {
  const { user } = useAuth();
  const supervisorModule = user?.supervisor_efficiency_module || '';
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [employeeMetrics, setEmployeeMetrics] = useState<TeamMemberMetrics[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [user]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Get current month date range
      const end = new Date().toISOString().split('T')[0];
      const start = new Date(new Date().setDate(1)).toISOString().split('T')[0];

      const [summaryRes, metricsRes] = await Promise.all([
        api.get(`/reporting/dashboard/summary?start=${start}&end=${end}&force=true`),
        api.get(`/reporting/all-employees-efficiency?start=${start}&end=${end}&force=true`),
      ]);

      setSummary(summaryRes.data);
      setEmployeeMetrics(metricsRes.data);
    } catch (error: any) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const KPICard = ({ title, value, unit = '%', icon: Icon, color }: any) => {
    const displayValue = value !== null && value !== undefined ? value.toFixed(1) : 'N/A';

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
          <div className="p-3 rounded-full" style={{ backgroundColor: `${color}20` }}>
            <Icon className="w-6 h-6" style={{ color }} />
          </div>
        </div>
      </div>
    );
  };

  // Prepare chart data - Different data for each module type
  const prepareChartData = () => {
    if (supervisorModule === 'TIME_BASED') {
      return employeeMetrics
        .map((metric) => ({
          name: metric.ec_number || 'Unknown',
          timeEff: metric.time_efficiency || 0,
        }))
        .sort((a, b) => b.timeEff - a.timeEff)
        .slice(0, 5);
    } else if (supervisorModule === 'QUANTITY_BASED') {
      return employeeMetrics
        .map((metric) => ({
          name: metric.ec_number || 'Unknown',
          qtyEff: metric.quantity_efficiency || 0,
        }))
        .sort((a, b) => b.qtyEff - a.qtyEff)
        .slice(0, 5);
    } else if (supervisorModule === 'TASK_BASED') {
      return employeeMetrics
        .map((metric) => ({
          name: metric.ec_number || 'Unknown',
          taskEff: metric.task_efficiency || 0,
        }))
        .sort((a, b) => b.taskEff - a.taskEff)
        .slice(0, 5);
    }
    // Default: show all metrics
    return employeeMetrics
      .map((metric) => {
        const time = metric.time_efficiency || 0;
        const qty = metric.quantity_efficiency || 0;
        const task = metric.task_efficiency || 0;
        const overall = (time + qty + task) / 3;
        return {
          name: metric.ec_number || 'Unknown',
          timeEff: time,
          qtyEff: qty,
          taskEff: task,
          overall,
        };
      })
      .sort((a, b) => b.overall - a.overall)
      .slice(0, 5);
  };

  const chartData = prepareChartData();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Render different content based on supervisor module
  const renderTimeBasedContent = () => {
    return (
      <>
        {/* Time-based KPI Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <KPICard
              title="Avg Time Efficiency"
              value={summary.avg_time_efficiency}
              icon={Clock}
              color="#627d98"
            />
            <KPICard
              title="Total Std Hours"
              value={summary.total_std_hours}
              icon={Clock}
              color="#38b2ac"
              unit="hrs"
            />
            <KPICard
              title="Total Actual Hours"
              value={summary.total_actual_hours}
              icon={Clock}
              color="#f59e0b"
              unit="hrs"
            />
          </div>
        )}

        {/* Time-based Employee Comparison Chart */}
        {chartData.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-secondary-900 mb-4">
              Employee Time Efficiency Comparison
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="timeEff" fill="#627d98" name="Time Efficiency %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Time-based Employee Performance Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Employee Time Performance</h2>
          </div>

          {employeeMetrics.length === 0 ? (
            <div className="text-center py-12 text-secondary-500">
              <Users className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
              <p className="text-lg font-medium">No employee data available</p>
              <p className="text-sm mt-2">Employees will appear here once they have job cards</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-secondary-200">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Employee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Time Eff %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Std Hours
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Actual Hours
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {employeeMetrics.map((metric, idx) => (
                    <tr key={idx} className="hover:bg-secondary-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="font-medium text-secondary-900">
                            {metric.employee_name || 'Unknown'}
                          </p>
                          <p className="text-sm text-secondary-500">{metric.ec_number}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            (metric.time_efficiency || 0) >= 80
                              ? 'bg-success-100 text-success-800'
                              : 'bg-warning-100 text-warning-800'
                          }`}
                        >
                          {metric.time_efficiency?.toFixed(1) || 'N/A'}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {metric.standard_hours_allowed?.toFixed(2) || '0.00'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {metric.actual_hours?.toFixed(2) || '0.00'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </>
    );
  };

  const renderQuantityBasedContent = () => {
    return (
      <>
        {/* Quantity-based KPI Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <KPICard
              title="Avg Quantity Efficiency"
              value={summary.avg_qty_efficiency}
              icon={BarChart3}
              color="#38b2ac"
            />
            <KPICard
              title="Total Std Quantity"
              value={summary.standard_quantity_allowed || 0}
              icon={BarChart3}
              color="#627d98"
              unit="units"
            />
            <KPICard
              title="Total Actual Quantity"
              value={summary.actual_quantity || 0}
              icon={BarChart3}
              color="#f59e0b"
              unit="units"
            />
          </div>
        )}

        {/* Quantity-based Employee Comparison Chart */}
        {chartData.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-secondary-900 mb-4">
              Employee Quantity Efficiency Comparison
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="qtyEff" fill="#38b2ac" name="Quantity Efficiency %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Quantity-based Employee Performance Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Employee Quantity Performance</h2>
          </div>

          {employeeMetrics.length === 0 ? (
            <div className="text-center py-12 text-secondary-500">
              <Users className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
              <p className="text-lg font-medium">No employee data available</p>
              <p className="text-sm mt-2">Employees will appear here once they have job cards</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-secondary-200">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Employee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Qty Eff %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Std Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Actual Quantity
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {employeeMetrics.map((metric, idx) => (
                    <tr key={idx} className="hover:bg-secondary-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="font-medium text-secondary-900">
                            {metric.employee_name || 'Unknown'}
                          </p>
                          <p className="text-sm text-secondary-500">{metric.ec_number}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            (metric.quantity_efficiency || 0) >= 80
                              ? 'bg-success-100 text-success-800'
                              : 'bg-warning-100 text-warning-800'
                          }`}
                        >
                          {metric.quantity_efficiency?.toFixed(1) || 'N/A'}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {metric.standard_quantity_allowed?.toFixed(2) || '0.00'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {metric.actual_quantity?.toFixed(2) || '0.00'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </>
    );
  };

  const renderTaskBasedContent = () => {
    return (
      <>
        {/* Task-based KPI Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <KPICard
              title="Avg Task Efficiency"
              value={summary.avg_task_efficiency}
              icon={TrendingUp}
              color="#f59e0b"
            />
            <KPICard
              title="Total Tasks Completed"
              value={summary.total_tasks || 0}
              icon={TrendingUp}
              color="#627d98"
              unit="tasks"
            />
            <KPICard
              title="Total Employees"
              value={employeeMetrics.length}
              icon={Users}
              color="#38b2ac"
              unit="employees"
            />
          </div>
        )}

        {/* Task-based Employee List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Employee Task Efficiency</h2>
          </div>

          {employeeMetrics.length === 0 ? (
            <div className="text-center py-12 text-secondary-500">
              <Users className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
              <p className="text-lg font-medium">No employee data available</p>
              <p className="text-sm mt-2">Employees will appear here once they have job cards</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-secondary-200">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Employee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Task Eff %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Tasks Completed
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Total Tasks
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {employeeMetrics.map((metric, idx) => (
                    <tr key={idx} className="hover:bg-secondary-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <p className="font-medium text-secondary-900">
                            {metric.employee_name || 'Unknown'}
                          </p>
                          <p className="text-sm text-secondary-500">{metric.ec_number}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            (metric.task_efficiency || 0) >= 80
                              ? 'bg-success-100 text-success-800'
                              : 'bg-warning-100 text-warning-800'
                          }`}
                        >
                          {metric.task_efficiency?.toFixed(1) || 'N/A'}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {metric.tasks_completed || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {metric.total_tasks || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Supervisor Dashboard</h1>
        <p className="text-secondary-600 mt-1">
          {supervisorModule
            ? `${supervisorModule.replace(/_/g, ' ')} Module - Current Month`
            : 'All Employees Performance - Current Month'}
        </p>
      </div>

      {/* Render content based on supervisor module */}
      {supervisorModule === 'TIME_BASED' && renderTimeBasedContent()}
      {supervisorModule === 'QUANTITY_BASED' && renderQuantityBasedContent()}
      {supervisorModule === 'TASK_BASED' && renderTaskBasedContent()}
      
      {/* Fallback for no module or unknown module */}
      {!supervisorModule || !['TIME_BASED', 'QUANTITY_BASED', 'TASK_BASED'].includes(supervisorModule) && (
        <>
          {/* Default KPI Cards */}
          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <KPICard
                title="Avg Time Efficiency"
                value={summary.avg_time_efficiency}
                icon={Clock}
                color="#627d98"
              />
              <KPICard
                title="Avg Quantity Efficiency"
                value={summary.avg_qty_efficiency}
                icon={BarChart3}
                color="#38b2ac"
              />
              <KPICard
                title="Avg Task Efficiency"
                value={summary.avg_task_efficiency}
                icon={TrendingUp}
                color="#f59e0b"
              />
            </div>
          )}

          {/* Default Employee Performance Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="px-6 py-4 border-b border-secondary-200">
              <h2 className="text-lg font-semibold text-secondary-900">Employee Performance</h2>
            </div>

            {employeeMetrics.length === 0 ? (
              <div className="text-center py-12 text-secondary-500">
                <Users className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
                <p className="text-lg font-medium">No employee data available</p>
                <p className="text-sm mt-2">Employees will appear here once they have job cards</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-secondary-200">
                  <thead className="bg-secondary-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                        Employee
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                        Time Eff %
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                        Qty Eff %
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                        Task Eff %
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-secondary-200">
                    {employeeMetrics.map((metric, idx) => (
                      <tr key={idx} className="hover:bg-secondary-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <p className="font-medium text-secondary-900">
                              {metric.employee_name || 'Unknown'}
                            </p>
                            <p className="text-sm text-secondary-500">{metric.ec_number}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${
                              (metric.time_efficiency || 0) >= 80
                                ? 'bg-success-100 text-success-800'
                                : 'bg-warning-100 text-warning-800'
                            }`}
                          >
                            {metric.time_efficiency?.toFixed(1) || 'N/A'}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${
                              (metric.quantity_efficiency || 0) >= 80
                                ? 'bg-success-100 text-success-800'
                                : 'bg-warning-100 text-warning-800'
                            }`}
                          >
                            {metric.quantity_efficiency?.toFixed(1) || 'N/A'}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${
                              (metric.task_efficiency || 0) >= 80
                                ? 'bg-success-100 text-success-800'
                                : 'bg-warning-100 text-warning-800'
                            }`}
                          >
                            {metric.task_efficiency?.toFixed(1) || 'N/A'}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default SupervisorDashboard;
