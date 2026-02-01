import { useEffect, useState, Fragment, useCallback } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { AlertCircle, XCircle, Filter, RefreshCw, Eye, Check, X, FileText } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface JobCardReview {
  id: number;
  employee_id?: number;
  employee_name?: string;
  employee_ec_number?: string;
  machine_code: string;
  wo_number: string;
  activity_desc: string;
  activity_code?: string;
  efficiency_module: string;
  qty: number;
  actual_hours: number;
  status: string;
  entry_date: string;
  shift: string;
  approval_status: string;
  has_flags: boolean;
  std_hours_per_unit?: number;
  std_qty_per_hour?: number;
}

interface SupervisorApprovalRequest {
  action: 'APPROVE' | 'REJECT';
  remarks?: string;
}

const ValidationPanel = () => {
  const { user } = useAuth();
  const supervisorModule = user?.supervisor_efficiency_module || '';
  const [jobCards, setJobCards] = useState<JobCardReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEfficiencyModule, setSelectedEfficiencyModule] = useState<string>(supervisorModule);
  const [selectedApprovalStatus, setSelectedApprovalStatus] = useState<string>('ALL');
  const [selectedJobCard, setSelectedJobCard] = useState<JobCardReview | null>(null);
  const [groupEntries, setGroupEntries] = useState<JobCardReview[]>([]);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [approvalAction, setApprovalAction] = useState<'APPROVE' | 'REJECT'>('APPROVE');
  const [approvalRemarks, setApprovalRemarks] = useState('');
  const [approving, setApproving] = useState(false);
  const [approvalTargets, setApprovalTargets] = useState<JobCardReview[]>([]);

  const fetchJobCards = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      // Only add approval_status filter if not "ALL"
      if (selectedApprovalStatus !== 'ALL') {
        params.append('approval_status', selectedApprovalStatus);
      }
      const moduleToUse = supervisorModule || selectedEfficiencyModule;
      if (moduleToUse) {
        params.append('efficiency_module', moduleToUse);
      }
      const response = await api.get(`/supervisor/jobcards/review?${params}`);
      const sorted = (response.data || []).sort((a: JobCardReview, b: JobCardReview) => 
        new Date(b.entry_date).getTime() - new Date(a.entry_date).getTime()
      );
      setJobCards(sorted);
    } catch (error) {
      console.error('Failed to fetch job cards:', error);
      toast.error('Failed to load job cards');
    } finally {
      setLoading(false);
    }
  }, [selectedEfficiencyModule, selectedApprovalStatus]);

  useEffect(() => {
    fetchJobCards();
  }, [fetchJobCards]);

  const handleViewDetails = (jobCard: JobCardReview) => {
    setSelectedJobCard(jobCard);
    setDetailsModalOpen(true);
  };

  const handleApprovalClick = (jobCard: JobCardReview, action: 'APPROVE' | 'REJECT') => {
    setSelectedJobCard(jobCard);
    setApprovalAction(action);
    setApprovalRemarks('');

    const related = jobCards.filter((jc) => {
      const sameEmployeeId =
        jc.employee_id !== undefined && jobCard.employee_id !== undefined
          ? jc.employee_id === jobCard.employee_id
          : jc.employee_name === jobCard.employee_name;
      const sameDate = jc.entry_date === jobCard.entry_date;
      const sameShift = jc.shift === jobCard.shift;
      const sameModule = jc.efficiency_module === jobCard.efficiency_module;
      return sameEmployeeId && sameDate && sameShift && sameModule;
    });

    const pendingRelated = related.filter((e) => e.approval_status === 'PENDING');
    setApprovalTargets(pendingRelated.length > 0 ? pendingRelated : [jobCard]);

    setApprovalModalOpen(true);
  };

  const handleApproval = async () => {
    if (!selectedJobCard) return;

    setApproving(true);
    try {
      const request: SupervisorApprovalRequest = {
        action: approvalAction,
        remarks: approvalRemarks,
      };

      const targets = approvalTargets.length > 0 ? approvalTargets : [selectedJobCard];
      for (const t of targets) {
        await api.post(`/supervisor/jobcards/${t.id}/approve`, request);
      }

      toast.success(`Job card${targets.length > 1 ? 's' : ''} ${approvalAction.toLowerCase()}d successfully`);
      setApprovalModalOpen(false);
      setSelectedJobCard(null);
      setApprovalRemarks('');
      const approvedIds = new Set(targets.map(t => t.id));
      // Optimistic UI: if viewing PENDING, remove the approved items immediately
      if (selectedApprovalStatus === 'PENDING') {
        setJobCards(prev => prev.filter(jc => !approvedIds.has(jc.id)));
      }
      setApprovalTargets([]);
      fetchJobCards();
    } catch (error: any) {
      console.error('Failed to approve/reject job card:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to process approval';
      toast.error(errorMessage);
    } finally {
      setApproving(false);
    }
  };

  const getEfficiencyModuleBadge = (module: string) => {
    const colors: Record<string, string> = {
      TIME_BASED: 'bg-blue-100 text-blue-800',
      QUANTITY_BASED: 'bg-green-100 text-green-800',
      TASK_BASED: 'bg-purple-100 text-purple-800',
      UNKNOWN: 'bg-gray-100 text-gray-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[module] || colors.UNKNOWN}`}>
        {module.replace(/_/g, ' ')}
      </span>
    );
  };

  const handleDownloadReport = () => {
    if (!selectedJobCard) {
      toast.error('No job card selected to download');
      return;
    }

    const jc = selectedJobCard;
    const entries = groupEntries.length > 0 ? groupEntries : [jc];
    const isTimeBased = jc.efficiency_module === 'TIME_BASED';
    const isQuantityBased = jc.efficiency_module === 'QUANTITY_BASED';
    const reportWindow = window.open('', '_blank', 'width=1200,height=800');
    if (!reportWindow) return;

    const doc = reportWindow.document;
    const entryDate = new Date(jc.entry_date).toLocaleDateString();

    const rowsHtml = entries
      .map(
        (entry) => {
          const timeTakenCell = (isTimeBased || isQuantityBased) ? `<td>${entry.actual_hours}</td>` : '';

          return `
            <tr>
              <td>${entry.activity_code || ''}</td>
              <td class="left">${entry.activity_desc}</td>
              <td>${entry.wo_number}</td>
              <td>${entry.machine_code}</td>
              <td>${entry.qty}</td>
              ${timeTakenCell}
            </tr>`;
        }
      )
      .join('');

    const hasAnyFlags = entries.some((e) => e.has_flags);

    doc.write(`
      <html>
        <head>
          <title>Production Report - Job Card #${jc.id}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 24px; }
            h2 { text-align: center; margin-bottom: 16px; }
            table { border-collapse: collapse; width: 100%; font-size: 12px; }
            th, td { border: 1px solid #000; padding: 4px 6px; text-align: center; }
            th { background-color: #f3f3f3; }
            .section-header { background-color: #e5e5e5; font-weight: bold; text-align: left; }
            .left { text-align: left; }
          </style>
        </head>
        <body>
          <h2>PRODUCTION REPORT</h2>

          <table>
            <tr>
              <th class="left">NAME</th>
              <td class="left">${jc.employee_name || 'Unknown'}</td>
              <th class="left">DATE</th>
              <td class="left">${entryDate}</td>
            </tr>
            <tr>
              <th class="left">SHIFT</th>
              <td class="left">${jc.shift || ''}</td>
              <th class="left">JOB CARD</th>
              <td class="left">#${jc.id}</td>
            </tr>
            <tr>
              <th class="left">EFFICIENCY MODULE</th>
              <td class="left" colspan="3">${jc.efficiency_module.replace(/_/g, ' ')}</td>
            </tr>
          </table>

          <br />

          <table>
            <tr>
              <th>ACTIVITY CODE</th>
              <th>ACTIVITY DESCRIPTION</th>
              <th>WORK ORDER</th>
              <th>MACHINE</th>
              <th>QTY</th>
              ${(isTimeBased || isQuantityBased) ? '<th>TIME TAKEN</th>' : ''}
            </tr>
            ${rowsHtml}
          </table>
        </body>
      </html>
    `);

    doc.close();
    reportWindow.focus();
    reportWindow.print();
  };

  const getApprovalStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Job Card Review</h1>
          <p className="text-secondary-600 mt-1">Review and approve/reject job cards submitted by operators</p>
        </div>
        <button
          onClick={fetchJobCards}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-md hover:bg-secondary-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Filter className="w-5 h-5 text-secondary-600" />
          <h2 className="text-lg font-semibold text-secondary-900">Filters</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">
              Efficiency Module
            </label>
            <div className="px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-800 text-sm">
              {supervisorModule ? supervisorModule.replace(/_/g, ' ') : 'All Modules'}
            </div>
          </div>

          <div>
            <label htmlFor="approval_status" className="block text-sm font-medium text-secondary-700 mb-1">
              Approval Status
            </label>
            <select
              id="approval_status"
              value={selectedApprovalStatus}
              onChange={(e) => setSelectedApprovalStatus(e.target.value)}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="ALL">All</option>
              <option value="PENDING">Pending Review</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Job Cards Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : jobCards.length === 0 ? (
          <div className="text-center py-12 text-secondary-500">
            <FileText className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
            <p className="text-lg font-medium">
              No job cards found
            </p>
            <p className="text-sm mt-2">
              No job cards match the selected filters
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-secondary-200">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Job Card ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Employee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Module
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {jobCards.map((jobCard) => (
                    <tr key={jobCard.id} className="hover:bg-secondary-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-secondary-900">
                        #{jobCard.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        <div>
                          <p className="font-medium">{jobCard.employee_name || 'Unknown'}</p>
                          <p className="text-secondary-500">{jobCard.employee_ec_number}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {getEfficiencyModuleBadge(jobCard.efficiency_module)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {getApprovalStatusBadge(jobCard.approval_status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {jobCard.approval_status === 'PENDING' ? (
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleViewDetails(jobCard)}
                              className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md hover:bg-blue-200 transition-colors"
                            >
                              <Eye className="w-3 h-3" />
                              <span>View</span>
                            </button>
                            <button
                              onClick={() => handleApprovalClick(jobCard, 'APPROVE')}
                              className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-md hover:bg-green-200 transition-colors"
                            >
                              <Check className="w-3 h-3" />
                              <span>Approve</span>
                            </button>
                            <button
                              onClick={() => handleApprovalClick(jobCard, 'REJECT')}
                              className="flex items-center space-x-1 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-md hover:bg-red-200 transition-colors"
                            >
                              <X className="w-3 h-3" />
                              <span>Reject</span>
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleViewDetails(jobCard)}
                            className="flex items-center space-x-1 px-2 py-1 bg-secondary-100 text-secondary-700 text-xs rounded-md hover:bg-secondary-200 transition-colors"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Summary Footer removed as requested */}
          </>
        )}
      </div>

      {/* Job Card Details Modal */}
      <Transition appear show={detailsModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setDetailsModalOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-lg bg-white p-6 shadow-xl transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <Dialog.Title className="text-lg font-semibold text-secondary-900">
                        Production Report
                      </Dialog.Title>
                      <p className="text-sm text-secondary-600 mt-1">Job Card #{selectedJobCard?.id}</p>
                    </div>
                    <button
                      onClick={() => setDetailsModalOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>

                  {selectedJobCard && (
                    <div className="space-y-6">
                      <div className="border border-secondary-400 rounded-lg overflow-hidden">
                        {/* Title Row */}
                        <div className="border-b border-secondary-400 py-2 text-center text-sm font-semibold tracking-wide">
                          PRODUCTION REPORT
                        </div>

                        {/* Header Info Table */}
                        <table className="w-full text-[11px]">
                          <tbody>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">NAME</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {selectedJobCard.employee_name || 'Unknown'}
                              </td>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">DATE</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {new Date(selectedJobCard.entry_date).toLocaleDateString()}
                              </td>
                            </tr>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">SHIFT</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">{selectedJobCard.shift}</td>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">JOB CARD</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">#{selectedJobCard.id}</td>
                            </tr>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">EFFICIENCY MODULE</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left" colSpan={3}>
                                {selectedJobCard.efficiency_module.replace(/_/g, ' ')}
                              </td>
                            </tr>
                          </tbody>
                        </table>

                        {/* Activity Row Table */}
                        <table className="w-full text-[11px] mt-2">
                          <thead>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">ACTIVITY CODE</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">ACTIVITY DESCRIPTION</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">WORK ORDER</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">MACHINE</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">QTY</th>
                              {(selectedJobCard.efficiency_module === 'TIME_BASED' || selectedJobCard.efficiency_module === 'QUANTITY_BASED') && (
                                <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">TIME TAKEN</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            <tr key={selectedJobCard.id}>
                              <td className="border border-secondary-400 px-2 py-1 text-center">
                                {selectedJobCard.activity_code || ''}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {selectedJobCard.activity_desc}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-center">
                                {selectedJobCard.wo_number}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-center">
                                {selectedJobCard.machine_code}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-center">{selectedJobCard.qty}</td>
                              {(selectedJobCard.efficiency_module === 'TIME_BASED' || selectedJobCard.efficiency_module === 'QUANTITY_BASED') && (
                                <td className="border border-secondary-400 px-2 py-1 text-center">
                                  {selectedJobCard.actual_hours}
                                </td>
                              )}
                            </tr>
                          </tbody>
                        </table>
                      </div>

                      <div className="flex justify-end">
                        <button
                          type="button"
                          onClick={handleDownloadReport}
                          className="mt-3 inline-flex items-center space-x-2 px-4 py-2 bg-secondary-900 text-white text-sm font-medium rounded-md hover:bg-secondary-800"
                        >
                          <FileText className="w-4 h-4" />
                          <span>Download Report</span>
                        </button>
                      </div>
                    </div>
                  )}
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>

      {/* Approval Modal */}
      <Transition appear show={approvalModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setApprovalModalOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-white p-6 shadow-xl transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <Dialog.Title className="text-lg font-semibold text-secondary-900">
                        {approvalAction === 'APPROVE' ? 'Approve' : 'Reject'} Job Card
                      </Dialog.Title>
                      <p className="text-sm text-secondary-600 mt-1">
                        Job Card #{selectedJobCard?.id}
                      </p>
                    </div>
                    <button
                      onClick={() => setApprovalModalOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label
                        htmlFor="approval_remarks"
                        className="block text-sm font-medium text-secondary-700 mb-1"
                      >
                        Remarks
                      </label>
                      <textarea
                        id="approval_remarks"
                        rows={4}
                        value={approvalRemarks}
                        onChange={(e) => setApprovalRemarks(e.target.value)}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder={`Provide remarks for ${approvalAction.toLowerCase()}ing this job card...`}
                      />
                    </div>

                    <div className="flex items-center justify-end space-x-3 pt-4 border-t border-secondary-200">
                      <button
                        type="button"
                        onClick={() => setApprovalModalOpen(false)}
                        className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleApproval}
                        disabled={approving}
                        className={`flex items-center space-x-2 px-4 py-2 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                          approvalAction === 'APPROVE'
                            ? 'bg-green-600 hover:bg-green-700'
                            : 'bg-red-600 hover:bg-red-700'
                        }`}
                      >
                        {approvalAction === 'APPROVE' ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                        <span>{approving ? 'Processing...' : approvalAction}</span>
                      </button>
                    </div>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  );
};

export default ValidationPanel;
