import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  ShieldAlert,
  Send,
  UserCheck,
  Building,
  Info,
  Check,
  Flame,
  CloudRain,
  Zap,
  TrendingUp,
  Layers,
  ArrowRight
} from 'lucide-react';
import { SystemAlert, DecisionAction } from '../types';

interface AlertsActionsViewProps {
  alerts: SystemAlert[];
  actions: DecisionAction[];
  onUpdateAction: (actionId: number, status: string, assignedTo?: string, reason?: string) => Promise<void>;
}

export const AlertsActionsView: React.FC<AlertsActionsViewProps> = ({
  alerts,
  actions,
  onUpdateAction,
}) => {
  const [alertFilter, setAlertFilter] = useState<string>('ALL');
  const [queueTab, setQueueTab] = useState<'ALL' | 'QUEUE_A' | 'QUEUE_B'>('ALL');
  const [activeActionId, setActiveActionId] = useState<number | null>(null);
  const [assigneeName, setAssigneeName] = useState<string>('Rapid Incident Response Unit');
  const [actionReason, setActionReason] = useState<string>('Immediate field verification and hazard mitigation');
  const [isUpdating, setIsUpdating] = useState<boolean>(false);

  const filteredAlerts = alerts.filter((a) => {
    if (alertFilter === 'ALL') return true;
    return a.alert_class === alertFilter;
  });

  const queueAActions = actions.filter(
    (a) => a.queue_type === 'EMERGING_PATTERN_QUEUE' || (!a.queue_type && a.priority_score < 90)
  );
  const queueBActions = actions.filter(
    (a) => a.queue_type === 'HIGH_SEVERITY_HAZARD_QUEUE' || (!a.queue_type && a.priority_score >= 90)
  );

  const displayedActions =
    queueTab === 'QUEUE_A' ? queueAActions : queueTab === 'QUEUE_B' ? queueBActions : actions;

  const handleActionStatusChange = async (actionId: number, newStatus: string) => {
    setIsUpdating(true);
    try {
      await onUpdateAction(actionId, newStatus, assigneeName, actionReason);
      setActiveActionId(null);
    } catch (err) {
      console.error('Failed to update action:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Dual Queue Operational Command Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">
                Dual Operational Decision &amp; Action Queues
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Separates systemic multi-incident pattern escalations from immediate single-incident life-safety hazards.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setQueueTab('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                queueTab === 'ALL'
                  ? 'bg-slate-700 text-white'
                  : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              All Tasks ({actions.length})
            </button>
            <button
              onClick={() => setQueueTab('QUEUE_A')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                queueTab === 'QUEUE_A'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <span>Queue A: Emerging Patterns ({queueAActions.length})</span>
            </button>
            <button
              onClick={() => setQueueTab('QUEUE_B')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                queueTab === 'QUEUE_B'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-rose-400" />
              <span>Queue B: Severe Hazards ({queueBActions.length})</span>
            </button>
          </div>
        </div>

        {/* Queue Description Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800">
          <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-xs">
            <span className="font-bold text-emerald-400 flex items-center gap-1.5 mb-1">
              <TrendingUp className="w-4 h-4" /> Queue A: Systemic Emerging Patterns
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Prioritized by statistical deviation, spatial clustering, and multi-category co-occurrence.
              Targeted for preventive infrastructure intervention before issues compound.
            </p>
          </div>

          <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 text-xs">
            <span className="font-bold text-rose-400 flex items-center gap-1.5 mb-1">
              <Zap className="w-4 h-4" /> Queue B: High-Severity Immediate Hazards
            </span>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              Fast-tracked urgent safety threats (open manholes, live wires, collapsed roads, trapped vehicles).
              Demands immediate squad dispatch within 30-minute target SLA.
            </p>
          </div>
        </div>
      </div>

      {/* Action Cards Queue */}
      <div className="space-y-4">
        {displayedActions.map((act) => {
          const isEditing = activeActionId === act.id;
          const isQueueB =
            act.queue_type === 'HIGH_SEVERITY_HAZARD_QUEUE' || act.priority_score >= 90;

          return (
            <div
              key={act.id}
              className={`p-5 rounded-xl border text-xs space-y-3 transition shadow-sm ${
                act.status === 'RESOLVED'
                  ? 'bg-slate-950/40 border-slate-800/60 opacity-60'
                  : isQueueB
                  ? 'bg-slate-950 border-rose-500/40'
                  : 'bg-slate-950 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      isQueueB
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    }`}
                  >
                    {isQueueB ? '🚨 QUEUE B: IMMEDIATE HAZARD' : '📈 QUEUE A: EMERGING PATTERN'}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    RANK #{act.priority_rank}
                  </span>
                  <h4 className="font-bold text-white text-sm">{act.location_name}</h4>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                    {act.target_department || act.action_type}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`font-bold font-mono text-sm ${
                      isQueueB ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    Priority: {act.priority_score}/100
                  </span>
                  <span
                    className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded ${
                      act.status === 'PENDING_REVIEW'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : act.status === 'RESOLVED'
                        ? 'bg-slate-800 text-slate-400'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    }`}
                  >
                    {act.status.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              <p className="text-slate-200 text-xs leading-relaxed">{act.description}</p>
              <p className="text-slate-400 text-[11px] bg-slate-900/50 p-2 rounded border border-slate-800/80">
                <strong className="text-slate-300">Evidence Basis:</strong> {act.evidence_basis}
              </p>

              {act.assigned_to && (
                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-300 flex items-center justify-between">
                  <span>
                    Assigned Unit: <strong className="text-white">{act.assigned_to}</strong>
                  </span>
                  <span className="text-slate-400">
                    Dispatched: {new Date(act.updated_at).toLocaleTimeString()}
                  </span>
                </div>
              )}

              {/* Operator Controls */}
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  {act.status === 'PENDING_REVIEW' && (
                    <button
                      onClick={() => handleActionStatusChange(act.id, 'ACKNOWLEDGED')}
                      disabled={isUpdating}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition cursor-pointer text-xs"
                    >
                      Acknowledge Task
                    </button>
                  )}

                  <button
                    onClick={() => setActiveActionId(isEditing ? null : act.id)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer text-xs"
                  >
                    {isEditing ? 'Cancel Assignment' : 'Assign Squad / Transition'}
                  </button>

                  {act.status !== 'RESOLVED' && (
                    <button
                      onClick={() => handleActionStatusChange(act.id, 'RESOLVED')}
                      disabled={isUpdating}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition cursor-pointer text-xs"
                    >
                      Mark Resolved
                    </button>
                  )}
                </div>

                <span className="text-[10px] text-slate-500 font-mono">
                  Audit Logging: Active (Immutable Operator Trail)
                </span>
              </div>

              {/* Inline Assignment Form */}
              {isEditing && (
                <div className="p-3.5 rounded-lg bg-slate-900 border border-emerald-500/40 space-y-3 mt-3">
                  <span className="font-bold text-white text-xs block">Operational Dispatch &amp; Assignment</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-1">Assigned Field Unit / Squad:</label>
                      <input
                        type="text"
                        value={assigneeName}
                        onChange={(e) => setAssigneeName(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-400 block mb-1">Operational Justification:</label>
                      <input
                        type="text"
                        value={actionReason}
                        onChange={(e) => setActionReason(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => handleActionStatusChange(act.id, 'ASSIGNED')}
                      disabled={isUpdating}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3 py-1.5 rounded transition cursor-pointer"
                    >
                      Confirm Dispatch
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 3-Tier Explainable Alert Stream */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Three-Tier Explainable Alert Stream
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly separates Official Meteorological Bulletins, Model Impact Signals, and Civic Anomaly Spikes.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={alertFilter}
              onChange={(e) => setAlertFilter(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-2.5 py-1 focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Alert Classes ({alerts.length})</option>
              <option value="OFFICIAL_WEATHER_ALERT">Class 1: Official Meteorological Warnings</option>
              <option value="MODEL_IMPACT_RISK">Class 2: Modeled Impact Risk</option>
              <option value="CIVIC_ANOMALY">Class 3: Civic Grievance Anomalies</option>
            </select>
          </div>
        </div>

        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-xl border text-xs space-y-2 transition ${
                alert.severity === 'CRITICAL'
                  ? 'bg-rose-950/20 border-rose-500/40'
                  : 'bg-slate-950 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      alert.severity === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    }`}
                  >
                    {alert.alert_class.replace(/_/g, ' ')}
                  </span>
                  <h4 className="font-bold text-white text-xs">{alert.title}</h4>
                </div>
                <span className="text-[11px] text-slate-400">{alert.location_name}</span>
              </div>

              <p className="text-slate-300 leading-relaxed">{alert.evidence_text}</p>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span>
                  <strong>Recommended Action:</strong> {alert.recommended_action}
                </span>
                <span className="text-[10px] font-mono text-slate-500">Ref: {alert.source_reference}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
