import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import {
  TrendingUp,
  ShieldAlert,
  AlertTriangle,

  Info,
  Building2,
  Waves,
  Compass
} from 'lucide-react';
import { ClimateScenario } from '../types';

interface ClimateStressViewProps {
  scenarios: ClimateScenario[];
}

export const ClimateStressView: React.FC<ClimateStressViewProps> = ({ scenarios }) => {
  const chartData = scenarios.map((s) => ({
    name: s.scenario_name.replace('CMIP6 ', '').replace('Historical ', ''),
    multiplier: s.extreme_rainfall_frequency_multiplier,
    runoffIncrease: s.projected_runoff_increase_pct,
    vulnerableWards: s.vulnerable_ward_count,
  }));

  return (
    <div className="space-y-6">
      {/* 1. Header & Distinct Climatological Disclaimer */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-white">
              Future Climate & Infrastructure Stress-Testing (CMIP6 / INDRA)
            </h2>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-medium">
            30-Year Climatological Horizon
          </span>
        </div>

        {/* Essential Scientific Disclaimer (Principle 3 & Module J) */}
        <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <strong className="block text-amber-300">CLIMATOLOGICAL HORIZON DISTINCTION NOTICE</strong>
            Climate scenarios evaluate changes in multi-decadal rainfall distributions and extreme return periods under shared socioeconomic pathways (SSP2-4.5 & SSP5-8.5). They are intended for municipal master planning, culvert sizing, and sponge-city retention investments, <strong>NOT as operational 24-hour weather forecasts.</strong>
          </div>
        </div>
      </div>

      {/* 2. Scenario Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extreme Rainfall Frequency Multiplier */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
            <Waves className="w-4 h-4 text-purple-400" />
            Frequency Multiplier of Extreme Rainfall Events (&gt;100 mm/day)
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Under SSP5-8.5 late-century, 100mm+ precipitation days occur with 2.45x historical frequency.
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="multiplier" name="Frequency Multiplier" fill="#A855F7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Projected Catchment Runoff Increase */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-cyan-400" />
            Catchment Runoff Volume Increase (%) under Urban Densification
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Combined climate warming and impervious concrete surface growth amplify peak stormwater discharge.
          </p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="runoffIncrease" name="Runoff Increase (%)" fill="#06B6D4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 3. Detailed Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {scenarios.map((s) => (
          <div key={s.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-slate-400 uppercase">{s.time_horizon}</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">CMIP6</span>
            </div>

            <h4 className="font-bold text-white text-sm leading-snug">{s.scenario_name}</h4>

            <div className="space-y-1.5 pt-2 border-t border-slate-800 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Extreme Rain Multiplier:</span>
                <span className="font-bold text-purple-400">{s.extreme_rainfall_frequency_multiplier}x</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Peak Runoff Surge:</span>
                <span className="font-bold text-cyan-400">+{s.projected_runoff_increase_pct}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Vulnerable Wards:</span>
                <span className="font-bold text-rose-400">{s.vulnerable_ward_count} of 15</span>
              </div>
            </div>

            <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-800/80">
              Source: {s.data_source_citation}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
