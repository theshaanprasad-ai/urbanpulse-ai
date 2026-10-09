import React, { useState } from 'react';
import {
  Brain,
  Sliders,
  Play,
  ShieldCheck,
  TrendingUp,
  Info,
  CheckCircle2,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import { RiskAssessment, WhatIfResponse } from '../types';

interface RiskEngineViewProps {
  assessments: RiskAssessment[];
  currentMode: 'MODE_1_BASELINE' | 'MODE_2_ML';
  onModeChange: (mode: 'MODE_1_BASELINE' | 'MODE_2_ML') => void;
  onSimulateWhatIf: (additionalRainMm: number, blockagePct: number) => Promise<WhatIfResponse>;
}

export const RiskEngineView: React.FC<RiskEngineViewProps> = ({
  assessments,
  currentMode,
  onModeChange,
  onSimulateWhatIf,
}) => {
  // What-If Simulation State
  const [additionalRain, setAdditionalRain] = useState<number>(45.0);
  const [blockagePct, setBlockagePct] = useState<number>(25.0);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<WhatIfResponse | null>(null);

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await onSimulateWhatIf(additionalRain, blockagePct);
      setSimResult(res);
    } catch (err) {
      console.error('What-If simulation failed:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleResetSimulation = () => {
    setSimResult(null);
    setAdditionalRain(45.0);
    setBlockagePct(25.0);
  };

  return (
    <div className="space-y-6">
      {/* 1. Operating Mode Selector Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs text-slate-400 font-semibold uppercase">Engine Analytical Paradigm</span>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Urban Impact-Risk Engine
            <span className="text-xs px-2.5 py-0.5 rounded font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              {currentMode === 'MODE_1_BASELINE' ? 'Mode 1: Evidence Baseline' : 'Mode 2: Empirical ML Classifier'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Estimates potential local physical and civic disruption rather than merely predicting weather occurrence.
          </p>
        </div>

        {/* Mode Toggle Controls */}
        <div className="flex items-center gap-1 bg-slate-950 p-1.5 rounded-lg border border-slate-800 w-full md:w-auto">
          <button
            onClick={() => onModeChange('MODE_1_BASELINE')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer flex-1 md:flex-initial ${
              currentMode === 'MODE_1_BASELINE'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Mode 1: Physical Baseline
          </button>
          <button
            onClick={() => onModeChange('MODE_2_ML')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer flex-1 md:flex-initial ${
              currentMode === 'MODE_2_ML'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Mode 2: Trained ML Model
          </button>
        </div>
      </div>

      {/* 2. Mode Explanation Card */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs flex items-start gap-3">
        <Info className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="text-white block font-medium">
            {currentMode === 'MODE_1_BASELINE'
              ? 'Mode 1 Architecture: Deterministic Multi-Factor Hydrologic-Urban Vulnerability Score'
              : 'Mode 2 Architecture: Regularized Logistic Regression with 5-Fold Temporal Holdout'}
          </strong>
          <p className="text-slate-300 leading-relaxed">
            {currentMode === 'MODE_1_BASELINE'
              ? 'Combines forecast precipitation (30%), soil moisture index (15%), low elevation basin depth (15%), urban imperviousness (15%), drainage chokes & subways (15%), and citizen grievance recurrence (10%). Guarantees deterministic explainability without black-box halluncinations.'
              : 'Empirically calibrated against historical Chennai flood events (2015-2023). Outputs calibrated flood probabilities and feature weights. Validates that empirical data matches physical hydrologic theory.'}
          </p>
        </div>
      </div>

      {/* 3. Interactive What-If Scenario Stress Testing */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Interactive What-If Rainfall Scenario Simulator</h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-medium">
            Hydrologic Stress-Testing
          </span>
        </div>

        <p className="text-xs text-slate-300 mb-5 leading-relaxed">
          Allows municipal engineers to evaluate drainage resilience by injecting hypothetical extreme precipitation bursts and silt choke percentages across Chennai catchments.
        </p>

        {/* Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-950/80 p-4 rounded-xl border border-slate-800/80">
          {/* Slider 1: Additional Rainfall */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-200">Hypothetical Additional Rainfall:</span>
              <span className="font-bold text-emerald-400 text-sm">+{additionalRain} mm</span>
            </div>
            <input
              type="range"
              min="0"
              max="150"
              step="5"
              value={additionalRain}
              onChange={(e) => setAdditionalRain(Number(e.target.value))}
              className="w-full accent-emerald-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>0 mm (Current)</span>
              <span>+50 mm (Heavy Shower)</span>
              <span>+100 mm (Downpour)</span>
              <span>+150 mm (Cloudburst)</span>
            </div>
          </div>

          {/* Slider 2: Storm Drain Silt Blockage */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-200">Culvert / Storm Drain Blockage:</span>
              <span className="font-bold text-amber-400 text-sm">{blockagePct}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="80"
              step="5"
              value={blockagePct}
              onChange={(e) => setBlockagePct(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400">
              <span>0% (Clean Drains)</span>
              <span>25% (Typical Monsoon Silt)</span>
              <span>50% (Heavy Silt & Plastic)</span>
              <span>80% (Severe Choke)</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition flex items-center gap-2 cursor-pointer shadow-md disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>{isSimulating ? 'Recalculating Catchment Runoff...' : 'Run Simulation'}</span>
          </button>

          {simResult && (
            <button
              onClick={handleResetSimulation}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs px-3 py-2.5 rounded-lg transition flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Simulation</span>
            </button>
          )}
        </div>

        {/* Simulation Output Card */}
        {simResult && (
          <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-emerald-500/40 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-white text-sm">{simResult.scenario_description}</h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Average City Flood Vulnerability Escalation: <strong className="text-amber-400">+{simResult.average_risk_increase_pct}%</strong>
                </p>
              </div>
              <div className="flex gap-4 text-right text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px]">Baseline Critical</span>
                  <span className="font-bold text-slate-300 text-base">{simResult.baseline_critical_wards} Wards</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Projected Critical</span>
                  <span className="font-bold text-rose-400 text-base">{simResult.projected_critical_wards} Wards</span>
                </div>
              </div>
            </div>

            {/* Ward-level Delta Table */}
            <div className="overflow-x-auto max-h-64">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-2 font-medium">Ward / Catchment</th>
                    <th className="pb-2 font-medium">Baseline Score</th>
                    <th className="pb-2 font-medium">Projected Score</th>
                    <th className="pb-2 font-medium">Risk Delta</th>
                    <th className="pb-2 font-medium">Projected Category</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {simResult.ward_projected_risks.map((w) => (
                    <tr key={w.zone_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2 font-medium text-white">{w.zone_name}</td>
                      <td className="py-2 text-slate-300">{w.baseline_score}</td>
                      <td className="py-2 font-bold text-white">{w.projected_score}</td>
                      <td className="py-2 font-bold text-amber-400">+{w.risk_delta} pts</td>
                      <td className="py-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            w.projected_category === 'CRITICAL'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                              : w.projected_category === 'HIGH'
                              ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                          }`}
                        >
                          {w.projected_category}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* 4. Complete Ward Risk Factor Contributions */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-bold text-white mb-3">
          Detailed Factor Decomposition by Administrative Zone ({assessments.length} Zones)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {assessments.map((a) => (
            <div key={a.zone_id} className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-xs">{a.zone_name ?? a.zone_id}</span>
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded ${
                    a.risk_category === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' :
                    a.risk_category === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                    a.risk_category === 'ELEVATED' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
                  }`}
                >
                  {a.overall_risk_score} / 100
                </span>
              </div>

              <div className="space-y-1 text-[11px] text-slate-300">
                {a.contributing_factors?.slice(0, 3).map((f, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-slate-400 truncate max-w-[180px]">{f.factor_name}</span>
                    <span className="font-medium text-emerald-400">{f.score} pts</span>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                <span>Confidence: {Math.round(a.confidence_score * 100)}%</span>
                <span>Completeness: {a.data_completeness_pct}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
