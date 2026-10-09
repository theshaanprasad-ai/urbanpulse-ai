import React from 'react';
import {
  CloudRain,
  MapPin,
  Activity,
  Layers,
  Brain,
  MessageSquare,
  AlertTriangle,
  ShieldCheck,
  TrendingUp,
  Database,
  LogOut,
  Home,
  Flame,
  History,
  Thermometer,
} from 'lucide-react';
import { DataMode } from '../types';
import { useAuth } from '../auth/AuthContext';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  selectedCity: string;
  onCityChange: (city: string) => void;
  dataMode: DataMode;
}

const CITIZEN_TABS = [
  { id: 'citizen-home', label: 'Report a problem', shortLabel: 'Report', icon: Home },
  { id: 'risk-map', label: 'City map', shortLabel: 'Map', icon: Layers },
  { id: 'alerts-actions', label: 'What the city is doing', shortLabel: 'Alerts', icon: AlertTriangle },
];

const OFFICER_TABS = [
  { id: 'command-center', label: 'Overview', shortLabel: 'Overview', icon: Activity },
  { id: 'risk-map', label: 'Risk map', shortLabel: 'Map', icon: Layers },
  { id: 'civic-intelligence', label: 'Citizen reports', shortLabel: 'Reports', icon: MessageSquare },
  { id: 'alerts-actions', label: 'Action queue', shortLabel: 'Actions', icon: AlertTriangle },
  { id: 'temporal-anomalies', label: 'Anomaly explorer', shortLabel: 'Anomalies', icon: TrendingUp },
  { id: 'cross-category', label: 'Patterns', shortLabel: 'Patterns', icon: Brain },
  { id: 'rainfall', label: 'Weather', shortLabel: 'Weather', icon: CloudRain },
  { id: 'risk-engine', label: 'Risk engine', shortLabel: 'Risk', icon: Flame },
  { id: 'hotspots-replay', label: 'Hotspots', shortLabel: 'Hotspots', icon: History },
  { id: 'climate', label: 'Climate', shortLabel: 'Climate', icon: Thermometer },
  { id: 'datasources', label: 'Data & evaluation', shortLabel: 'Data', icon: Database },
];

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  selectedCity,
  onCityChange,
  dataMode,
}) => {
  const { user, workspace, setWorkspace, signOut } = useAuth();
  const tabs = workspace === 'citizen' ? CITIZEN_TABS : OFFICER_TABS;

  return (
    <header className="bg-[#0B0F17] border-b border-slate-800 sticky top-0 z-50">
      <div className="px-4 py-2.5 flex flex-wrap items-center justify-between border-b border-slate-800/80 gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">UrbanPulse</span>
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                {workspace === 'citizen' ? 'Resident' : 'Control room'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-none">
              {workspace === 'citizen' ? 'Simple city reporting for local people' : 'Full urban issue intelligence'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center bg-slate-900 border border-slate-700 rounded-lg p-0.5 text-xs">
            <button
              onClick={() => { setWorkspace('citizen'); onTabChange('citizen-home'); }}
              className={`px-2.5 py-1 rounded-md ${workspace === 'citizen' ? 'bg-emerald-500 text-slate-950 font-semibold' : 'text-slate-400'}`}
            >
              Resident
            </button>
            <button
              onClick={() => { setWorkspace('control-room'); onTabChange('command-center'); }}
              className={`px-2.5 py-1 rounded-md ${workspace === 'control-room' ? 'bg-emerald-500 text-slate-950 font-semibold' : 'text-slate-400'}`}
            >
              Control room
            </button>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700/80 rounded-md px-2.5 py-1 text-xs">
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <select
              value={selectedCity}
              onChange={(e) => onCityChange(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
            >
              <option value="chennai" className="bg-slate-900">Chennai</option>
              <option value="bengaluru" className="bg-slate-900">Bengaluru</option>
              <option value="bhubaneswar" className="bg-slate-900">Bhubaneswar</option>
            </select>
          </div>

          {workspace === 'control-room' && (
            <div className="hidden sm:flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-md px-2.5 py-1 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{dataMode}</span>
            </div>
          )}

          {user?.email && (
            <button
              onClick={() => signOut()}
              className="flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1 text-xs text-slate-300 hover:text-white"
              title={user.email}
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline max-w-[140px] truncate">{user.email}</span>
            </button>
          )}
        </div>
      </div>

      <nav className="px-4 py-2 bg-[#0B0F17]/90 backdrop-blur">
        <label className="sr-only" htmlFor="section-navigation">Navigate dashboard section</label>
        <select
          id="section-navigation"
          value={currentTab}
          onChange={(event) => onTabChange(event.target.value)}
          className="mb-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400 md:hidden"
        >
          {tabs.map((tab) => <option key={tab.id} value={tab.id}>{tab.label}</option>)}
        </select>
        <div className="hidden space-x-1 overflow-x-auto scrollbar-none md:flex">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition cursor-pointer ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{tab.shortLabel}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </header>
  );
};
