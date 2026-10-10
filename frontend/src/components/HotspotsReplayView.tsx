import React, { useState, useEffect } from 'react';
import {
  Flame,
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  Clock,
  History,
  ShieldAlert,
  CloudRain,
  MessageSquare,
  AlertTriangle
} from 'lucide-react';
import { HotspotCluster } from '../types';

interface HotspotsReplayViewProps {
  hotspots: HotspotCluster[];
}

export const HotspotsReplayView: React.FC<HotspotsReplayViewProps> = ({ hotspots }) => {
  // Replay timeline state
  const [currentStep, setCurrentStep] = useState<number>(3); // Default to full peak scenario
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const replaySteps = [
    {
      hour: 'T+0 Hours (Morning Baseline)',
      rainfall: '0.0 mm',
      status: 'NORMAL',
      complaintsCount: 1,
      hotspotState: 'Zero clusters detected. Base municipal drainage operational.',
      riskLevel: 'LOW (Citywide Score: 18/100)',
      highlight: 'Weather clear. Automatic rain gauges operating normally.',
    },
    {
      hour: 'T+3 Hours (Monsoon Trough Arrives)',
      rainfall: '28.5 mm (1h Burst)',
      status: 'WATCH',
      complaintsCount: 3,
      hotspotState: 'Scattered complaints at Vyasarpadi and Velachery. No clusters yet.',
      riskLevel: 'MODERATE (Score: 38/100)',
      highlight: 'Rainfall burst begins. Storm drains flowing at 60% capacity.',
    },
    {
      hour: 'T+6 Hours (IMD Orange Alert & Downpour)',
      rainfall: '68.0 mm (3h Burst)',
      status: 'WARNING',
      complaintsCount: 6,
      hotspotState: 'Spatial density clustering detects initial clustering at Vyasarpadi Subway (2.5x baseline).',
      riskLevel: 'ELEVATED (Score: 56/100)',
      highlight: 'IMD issues Orange Warning. Water level reaches 25cm in subways.',
    },
    {
      hour: 'T+12 Hours (Torrential Deluge & Lake Overflow)',
      rainfall: '118.0 mm (24h Total)',
      status: 'CRITICAL',
      complaintsCount: 10,
      hotspotState: 'EMERGING HOTSPOT: Velachery Main Road surge (5.0x above dry baseline).',
      riskLevel: 'CRITICAL (Score: 88.5/100)',
      highlight: 'Velachery lake sluice overflows. 3 subways closed by traffic police.',
    },
    {
      hour: 'T+18 Hours (Municipal Response & Dewatering)',
      rainfall: '135.0 mm (Cumulative)',
      status: 'CONTROLLED ACTION',
      complaintsCount: 10,
      hotspotState: 'Hotspot stabilized. Mobile high-capacity 100-HP pumps active.',
      riskLevel: 'HIGH (Score: 68/100 - Falling)',
      highlight: 'Disaster command center coordinates mobile sump drainage.',
    },
  ];

  // Auto-player effect
  useEffect(() => {
    let timer: any;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= replaySteps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 3000);
    }
    return () => clearInterval(timer);
  }, [isPlaying, replaySteps.length]);

  const activeStepData = replaySteps[currentStep];

  return (
    <div className="space-y-6">
      {/* 1. Historical Event Replay Controller (Module 13A) */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">
              Historical Event Replay & Hotspot Emergence Simulator
            </h3>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium">
            Timeline Step {currentStep + 1} of {replaySteps.length}
          </span>
        </div>

        <p className="text-xs text-slate-300 mb-5 leading-relaxed">
          Demonstrates how the early warning pipeline transitions dynamically from early rainfall observations to civic complaint bursts, spatial density clustering, and automated risk escalation.
        </p>

        {/* Timeline Progress Tracker */}
        <div className="grid grid-cols-5 gap-2 mb-5">
          {replaySteps.map((step, idx) => (
            <button
              key={idx}
              onClick={() => {
                setCurrentStep(idx);
                setIsPlaying(false);
              }}
              className={`p-2.5 rounded-lg border text-left transition cursor-pointer ${
                currentStep === idx
                  ? 'bg-emerald-500/20 border-emerald-500 text-white shadow-sm'
                  : currentStep > idx
                  ? 'bg-slate-950 border-slate-800 text-slate-300'
                  : 'bg-slate-950/50 border-slate-900 text-slate-400'
              }`}
            >
              <div className="text-[10px] font-mono text-slate-400">Step {idx + 1}</div>
              <div className="text-xs font-semibold truncate">{step.hour.split(' ')[0]}</div>
            </button>
          ))}
        </div>

        {/* Step Snapshot Box */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Timeline Milestone</span>
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                {activeStepData.hour}
                <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                  {activeStepData.status}
                </span>
              </h4>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="text-right">
                <span className="text-slate-400 block text-[10px]">Precipitation:</span>
                <span className="font-bold text-blue-400">{activeStepData.rainfall}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-400 block text-[10px]">Civic Reports:</span>
                <span className="font-bold text-amber-400">{activeStepData.complaintsCount} Grievances</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80 text-xs">
            <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400 text-[10px] font-semibold uppercase block">
                Spatial Hotspot Engine
              </span>
              <p className="text-slate-200 mt-0.5">{activeStepData.hotspotState}</p>
            </div>
            <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-400 text-[10px] font-semibold uppercase block">
                Modeled Risk State
              </span>
              <p className="text-emerald-400 font-semibold mt-0.5">{activeStepData.riskLevel}</p>
            </div>
          </div>

          <p className="text-xs text-slate-400 italic pt-1">
            Summary: {activeStepData.highlight}
          </p>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-between gap-3 mt-4 pt-3 border-t border-slate-800">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition flex items-center gap-2 cursor-pointer"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-white" />}
              <span>{isPlaying ? 'Pause Replay' : 'Play Scenario'}</span>
            </button>
            <button
              onClick={() => {
                if (currentStep < replaySteps.length - 1) setCurrentStep((prev) => prev + 1);
              }}
              disabled={currentStep >= replaySteps.length - 1}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-3 py-2 rounded-lg transition flex items-center gap-1.5 cursor-pointer disabled:opacity-40"
            >
              <SkipForward className="w-3.5 h-3.5" />
              <span>Step Next</span>
            </button>
            <button
              onClick={() => {
                setCurrentStep(0);
                setIsPlaying(false);
              }}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-3 py-2 rounded-lg transition flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>

          <span className="text-xs text-slate-400 font-mono hidden sm:inline">
            Event Velocity: 1 Step / 3s
          </span>
        </div>
      </div>

      {/* 2. Detected Spatial Hotspot Clusters Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-500" />
            <h3 className="text-base font-bold text-white">Active Spatial Hotspot Clusters (Density-Based)</h3>
          </div>
          <span className="text-xs text-slate-400">
            Density Radius: 450 meters • Min Reports: 2
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {hotspots.map((h) => (
            <div key={h.id} className="p-4 rounded-xl bg-slate-950 border border-rose-500/30 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-rose-400" /> {h.cluster_name}
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 font-semibold text-[10px] uppercase">
                  {h.status}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[11px] p-2.5 rounded bg-slate-900 border border-slate-800">
                <div>
                  <span className="text-slate-400 block">Reports:</span>
                  <span className="font-bold text-white text-sm">{h.complaint_count}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Dry Baseline:</span>
                  <span className="text-slate-300 font-semibold">{h.baseline_normal_count}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Anomaly Surge:</span>
                  <span className="font-bold text-rose-400 text-sm">{h.anomaly_ratio}x</span>
                </div>
              </div>

              <p className="text-slate-300 text-[11px] leading-relaxed">
                Evidence: {h.rainfall_evidence}
              </p>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-400">
                <span>Centroid: {h.center_lat.toFixed(4)}, {h.center_lon.toFixed(4)}</span>
                <span>Radius: {h.radius_meters}m</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
