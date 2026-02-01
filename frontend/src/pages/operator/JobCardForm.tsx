import { useEffect, useState } from 'react';
import { useForm, useFieldArray, Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Machine, WorkOrder, ActivityCode, JobCardStatusEnum, CreateJobCardRequest } from '../../types';
import { ArrowLeft, Save } from 'lucide-react';

const jobCardEntrySchema = z.object({
  work_order_id: z
    .preprocess((val) => {
      if (val === '' || val === undefined || val === null) return undefined;
      const n = typeof val === 'string' ? Number(val) : (val as number);
      return Number.isNaN(n) ? undefined : n;
    }, z.number().optional()),
  machine_id: z
    .preprocess((val) => {
      if (val === '' || val === undefined || val === null) return undefined;
      const n = typeof val === 'string' ? Number(val) : (val as number);
      return Number.isNaN(n) ? undefined : n;
    }, z.number().optional()),
  activity_code_id: z
    .preprocess((val) => {
      if (val === '' || val === undefined || val === null) return null;
      const n = typeof val === 'string' ? Number(val) : (val as number);
      return Number.isNaN(n) ? null : n;
    }, z.number().int().nullable().optional()),
  activity_desc: z.string().optional(),
  qty: z
    .preprocess((val) => {
      if (val === '' || val === undefined || val === null) return undefined;
      const n = typeof val === 'string' ? Number(val) : (val as number);
      return Number.isNaN(n) ? undefined : n;
    }, z.number().optional()),
  actual_hours: z
    .preprocess((val) => {
      if (val === '' || val === undefined || val === null) return undefined;
      const n = typeof val === 'string' ? Number(val) : (val as number);
      return Number.isNaN(n) ? undefined : n;
    }, z.number().optional()),
  status: z.nativeEnum(JobCardStatusEnum).optional(),
});

const jobCardSchema = z.object({
  entry_date: z.string({ required_error: 'Date is required' }),
  efficiency_module: z.enum(['TIME_BASED', 'QUANTITY_BASED', 'TASK_BASED'], {
    required_error: 'Efficiency module is required',
  }),
  is_awc: z.boolean(),
  shift: z.number().min(1).max(3).optional(),
  entries: z
    .array(jobCardEntrySchema)
    .min(1, { message: 'At least one entry is required' }),
});

type JobCardFormData = z.infer<typeof jobCardSchema>;

