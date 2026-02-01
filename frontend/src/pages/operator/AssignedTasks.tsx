import { useEffect, useState, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Dialog, Transition } from '@headlessui/react';
import { Eye, XCircle, FileText, Edit3 } from 'lucide-react';

interface AssignedTaskItem {
  id: number;
  work_order_id: number;
  wo_number?: string;
  machine_id: number;
  machine_code?: string;
  activity_code_id?: number | null;
  activity_code?: string | null;
  activity_desc: string;
  qty: number;
  actual_hours: number;
  status: string;
  entry_date: string;
  efficiency_module?: string;
  shift?: number;
  approval_status?: string | null;
  has_flags?: boolean;
  supervisor_remarks?: string | null;
}

const AssignedTasks = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState<AssignedTaskItem[]>([]);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [selected, setSelected] = useState<AssignedTaskItem | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      // Only supervisor-assigned for current operator; backend auto-scopes by current user
      const res = await api.get('/jobcards', {
        params: {
          source: 'SUPERVISOR',
          status: 'IC',
        },
      });
      const data: AssignedTaskItem[] = res.data || [];
      setTasks(data);
    } catch (err: any) {
      console.error('Failed to load assigned tasks:', err);
      toast.error('Failed to load assigned tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleEdit = (task: AssignedTaskItem) => {
    setSelected(task);
    setEditOpen(true);
  };

  const handleView = (task: AssignedTaskItem) => {
    setSelected(task);
    setDetailsOpen(true);
  };

  const handleDownloadReport = () => {
    if (!selected) return;

    const reportWindow = window.open('', '_blank', 'width=1200,height=800');
    if (!reportWindow) return;

    const doc = reportWindow.document;
    const entryDate = new Date(selected.entry_date).toLocaleDateString();
    const efficiencyModule = (selected.efficiency_module || '').replace(/_/g, ' ');
    const isTimeBased = selected.efficiency_module === 'TIME_BASED';
    const isQuantityBased = selected.efficiency_module === 'QUANTITY_BASED';

    const timeTakenCell = (isTimeBased || isQuantityBased) ? `<td>${selected.actual_hours}</td>` : '';

    doc.write(`
      <html>
        <head>
          <title>Production Report - Job Card #${selected.id}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 24px; }
            h2 { text-align: center; margin-bottom: 16px; }
            table { border-collapse: collapse; width: 100%; font-size: 12px; }
            th, td { border: 1px solid #000; padding: 4px 6px; text-align: center; }
            th { background-color: #f3f3f3; }
            .left { text-align: left; }
          </style>
        </head>
        <body>
          <h2>PRODUCTION REPORT</h2>
          <table>
            <tr>
              <th class="left">NAME</th>
              <td class="left">${user?.name || 'Unknown'}</td>
              <th class="left">DATE</th>
              <td class="left">${entryDate}</td>
            </tr>
            <tr>
              <th class="left">SHIFT</th>
              <td class="left">${selected.shift ?? ''}</td>
              <th class="left">JOB CARD</th>
              <td class="left">#${selected.id}</td>
            </tr>
            <tr>
              <th class="left">EFFICIENCY MODULE</th>
              <td class="left" colspan="3">${efficiencyModule}</td>
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
            <tr>
              <td>${selected.activity_code || ''}</td>
              <td class="left">${selected.activity_desc}</td>
              <td>${selected.wo_number || selected.work_order_id}</td>
              <td>${selected.machine_code || selected.machine_id}</td>
              <td>${selected.qty}</td>
              ${timeTakenCell}
            </tr>
          </table>
        </body>
      </html>
    `);

    doc.close();
    reportWindow.focus();
    reportWindow.print();
  };

  const handleSubmit = async (id: number) => {
    try {
      await api.patch(`/jobcards/${id}`, { status: 'C' });
      toast.success('Task submitted');
      fetchTasks();
    } catch (err: any) {
      console.error('Submit failed:', err);
      toast.error(err.response?.data?.detail || 'Failed to submit task');
    }
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
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Assigned Tasks</h1>
        <p className="text-secondary-600 mt-1">Tasks assigned by your supervisor</p>
      </div>

      {tasks.length === 0 ? (
        <div className="text-center py-12 text-secondary-500 bg-white rounded-lg shadow">
          <p className="text-lg font-medium">No assigned tasks</p>
          <p className="text-sm mt-2">Tasks assigned to you will appear here.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary-200">
              <thead className="bg-secondary-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">WO</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">Machine</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">Activity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">Qty</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">Hours</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">Approval</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-secondary-700 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-secondary-200">
                {tasks.map((t) => (
                  <tr key={t.id} className="hover:bg-secondary-50">
                    <td className="px-6 py-4 whitespace-nowrap">{t.wo_number || t.work_order_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{t.machine_code || t.machine_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{t.activity_code || t.activity_desc}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{t.qty}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{t.actual_hours}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{(t.entry_date || '').toString().slice(0, 10)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        t.approval_status === 'APPROVED'
                          ? 'bg-green-100 text-green-800'
                          : t.approval_status === 'REJECTED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {t.approval_status || 'PENDING'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => handleView(t)}
                          className="px-3 py-1.5 rounded-md border border-secondary-300 text-secondary-700 hover:bg-secondary-50 flex items-center gap-1"
                        >
                          <Eye className="w-4 h-4" /> View
                        </button>
                        <button
                          onClick={() => handleEdit(t)}
                          className="px-3 py-1.5 rounded-md border border-secondary-300 text-secondary-700 hover:bg-secondary-50"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleSubmit(t.id)}
                          disabled={t.approval_status === 'APPROVED'}
                          className="px-3 py-1.5 rounded-md bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Submit
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Details Modal */}
      <Transition appear show={detailsOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setDetailsOpen(false)}>
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
                <Dialog.Panel className="w-full max-w-3xl transform overflow-hidden rounded-lg bg-white p-6 shadow-xl transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <Dialog.Title className="text-lg font-semibold text-secondary-900">
                        Production Report
                      </Dialog.Title>
                      <p className="text-sm text-secondary-600 mt-1">Job Card #{selected?.id}</p>
                    </div>
                    <button onClick={() => setDetailsOpen(false)} className="text-secondary-400 hover:text-secondary-600">
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>

                  {selected && (
                    <div className="space-y-6">
                      <div className="border border-secondary-400 rounded-lg overflow-hidden">
                        <div className="border-b border-secondary-400 py-2 text-center text-sm font-semibold tracking-wide">
                          PRODUCTION REPORT
                        </div>

                        <table className="w-full text-[11px]">
                          <tbody>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">NAME</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {user?.name || 'Unknown'}
                              </td>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">DATE</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {new Date(selected.entry_date).toLocaleDateString()}
                              </td>
                            </tr>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">SHIFT</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {selected.shift ?? ''}
                              </td>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">JOB CARD</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left">#{selected.id}</td>
                            </tr>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold">EFFICIENCY MODULE</th>
                              <td className="border border-secondary-400 px-2 py-1 text-left" colSpan={3}>
                                {(selected.efficiency_module || '').replace(/_/g, ' ')}
                              </td>
                            </tr>
                          </tbody>
                        </table>

                        <table className="w-full text-[11px] mt-2">
                          <thead>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">ACTIVITY CODE</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">ACTIVITY DESCRIPTION</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">WORK ORDER</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">MACHINE</th>
                              <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">QTY</th>
                              {(selected.efficiency_module === 'TIME_BASED' || selected.efficiency_module === 'QUANTITY_BASED') && (
                                <th className="border border-secondary-400 px-2 py-1 text-center font-semibold">TIME TAKEN</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td className="border border-secondary-400 px-2 py-1 text-center">
                                {selected.activity_code || ''}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-left">
                                {selected.activity_desc}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-center">
                                {selected.wo_number || selected.work_order_id}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-center">
                                {selected.machine_code || selected.machine_id}
                              </td>
                              <td className="border border-secondary-400 px-2 py-1 text-center">{selected.qty}</td>
                              {(selected.efficiency_module === 'TIME_BASED' || selected.efficiency_module === 'QUANTITY_BASED') && (
                                <td className="border border-secondary-400 px-2 py-1 text-center">
                                  {selected.actual_hours}
                                </td>
                              )}
                            </tr>
                          </tbody>
                        </table>

                        <table className="w-full text-[11px] mt-2">
                          <tbody>
                            <tr>
                              <th className="border border-secondary-400 px-2 py-1 text-left font-semibold" colSpan={2}>
                                SUPERVISOR REMARKS
                              </th>
                            </tr>
                            <tr>
                              <td className="border border-secondary-400 px-2 py-1 text-left" colSpan={2}>
                                {selected.supervisor_remarks || '-'}
                              </td>
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

      {/* Edit Modal */}
      <Transition appear show={editOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setEditOpen(false)}>
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
                        Edit Job Card
                      </Dialog.Title>
                      <p className="text-sm text-secondary-600 mt-1">Job Card #{selected?.id}</p>
                    </div>
                    <button
                      onClick={() => setEditOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                  </div>

                  {selected && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-secondary-900 mb-1">
                            Work Order
                          </label>
                          <input
                            type="text"
                            value={selected.wo_number || ''}
                            disabled
                            className="w-full px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-700"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-secondary-900 mb-1">
                            Machine
                          </label>
                          <input
                            type="text"
                            value={selected.machine_code || ''}
                            disabled
                            className="w-full px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-700"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-secondary-900 mb-1">
                          Activity Description
                        </label>
                        <input
                          type="text"
                          value={selected.activity_desc || ''}
                          disabled
                          className="w-full px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-700"
                        />
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-secondary-900 mb-1">
                            Quantity
                          </label>
                          <input
                            type="number"
                            defaultValue={selected.qty}
                            className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-secondary-900 mb-1">
                            Hours
                          </label>
                          <input
                            type="number"
                            defaultValue={selected.actual_hours}
                            className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-secondary-900 mb-1">
                            Shift
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="3"
                            defaultValue={selected.shift || 1}
                            className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500"
                          />
                        </div>
                      </div>

                      {selected.supervisor_remarks && (
                        <div>
                          <label className="block text-sm font-medium text-secondary-900 mb-1">
                            Supervisor Remarks
                          </label>
                          <div className="w-full px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-700 text-sm">
                            {selected.supervisor_remarks}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-end space-x-3 pt-4 border-t border-secondary-200">
                        <button
                          onClick={() => setEditOpen(false)}
                          className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => {
                            // Navigate to edit page only when user confirms
                            navigate(`/operator/jobcards/${selected.id}/edit`);
                          }}
                          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
                        >
                          <Edit3 className="w-4 h-4" />
                          <span>Edit in Full Form</span>
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
    </div>
  );
};

export default AssignedTasks;
