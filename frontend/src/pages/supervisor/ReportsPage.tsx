import { useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Download, Calendar, FileText, TrendingUp } from 'lucide-react';

const ReportsPage = () => {
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [downloading, setDownloading] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const handleDownloadReport = async () => {
    if (!selectedMonth) {
      toast.error('Please select a month');
      return;
    }

    setDownloading(true);
    try {
      const response = await api.get(`/reporting/report/monthly?month=${selectedMonth}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${selectedMonth}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Report downloaded successfully!');
    } catch (error: any) {
      console.error('Failed to download report:', error);
      toast.error(error.response?.data?.detail || 'Failed to download report');
    } finally {
      setDownloading(false);
    }
  };

  const handlePreviewReport = async () => {
    if (!selectedMonth) {
      toast.error('Please select a month');
      return;
    }

    setLoadingPreview(true);
    try {
      const response = await api.get(
        `/reporting/dashboard/summary?month=${selectedMonth}`
      );
      setPreviewData(response.data);
    } catch (error: any) {
      console.error('Failed to preview report:', error);
      toast.error('Failed to load preview');
    } finally {
      setLoadingPreview(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Reports</h1>
        <p className="text-secondary-600 mt-1">Generate and download performance reports</p>
      </div>

      {/* Report Configuration */}
      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-secondary-900">Monthly Report</h2>
        </div>

        {/* Month Selection */}
        <div>
          <label htmlFor="month" className="block text-sm font-medium text-secondary-700 mb-1">
            Select Month
          </label>
          <div className="flex items-center space-x-3">
            <div className="relative flex-1">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-secondary-400" />
              <input
                type="month"
                id="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <button
              onClick={handlePreviewReport}
              disabled={loadingPreview}
              className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors disabled:opacity-50"
            >
              {loadingPreview ? 'Loading...' : 'Preview'}
            </button>
          </div>
        </div>

        {/* Report Info */}
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-primary-900 mb-2">Report Contents:</h3>
          <ul className="text-sm text-primary-800 space-y-1 list-disc list-inside">
            <li>Employee-wise efficiency metrics</li>
            <li>Time, Quantity, and Task efficiency percentages</li>
            <li>Standard hours allowed vs Actual hours worked</li>
            <li>AWC (Activity Without Code) percentage</li>
            <li>Period start and end dates</li>
            <li>Employee details</li>
          </ul>
        </div>

        {/* Download Button */}
        <div className="flex items-center justify-end pt-4 border-t border-secondary-200">
          <button
            onClick={handleDownloadReport}
            disabled={downloading || !selectedMonth}
            className="flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-5 h-5" />
            <span>{downloading ? 'Downloading...' : 'Download CSV Report'}</span>
          </button>
        </div>
      </div>

      {/* Preview Section */}
      {previewData && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-2 mb-4">
            <TrendingUp className="w-5 h-5 text-accent-600" />
            <h2 className="text-lg font-semibold text-secondary-900">Report Preview</h2>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div className="p-4 bg-secondary-50 rounded-lg">
              <p className="text-sm text-secondary-600">Total Employees</p>
              <p className="text-xl font-bold text-secondary-900">
                {previewData.employee_count || 0}
              </p>
            </div>
            <div className="p-4 bg-secondary-50 rounded-lg">
              <p className="text-sm text-secondary-600">Avg Time Efficiency</p>
              <p className="text-xl font-bold text-secondary-900">
                {previewData.avg_time_efficiency?.toFixed(1) || 'N/A'}%
              </p>
            </div>
            <div className="p-4 bg-secondary-50 rounded-lg">
              <p className="text-sm text-secondary-600">Avg Quantity Efficiency</p>
              <p className="text-xl font-bold text-secondary-900">
                {previewData.avg_qty_efficiency?.toFixed(1) || 'N/A'}%
              </p>
            </div>
            <div className="p-4 bg-secondary-50 rounded-lg">
              <p className="text-sm text-secondary-600">Total Standard Hours</p>
              <p className="text-xl font-bold text-secondary-900">
                {previewData.total_std_hours?.toFixed(1) || '0.0'}
              </p>
            </div>
            <div className="p-4 bg-secondary-50 rounded-lg">
              <p className="text-sm text-secondary-600">Total Actual Hours</p>
              <p className="text-xl font-bold text-secondary-900">
                {previewData.total_actual_hours?.toFixed(1) || '0.0'}
              </p>
            </div>
          </div>

          <div className="mt-4 p-4 bg-accent-50 border border-accent-200 rounded-lg">
            <p className="text-sm text-accent-900">
              💡 <strong>Tip:</strong> This is a summary preview. Download the full CSV report for
              detailed employee-level data.
            </p>
          </div>
        </div>
      )}

      {/* Report Types */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">Available Report Types</h2>

        <div className="space-y-3">
          <div className="p-4 border border-secondary-200 rounded-lg hover:border-primary-400 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-secondary-900">Monthly Efficiency Report</h3>
                <p className="text-sm text-secondary-600 mt-1">
                  Comprehensive efficiency metrics for all employees for a selected month
                </p>
              </div>
              <span className="px-2 py-1 bg-success-100 text-success-800 text-xs font-medium rounded-full">
                Active
              </span>
            </div>
          </div>

          <div className="p-4 border border-secondary-200 rounded-lg opacity-60">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-secondary-900">Daily Job Card Report</h3>
                <p className="text-sm text-secondary-600 mt-1">
                  Detailed daily job card entries with validation flags
                </p>
              </div>
              <span className="px-2 py-1 bg-secondary-100 text-secondary-600 text-xs font-medium rounded-full">
                Coming Soon
              </span>
            </div>
          </div>

          <div className="p-4 border border-secondary-200 rounded-lg opacity-60">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-secondary-900">AWC Analysis Report</h3>
                <p className="text-sm text-secondary-600 mt-1">
                  Analysis of activities without codes and trends
                </p>
              </div>
              <span className="px-2 py-1 bg-secondary-100 text-secondary-600 text-xs font-medium rounded-full">
                Coming Soon
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