const JobCardForm = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = !!id;
  const [machines, setMachines] = useState<Machine[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [activityCodes, setActivityCodes] = useState<ActivityCode[]>([]);
  const [loading, setLoading] = useState(false);
  const [existingJobCard, setExistingJobCard] = useState<any>(null);
  const [groupEditIds, setGroupEditIds] = useState<number[]>([]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<JobCardFormData>({
    resolver: zodResolver(jobCardSchema) as Resolver<JobCardFormData>,
    defaultValues: {
      entry_date: new Date().toISOString().split('T')[0],
      is_awc: false,
      efficiency_module: 'TIME_BASED',
      shift: 1,
      entries: [
        {
          work_order_id: undefined,
          machine_id: undefined,
          activity_code_id: null,
          activity_desc: '',
          qty: undefined,
          actual_hours: undefined,
          status: JobCardStatusEnum.C,
        },
      ],
    } as JobCardFormData,
  });

  const isAWC = watch('is_awc');
  const selectedEfficiencyModule = watch('efficiency_module');
  const isOperator = user?.role === 'OPERATOR';
  const operatorModule = isOperator ? user?.supervisor_efficiency_module ?? null : null;

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'entries',
  });

  const effectiveModuleForFilter = operatorModule || selectedEfficiencyModule;
  const filteredActivityCodes = activityCodes.filter(
    (ac) => ac.efficiency_type === effectiveModuleForFilter
  );

  // Filter machines and work orders for operators based on supervisor efficiency module
  const filteredMachines = isOperator && operatorModule
    ? machines // Machines do not have efficiency_type; keep all for now
    : machines;

  const filteredWorkOrders = isOperator && operatorModule
    ? workOrders // WorkOrders do not have efficiency_type; keep all for now
    : workOrders;

  useEffect(() => {
    fetchFormData();
    if (isEditing && id) {
      fetchExistingJobCard(id);
    }
  }, []);

  useEffect(() => {
    if (isEditing) return;
    if (operatorModule) {
      setValue('efficiency_module', operatorModule as JobCardFormData['efficiency_module']);
    }
  }, [operatorModule, isEditing, setValue]);

  useEffect(() => {
    // Skip auto-resets and clearing behavior while editing an existing job card
    if (isEditing) return;

    // Automatically set AWC for TASK_BASED module (create mode only)
    const targetModule = operatorModule || selectedEfficiencyModule;
    if (targetModule === 'TASK_BASED') {
      setValue('is_awc', true);
    } else if (targetModule === 'TIME_BASED' || targetModule === 'QUANTITY_BASED') {
      setValue('is_awc', false);
    }

    // Clear incompatible selections when module changes (create mode only)
    const currentEntries = watch('entries');
    if (currentEntries && currentEntries.length > 0) {
      const cleared = currentEntries.map((entry) => ({
        ...entry,
        activity_code_id: null,
        activity_desc: '',
      }));
      setValue('entries', cleared, { shouldValidate: true });
    }
  }, [selectedEfficiencyModule, operatorModule, setValue, watch]);

  const fetchExistingJobCard = async (jobCardId: string) => {
    try {
      const response = await api.get(`/jobcards/${jobCardId}`);
      const jobCard = response.data;
      setExistingJobCard(jobCard);

      // Check if job card can be edited (rejected or assigned tasks pending submission)
      const isRejected = jobCard.approval_status === 'REJECTED';
      const isAssignedPending = jobCard.source === 'SUPERVISOR' && jobCard.status === 'IC';
      if (!isRejected && !isAssignedPending) {
        toast.error('Only rejected or assigned pending job cards can be edited');
        navigate('/operator/jobcards');
        return;
      }

      // Populate header fields
      setValue('entry_date', jobCard.entry_date.split('T')[0]);
      setValue('is_awc', jobCard.is_awc);

      // Preserve efficiency module exactly as stored on server; do not fall back/change during edit
      if (jobCard.efficiency_module) {
        setValue('efficiency_module', jobCard.efficiency_module);
      }

      // Set shift (default if not available)
      setValue('shift', jobCard.shift || 1);

      // Load entire group for this employee/date/shift/module
      const start = jobCard.entry_date.split('T')[0];
      const end = start;
      const listRes = await api.get('/jobcards', {
        params: {
          employee_id: jobCard.employee_id,
          start_date: start,
          end_date: end,
        },
      });

      const allForDay: any[] = listRes.data || [];
      const sameShift = (e: any) => (e.shift ?? 1) === (jobCard.shift ?? 1);
      const sameModule = (e: any) => (e.efficiency_module || (e.is_awc ? 'TASK_BASED' : undefined)) === (jobCard.efficiency_module || (jobCard.is_awc ? 'TASK_BASED' : undefined));

      const groupToEdit = allForDay.filter((e) => {
        if (!sameShift(e) || !sameModule(e)) return false;
        if (isRejected) return e.approval_status === 'REJECTED';
        return e.source === 'SUPERVISOR' && e.status === 'IC';
      });

      // Fallback to single card if no group found
      const groupToEditSafe = groupToEdit.length > 0 ? groupToEdit : [jobCard];

      // Store ids for patching on submit
      setGroupEditIds(groupToEditSafe.map((g) => g.id));

      // Populate entries for the whole group
      const mappedEntries = groupToEditSafe.map((g) => ({
        work_order_id: g.work_order_id,
        machine_id: g.machine_id,
        activity_code_id: g.activity_code_id || null,
        activity_desc: g.activity_desc,
        qty: g.qty,
        actual_hours: g.actual_hours,
        status: g.status,
      }));

      setValue('entries', mappedEntries);

    } catch (error: any) {
      console.error('Failed to fetch job card:', error);
      toast.error('Failed to load job card for editing');
      navigate('/operator/jobcards');
    }
  };

  const fetchFormData = async () => {
    try {
      const [machinesRes, workOrdersRes, activityCodesRes] = await Promise.all([
        api.get('/machines'),
        api.get('/work-orders'),
        api.get('/activity-codes'),
      ]);

      setMachines(machinesRes.data);
      setWorkOrders(workOrdersRes.data);
      setActivityCodes(activityCodesRes.data);
    } catch (error) {
      console.error('Failed to fetch form data:', error);
      toast.error('Failed to load form data');
    }
  };

  const onSubmit = async (data: JobCardFormData) => {
    console.log('Form submitted with data:', data);
    
    if (!user?.id) {
      toast.error('User not found');
      return;
    }

    setLoading(true);
    try {
      const sharedShift = data.shift || 1;
      const requiresHours = getFieldRequirements().showHours;

      if (isEditing && existingJobCard) {
        // Edit mode: patch all entries in the rejected group
        const patchPromises: Promise<any>[] = [];
        const shouldSubmitAssigned =
          existingJobCard.source === 'SUPERVISOR' && existingJobCard.status === 'IC';

        data.entries.forEach((entry, idx) => {
          const targetId = groupEditIds[idx] ?? existingJobCard.id;
          const updateData = {
            machine_id: entry.machine_id,
            work_order_id: entry.work_order_id,
            activity_code_id: data.is_awc ? null : entry.activity_code_id,
            activity_desc: data.is_awc ? entry.activity_desc : entry.activity_desc || existingJobCard.activity_desc,
            qty: entry.qty ?? 0,
            actual_hours: entry.actual_hours ?? 0,
            status: shouldSubmitAssigned ? JobCardStatusEnum.C : (entry.status || JobCardStatusEnum.C),
            entry_date: data.entry_date,
            is_awc: selectedEfficiencyModule === 'TASK_BASED',
            shift: sharedShift,
          };
          console.log('Updating job card:', targetId, updateData);
          patchPromises.push(api.patch(`/jobcards/${targetId}`, updateData));
        });

        await Promise.all(patchPromises);

        toast.success('✅ Job card updated successfully!', {
          duration: 3000,
          style: {
            background: '#10B981',
            color: '#fff',
            fontWeight: 'bold',
          },
        });

        // Reset approval status to pending for re-review
        setTimeout(() => {
          navigate('/operator/jobcards');
        }, 1500);
      } else {
        // Create new job cards - one per entry row
        const createPromises: Promise<any>[] = [];

        data.entries.forEach((entry) => {
          // For TIME_BASED (or any module that requires hours), enforce a positive value on the client
          if (requiresHours) {
            if (!entry.actual_hours || entry.actual_hours <= 0) {
              throw new Error('Actual hours must be greater than 0 for this module.');
            }
          }

          const payload: CreateJobCardRequest = {
            employee_id: user.id!,
            work_order_id: entry.work_order_id,
            machine_id: entry.machine_id,
            activity_code_id: data.is_awc ? null : entry.activity_code_id,
            activity_desc: data.is_awc
              ? entry.activity_desc || 'AWC Activity'
              : entry.activity_desc || 'Activity',
            qty: entry.qty ?? 0,
            // Backend requires actual_hours > 0; for modules where hours are not shown,
            // send a small positive fallback.
            actual_hours: requiresHours ? entry.actual_hours! : (entry.actual_hours ?? 0.01),
            status: entry.status || JobCardStatusEnum.C,
            entry_date: data.entry_date,
            source: 'TECHNICIAN',
            shift: sharedShift,
            is_awc: selectedEfficiencyModule === 'TASK_BASED',
          };

          console.log('Sending payload to API:', payload);
          createPromises.push(api.post('/jobcards', payload));
        });

        await Promise.all(createPromises);

        toast.success('✅ Job cards created successfully!', {
          duration: 3000,
          style: {
            background: '#10B981',
            color: '#fff',
            fontWeight: 'bold',
          },
        });
        
        setTimeout(() => {
          navigate('/operator/jobcards');
        }, 1500);
      }
    } catch (error: any) {
      console.error('Failed to save job card:', error);

      let message: string = 'Failed to save job card';
      const detail = error?.response?.data?.detail ?? error?.response?.data;

      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        // Pydantic-style error list
        message = detail
          .map((e: any) => e?.msg || JSON.stringify(e))
          .join('; ');
      } else if (detail && typeof detail === 'object') {
        // Single Pydantic error object
        message = (detail as any).msg || JSON.stringify(detail);
      } else if (error?.message) {
        message = error.message;
      }

      toast.error(message, {
        duration: 4000,
      });
      setLoading(false);
    }
  };

  const getFieldRequirements = () => {
    switch (selectedEfficiencyModule) {
      case 'TIME_BASED':
        return { showShift: true, showHours: true, showQty: true, showStatus: false };
      case 'QUANTITY_BASED':
        return { showShift: true, showHours: true, showQty: true, showStatus: false };
      case 'TASK_BASED':
        return { showShift: true, showHours: true, showQty: true, showStatus: false };
      default:
        return { showShift: true, showHours: true, showQty: true, showStatus: false };
    }
  };

  const fieldReqs = getFieldRequirements();

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => navigate('/operator/jobcards')}
          className="flex items-center text-secondary-600 hover:text-secondary-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Job Cards
        </button>
        <h1 className="text-3xl font-bold text-secondary-900">{isEditing ? 'Edit Job Card' : 'Create Job Card'}</h1>
        <p className="text-secondary-600 mt-1">
          {isEditing ? 'Make corrections to your rejected job card' : `Enter job card details for ${user?.ec_number}`}
        </p>
      </div>

      <form 
        onSubmit={handleSubmit(
          onSubmit,
          (errors) => {
            console.error('Form validation failed:', errors);
            toast.error('Please fix form errors before submitting');
          }
        )} 
        className="bg-white rounded-lg shadow-md p-6 space-y-6"
      >
        {/* Date */}
        <div>
          <label htmlFor="entry_date" className="block text-sm font-medium text-secondary-700 mb-1">
            Date <span className="text-danger-600">*</span>
          </label>
          <input
            type="date"
            id="entry_date"
            {...register('entry_date')}
            className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          {errors.entry_date && (
            <p className="mt-1 text-sm text-danger-600">{errors.entry_date.message}</p>
          )}
        </div>

        {/* Efficiency Module Selection */}
        <div>
          <label htmlFor="efficiency_module" className="block text-sm font-medium text-secondary-700 mb-1">
            Efficiency Module <span className="text-danger-600">*</span>
          </label>
          {operatorModule ? (
            <div className="w-full px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-700">
              {operatorModule === 'TIME_BASED'
                ? 'Time-based'
                : operatorModule === 'QUANTITY_BASED'
                  ? 'Quantity-based'
                  : 'Task-based (AWC)'}
            </div>
          ) : (
            <select
              id="efficiency_module"
              {...register('efficiency_module')}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="TIME_BASED">Time-based</option>
              <option value="QUANTITY_BASED">Quantity-based</option>
              <option value="TASK_BASED">Task-based (AWC)</option>
            </select>
          )}
          {errors.efficiency_module && (
            <p className="mt-1 text-sm text-danger-600">{errors.efficiency_module.message}</p>
          )}
          {operatorModule && (
            <p className="mt-1 text-xs text-secondary-500">
              Your module is set by your supervisor assignment.
            </p>
          )}
        </div>

        {/* AWC Checkbox - only for Task-based module */}
        {(operatorModule || selectedEfficiencyModule) === 'TASK_BASED' && (
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_awc"
              {...register('is_awc')}
              disabled
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded disabled:opacity-50"
            />
            <label htmlFor="is_awc" className="ml-2 block text-sm text-secondary-700">
              Activity Without Code (AWC)
              <span className="text-primary-600 font-medium"> - Required for Task-based</span>
            </label>
          </div>
        )}

        {/* Entry Rows */}
        <div className="space-y-4">
          {fields.map((field, index) => (
            <div key={field.id} className="border border-secondary-200 rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-secondary-900">Entry {index + 1}</h2>
                {fields.length > 1 && !isEditing && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-xs text-danger-600 hover:text-danger-800"
                  >
                    Remove
                  </button>
                )}
              </div>

              {/* Manual machine/work order inputs removed as per requirement */}

              {/* Activity Code or Description per entry */}
              {!isAWC ? (
                <div>
                  <label
                    htmlFor={`entries.${index}.activity_code_id`}
                    className="block text-sm font-medium text-secondary-700 mb-1"
                  >
                    Activity Code <span className="text-danger-600">*</span>
                  </label>
                  <select
                    id={`entries.${index}.activity_code_id`}
                    {...register(`entries.${index}.activity_code_id` as const, { valueAsNumber: true })}
                    className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Select Activity Code</option>
                    {filteredActivityCodes.map((ac) => (
                      <option key={ac.id} value={ac.id}>
                        {ac.code} - {ac.description}
                      </option>
                    ))}
                  </select>
                  {errors.entries?.[index]?.activity_code_id && (
                    <p className="mt-1 text-sm text-danger-600">
                      {errors.entries[index]?.activity_code_id?.message as string}
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <label
                    htmlFor={`entries.${index}.activity_desc`}
                    className="block text-sm font-medium text-secondary-700 mb-1"
                  >
                    Activity Description <span className="text-danger-600">*</span>
                  </label>
                  <input
                    type="text"
                    id={`entries.${index}.activity_desc`}
                    {...register(`entries.${index}.activity_desc` as const)}
                    placeholder="Enter activity description"
                    className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                  {errors.entries?.[index]?.activity_desc && (
                    <p className="mt-1 text-sm text-danger-600">
                      {errors.entries[index]?.activity_desc?.message as string}
                    </p>
                  )}
                </div>
              )}

              {/* Machine per entry */}
              <div>
                <label
                  htmlFor={`entries.${index}.machine_id`}
                  className="block text-sm font-medium text-secondary-700 mb-1"
                >
                  Machine
                  {selectedEfficiencyModule !== 'TASK_BASED' && (
                    <span className="text-danger-600"> *</span>
                  )}
                </label>
                <select
                  id={`entries.${index}.machine_id`}
                  {...register(`entries.${index}.machine_id` as const, { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Select Machine</option>
                  {filteredMachines.map((machine) => (
                    <option key={machine.id} value={machine.id}>
                      {machine.machine_code} - {machine.description}
                    </option>
                  ))}
                </select>
                {errors.entries?.[index]?.machine_id && (
                  <p className="mt-1 text-sm text-danger-600">
                    {errors.entries[index]?.machine_id?.message as string}
                  </p>
                )}
              </div>

              {/* Work Order per entry */}
              <div>
                <label
                  htmlFor={`entries.${index}.work_order_id`}
                  className="block text-sm font-medium text-secondary-700 mb-1"
                >
                  Work Order
                  {selectedEfficiencyModule !== 'TASK_BASED' && (
                    <span className="text-danger-600"> *</span>
                  )}
                </label>
                <select
                  id={`entries.${index}.work_order_id`}
                  {...register(`entries.${index}.work_order_id` as const, { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Select Work Order</option>
                  {workOrders.map((wo) => (
                    <option key={wo.id} value={wo.id}>
                      {wo.wo_number} - Qty: {wo.planned_qty}
                    </option>
                  ))}
                </select>
                {errors.entries?.[index]?.work_order_id && (
                  <p className="mt-1 text-sm text-danger-600">
                    {errors.entries[index]?.work_order_id?.message as string}
                  </p>
                )}
              </div>

              {/* Quantity per entry (conditional) */}
              {fieldReqs.showQty && (
                <div>
                  <label
                    htmlFor={`entries.${index}.qty`}
                    className="block text-sm font-medium text-secondary-700 mb-1"
                  >
                    {selectedEfficiencyModule === 'QUANTITY_BASED' ? 'Actual Quantity' : 'Quantity'} <span className="text-danger-600">*</span>
                  </label>
                  <input
                    type="number"
                    id={`entries.${index}.qty`}
                    step="0.01"
                    {...register(`entries.${index}.qty` as const, { valueAsNumber: true })}
                    className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                  {errors.entries?.[index]?.qty && (
                    <p className="mt-1 text-sm text-danger-600">
                      {errors.entries[index]?.qty?.message as string}
                    </p>
                  )}
                </div>
              )}

              {/* Actual Hours per entry (conditional) */}
              {fieldReqs.showHours && (
                <div>
                  <label
                    htmlFor={`entries.${index}.actual_hours`}
                    className="block text-sm font-medium text-secondary-700 mb-1"
                  >
                    {selectedEfficiencyModule === 'TIME_BASED' ? 'Actual Hours' : 'Time Taken'} <span className="text-danger-600">*</span>
                  </label>
                  <input
                    type="number"
                    id={`entries.${index}.actual_hours`}
                    step="0.01"
                    {...register(`entries.${index}.actual_hours` as const, { valueAsNumber: true })}
                    className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                  {errors.entries?.[index]?.actual_hours && (
                    <p className="mt-1 text-sm text-danger-600">
                      {errors.entries[index]?.actual_hours?.message as string}
                    </p>
                  )}
                </div>
              )}

              {/* Status per entry (conditional) */}
              {fieldReqs.showStatus && (
                <div>
                  <label
                    htmlFor={`entries.${index}.status`}
                    className="block text-sm font-medium text-secondary-700 mb-1"
                  >
                    Status <span className="text-danger-600">*</span>
                  </label>
                  <select
                    id={`entries.${index}.status`}
                    {...register(`entries.${index}.status` as const)}
                    className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value={JobCardStatusEnum.C}>Complete (C)</option>
                    <option value={JobCardStatusEnum.IC}>Incomplete (IC)</option>
                  </select>
                  {errors.entries?.[index]?.status && (
                    <p className="mt-1 text-sm text-danger-600">
                      {errors.entries[index]?.status?.message as string}
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}

          {!isEditing && (
            <button
              type="button"
              onClick={() =>
                append({
                  work_order_id: undefined as unknown as number,
                  machine_id: undefined as unknown as number,
                  activity_code_id: null,
                  activity_desc: '',
                  qty: undefined,
                  actual_hours: undefined,
                  status: JobCardStatusEnum.C,
                })
              }
              className="mt-2 inline-flex items-center px-3 py-1.5 border border-dashed border-primary-500 text-sm text-primary-700 rounded-md hover:bg-primary-50"
            >
              + Add Entry
            </button>
          )}
        </div>
        {/* Shift (conditional, shared header) */}
        {fieldReqs.showShift && (
          <div>
            <label htmlFor="shift" className="block text-sm font-medium text-secondary-700 mb-1">
              Shift <span className="text-danger-600">*</span>
            </label>
            <select
              id="shift"
              {...register('shift', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value={1}>Shift 1</option>
              <option value={2}>Shift 2</option>
              <option value={3}>Shift 3</option>
            </select>
            {errors.shift && (
              <p className="mt-1 text-sm text-danger-600">{errors.shift.message}</p>
            )}
          </div>
        )}


        {/* Submit Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-secondary-200">
          <button
            type="button"
            onClick={() => navigate('/operator/jobcards')}
            className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            onClick={() => console.log('Create button clicked!')}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>{isEditing ? 'Updating...' : 'Creating...'}</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{isEditing ? 'Update Job Card' : 'Create Job Card'}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default JobCardForm;
