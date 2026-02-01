import { useEffect, useState, Fragment } from 'react';
import { Link } from 'react-router-dom';
import { Dialog, Transition } from '@headlessui/react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { JobCard } from '../../types';
import { Plus, Filter, RefreshCw, AlertCircle, Edit3, XCircle, Eye, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

const JobCardList = () => {
  const { user } = useAuth();
  const [jobCards, setJobCards] = useState<JobCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedJobCard, setSelectedJobCard] = useState<JobCard | null>(null);
  const [reportEntries, setReportEntries] = useState<JobCard[]>([]);
  const [remarksModalOpen, setRemarksModalOpen] = useState(false);

  type JobCardGroup = {
    key: string;
    representative: JobCard;
    entries: JobCard[];
    totalQty: number;
    totalHours: number;
    isExpanded: boolean;
  };

  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // Group job cards by entry_date and source (submission batch)
  const groupJobCards = (cards: JobCard[]): JobCardGroup[] => {
    const grouped = new Map<string, JobCard[]>();
    
    cards.forEach((card) => {
      const key = `${card.entry_date}_${card.source}`;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(card);
    });

    return Array.from(grouped.entries()).map(([key, entries]) => ({
      key,
      representative: entries[0],
      entries: entries.sort((a, b) => a.id - b.id),
      totalQty: entries.reduce((sum, e) => sum + e.qty, 0),
      totalHours: entries.reduce((sum, e) => sum + e.actual_hours, 0),
      isExpanded: expandedGroups.has(key),
    }));
  };

  const toggleGroupExpanded = (key: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedGroups(newExpanded);
  };

  useEffect(() => {
    // No date range by default to show all job cards
  }, []);

  useEffect(() => {
    fetchJobCards();
  }, [user]);

  const fetchJobCards = async () => {
    if (!user?.id) return;

    setLoading(true);
    try {
      const response = await api.get('/jobcards', {
        params: {
          employee_id: user.id,
          source: 'TECHNICIAN',
        },
      });
      console.log('Job cards API response:', response.data);
      setJobCards(response.data);
      console.log('jobCards state after set:', response.data?.length, response.data);
    } catch (error) {
      console.error('Failed to fetch job cards:', error);
      toast.error('Failed to load job cards');
    } finally {
      setLoading(false);
    }
  };

  const getApprovalStatusBadge = (status?: string) => {
    if (!status || status === 'PENDING') {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
          Pending Review
        </span>
      );
    } else if (status === 'APPROVED') {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
          Approved
        </span>
      );
    } else if (status === 'REJECTED') {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
          Rejected
        </span>
      );
    } else if (status === 'MIXED') {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-secondary-100 text-secondary-800">
          Mixed
        </span>
      );
    }
    return null;
  };

  const getSubmissionStatusBadge = () => (
    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
      Pending Submission
    </span>
  );

  const handleViewRemarks = (jobCard: JobCard) => {
    setSelectedJobCard(jobCard);
    // Load all entries in the same submission group
    const key = `${jobCard.entry_date}_${jobCard.source}`;
    const grouped = groupJobCards(jobCards);
    const group = grouped.find(g => g.key === key);
    if (group) {
      setReportEntries(group.entries);
    } else {
      setReportEntries([]);
    }
    setRemarksModalOpen(true);
  };

  const handleDownloadReport = () => {
    if (!selectedJobCard) {
      toast.error('No job card selected to download');
      return;
    }

    const jc = selectedJobCard;
    const entries = reportEntries.length > 0 ? reportEntries : [jc];
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
              <td>${entry.wo_number || ''}</td>
              <td>${entry.machine_code || ''}</td>
              <td>${entry.qty}</td>
              ${timeTakenCell}
            </tr>`;
        }
      )
      .join('');

    const timeTakenHeader = (isTimeBased || isQuantityBased) 
      ? '<th class="center">TIME TAKEN</th>' 
      : '';

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Production Report - Job Card #${jc.id}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
          th, td { border: 1px solid #000; padding: 8px; text-align: center; }
          th { background-color: #f0f0f0; font-weight: bold; }
          .left { text-align: left; }
          .center { text-align: center; }
          .title { text-align: center; font-weight: bold; margin-bottom: 20px; }
          @media print { body { margin: 0; } }
        </style>
      </head>
      <body>
        <div class="title">PRODUCTION REPORT</div>
        <table>
          <tr>
            <th>NAME</th>
            <td>${user?.name || 'Unknown'}</td>
            <th>DATE</th>
            <td>${entryDate}</td>
          </tr>
          <tr>
            <th>SHIFT</th>
            <td>${jc.shift || ''}</td>
            <th>JOB CARD</th>
            <td>#${jc.id}</td>
          </tr>
          <tr>
            <th>EFFICIENCY MODULE</th>
            <td colspan="3">${jc.efficiency_module?.replace(/_/g, ' ') || ''}</td>
          </tr>
        </table>
        <table>
          <thead>
            <tr>
              <th class="center">ACTIVITY CODE</th>
              <th class="center">ACTIVITY DESCRIPTION</th>
              <th class="center">WORK ORDER</th>
              <th class="center">MACHINE</th>
              <th class="center">QTY</th>
              ${timeTakenHeader}
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
        <table>
          <tr>
            <th>SUPERVISOR REMARKS</th>
          </tr>
          <tr>
            <td>${jc.supervisor_remarks || '-'}</td>
          </tr>
        </table>
      </body>
      </html>
    `;

    doc.write(html);
    doc.close();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Job Cards</h1>
          <p className="text-secondary-600 mt-1">View and manage your job cards</p>
        </div>
        <Link
          to="/operator/jobcards/new"
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
        >
          
          <Plus className="w-5 h-5" />
          <span>New Job Card</span>
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center space-x-2 mb-4">
          <Filter className="w-5 h-5 text-secondary-600" />
          <h2 className="text-lg font-semibold text-secondary-900">Filters</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="start_date" className="block text-sm font-medium text-secondary-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              id="start_date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label htmlFor="end_date" className="block text-sm font-medium text-secondary-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              id="end_date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchJobCards}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-md hover:bg-secondary-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
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
            <AlertCircle className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
            <p className="text-lg font-medium">No job cards found</p>
            <p className="text-sm mt-2">Try adjusting your filters or create a new job card</p>
            <Link
              to="/operator/jobcards/new"
              className="inline-block mt-4 text-primary-600 hover:text-primary-700"
            >
              Create Job Card →
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-secondary-200">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Work Order
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Activity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Efficiency Module
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Quantity Produced
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Hours
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Approval Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {groupJobCards(jobCards).map((group) => (
                    <Fragment key={group.key}>
                      {/* Group Header Row */}
                      <tr 
                        onClick={() => toggleGroupExpanded(group.key)}
                        className="hover:bg-secondary-100 transition-colors cursor-pointer bg-secondary-50 font-semibold"
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                          <div className="flex items-center space-x-2">
                            <span className={`inline-block transform transition-transform ${group.isExpanded ? 'rotate-90' : ''}`}>
                              ▶
                            </span>
                            <span>{new Date(group.representative.entry_date).toLocaleDateString()}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                          <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                            {group.entries.length} {group.entries.length === 1 ? 'entry' : 'entries'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-secondary-900">
                          <span className="text-xs text-secondary-600">{group.representative.source}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                          {group.representative.efficiency_module ? group.representative.efficiency_module.replace(/_/g, ' ') : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-secondary-900">
                          {group.totalQty}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-secondary-900">
                          {group.totalHours.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {getApprovalStatusBadge(group.representative.approval_status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewRemarks(group.representative);
                            }}
                            className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md hover:bg-blue-200 transition-colors"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View Group</span>
                          </button>
                        </td>
                      </tr>

                      {/* Expanded Entries */}
                      {group.isExpanded && group.entries.map((job, idx) => (
                        <tr key={job.id} className="hover:bg-secondary-50 transition-colors bg-white">
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-secondary-700 pl-12">
                            Entry {idx + 1}
                          </td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-secondary-900">
                            WO-{job.work_order_id}
                          </td>
                          <td className="px-6 py-3 text-sm text-secondary-900">
                            <div className="max-w-xs">
                              <p className="font-medium">{job.activity_desc}</p>
                              {job.activity_code && (
                                <p className="text-xs text-secondary-500">Code: {job.activity_code}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-secondary-900">
                            {job.efficiency_module ? job.efficiency_module.replace(/_/g, ' ') : '-'}
                          </td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-secondary-900">
                            {job.qty}
                          </td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm text-secondary-900">
                            {job.actual_hours}
                          </td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm">
                            {getApprovalStatusBadge(job.approval_status)}
                          </td>
                          <td className="px-6 py-3 whitespace-nowrap text-sm">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => handleViewRemarks(job)}
                                className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md hover:bg-blue-200 transition-colors"
                              >
                                <Eye className="w-3 h-3" />
                                <span>View</span>
                              </button>
                              {(job.approval_status === 'REJECTED' || (job.source === 'SUPERVISOR' && job.status === 'IC')) && (
                                <Link
                                  to={`/operator/jobcards/${job.id}/edit`}
                                  className="flex items-center space-x-1 px-2 py-1 bg-secondary-100 text-secondary-700 text-xs rounded-md hover:bg-secondary-200 transition-colors"
                                >
                                  <Edit3 className="w-3 h-3" />
                                  <span>Edit</span>
                                </Link>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Summary Footer */}
            <div className="bg-secondary-50 px-6 py-4 border-t border-secondary-200">
              <div className="flex items-center justify-between text-sm text-secondary-700">
                <span>
                  Total: <strong>{jobCards.length}</strong> job card {jobCards.length === 1 ? 'entry' : 'entries'} in <strong>{groupJobCards(jobCards).length}</strong> submission{groupJobCards(jobCards).length === 1 ? '' : 's'}
                </span>
                <span>
                  Total Quantity:{' '}
                  <strong>
                    {jobCards.reduce((sum, job) => sum + job.qty, 0).toFixed(2)}
                  </strong>
                </span>
                <span>
                  Total Hours:{' '}
                  <strong>
                    {jobCards.reduce((sum, job) => sum + job.actual_hours, 0).toFixed(2)}
                  </strong>
                </span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Job Card Details / Production Report Modal */}
      <Transition appear show={remarksModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setRemarksModalOpen(false)}>
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
                      onClick={() => setRemarksModalOpen(false)}
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
                                {user?.name || 'Unknown'}
                              </td>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">DATE</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {new Date(selectedJobCard.entry_date).toLocaleDateString()}
                              </td>
                            </tr>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">SHIFT</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {selectedJobCard.shift ?? ''}
                              </td>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">JOB CARD</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">#{selectedJobCard.id}</td>
                            </tr>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">EFFICIENCY MODULE</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left" colSpan={3}>
                                {(selectedJobCard.efficiency_module || '').replace(/_/g, ' ')}
                              </td>
                            </tr>
                          </tbody>
                        </table>

                        {/* Activity Rows Table - aligned with supervisor view */}
                        <table className="w-full text-[11px] mt-2">
                          <thead>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">ACTIVITY CODE</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">ACTIVITY DESCRIPTION</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">WORK ORDER</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">MACHINE</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">{selectedJobCard.efficiency_module === 'QUANTITY_BASED' ? 'Quantity Produced' : 'QTY'}</th>
                              {selectedJobCard.efficiency_module === 'TIME_BASED' && (
                                <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">TIME TAKEN</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {(reportEntries.length > 0 ? reportEntries : [selectedJobCard]).map((entry) => (
                              <tr key={entry.id}>
                                <td className="border border-secondary-400 px-2 py-1 text-center">
                                  {entry.activity_code || ''}
                                </td>
                                <td className="border border-secondary-400 px-2 py-1 text-left">
                                  {entry.activity_desc}
                                </td>
                                <td className="border border-secondary-400 px-2 py-1 text-center">
                                  {entry.wo_number || ''}
                                </td>
                                <td className="border border-secondary-400 px-2 py-1 text-center">
                                  {entry.machine_code || ''}
                                </td>
                                <td className="border border-secondary-400 px-2 py-1 text-center">{entry.qty}</td>
                                {selectedJobCard.efficiency_module === 'TIME_BASED' && (
                                  <td className="border border-secondary-400 px-2 py-1 text-center">
                                    {entry.actual_hours}
                                  </td>
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        {/* Supervisor Remarks only */}
                        <table className="w-full text-[11px] mt-2">
                          <tbody>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold" colSpan={2}>
                                SUPERVISOR REMARKS
                              </th>
                            </tr>
                            <tr>
                              <td className="border border-secondary-400 px-2 py-1 text-left" colSpan={2}>
                                {selectedJobCard.supervisor_remarks || '-'}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>

                      <div className="flex items-center justify-end space-x-3 pt-4 border-t border-secondary-200">
                        <button
                          type="button"
                          onClick={handleDownloadReport}
                          className="inline-flex items-center space-x-2 px-4 py-2 bg-secondary-900 text-white text-sm font-medium rounded-md hover:bg-secondary-800"
                        >
                          <FileText className="w-4 h-4" />
                          <span>Download Report</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setRemarksModalOpen(false)}
                          className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
                        >
                          Close
                        </button>
                        {selectedJobCard.approval_status === 'REJECTED' && (
                          <Link
                            to={`/operator/jobcards/${selectedJobCard.id}/edit`}
                            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                          >
                            <Edit3 className="w-4 h-4" />
                            <span>Edit Job Card</span>
                          </Link>
                        )}
                      </div>
                    </div>
                  )}
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  );
};

export default JobCardList;
