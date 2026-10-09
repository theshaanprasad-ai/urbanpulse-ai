import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import {
  City,
  Zone,
  VulnerableAsset,
  RainfallObservation,
  RainfallAnalytics,
  OfficialWarning,
  HistoricalWaterlogging,
  CivicComplaint,
  DuplicateCandidatePair,
  HotspotCluster,
  RiskAssessment,
  SystemAlert,
  DecisionAction,
  ClimateScenario,
  DataSourceStatus,
  EvaluationReport,
  DataMode
} from './types';
import { Navbar } from './components/Navbar';
import { CommandCenterView } from './components/CommandCenterView';
import { UrbanRiskMapView } from './components/UrbanRiskMapView';
import { RainfallIntelligenceView } from './components/RainfallIntelligenceView';
import { RiskEngineView } from './components/RiskEngineView';
import { CivicIntelligenceView } from './components/CivicIntelligenceView';
import { TemporalAnomalyExplorerView } from './components/TemporalAnomalyExplorerView';
import { CrossCategoryPatternsView } from './components/CrossCategoryPatternsView';
import { HotspotsReplayView } from './components/HotspotsReplayView';
import { AlertsActionsView } from './components/AlertsActionsView';
import { ClimateStressView } from './components/ClimateStressView';
import { DataSourcesEvaluationView } from './components/DataSourcesEvaluationView';
import { CitizenHomeView } from './components/CitizenHomeView';
import { LoginScreen } from './components/LoginScreen';
import { Loader2, AlertCircle, ShieldAlert } from 'lucide-react';
import { AIAssistant } from './components/AIAssistant';
import { useAuth } from './auth/AuthContext';

export function App() {
  const { user, loading: authLoading, workspace } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('citizen-home');
  const [selectedCity, setSelectedCity] = useState<string>('chennai');
  const [dataMode, setDataMode] = useState<DataMode>('LIVE');
  const [riskMode, setRiskMode] = useState<'MODE_1_BASELINE' | 'MODE_2_ML'>('MODE_1_BASELINE');
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);

  // Loaded Data
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const [zones, setZones] = useState<Zone[]>([]);
  const [assets, setAssets] = useState<VulnerableAsset[]>([]);
  const [observations, setObservations] = useState<RainfallObservation[]>([]);
  const [analytics, setAnalytics] = useState<RainfallAnalytics | null>(null);
  const [warnings, setWarnings] = useState<OfficialWarning[]>([]);
  const [historicalRecords, setHistoricalRecords] = useState<HistoricalWaterlogging[]>([]);
  const [complaints, setComplaints] = useState<CivicComplaint[]>([]);
  const [duplicatePairs, setDuplicatePairs] = useState<DuplicateCandidatePair[]>([]);
  const [hotspots, setHotspots] = useState<HotspotCluster[]>([]);
  const [riskAssessments, setRiskAssessments] = useState<RiskAssessment[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [actions, setActions] = useState<DecisionAction[]>([]);
  const [climateScenarios, setClimateScenarios] = useState<ClimateScenario[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceStatus[]>([]);
  const [evaluationReport, setEvaluationReport] = useState<EvaluationReport | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Fetch all core datasets
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        healthRes,
        zonesRes,
        assetsRes,
        obsRes,
        analyticsRes,
        warnRes,
        histRes,
        compRes,
        dupRes,
        hotRes,
        riskRes,
        alertRes,
        actRes,
        climRes,
        dsRes,
        evalRes
      ] = await Promise.all([
        api.getHealth().catch(() => ({ data_mode: 'LIVE' })),
        api.getZones(selectedCity),
        api.getAssets(selectedCity),
        api.getRainfallObservations(selectedCity),
        api.getRainfallAnalytics(selectedCity),
        api.getOfficialWarnings(selectedCity),
        api.getHistoricalWaterlogging(selectedCity),
        api.getComplaints(selectedCity),
        api.getDuplicateCandidates(selectedCity),
        api.getHotspots(selectedCity),
        api.getRiskAssessments(selectedCity, riskMode),
        api.getAlerts(selectedCity),
        api.getActions(selectedCity),
        api.getClimateScenarios(selectedCity),
        api.getDataSources(),
        api.getEvaluationReport(selectedCity),
      ]);

      setDataMode((healthRes.data_mode as DataMode) ?? 'LIVE');
      setZones(zonesRes);
      setAssets(assetsRes);
      setObservations(obsRes);
      setAnalytics(analyticsRes);
      setWarnings(warnRes);
      setHistoricalRecords(histRes);
      setComplaints(compRes);
      setDuplicatePairs(dupRes);
      setHotspots(hotRes);
      setRiskAssessments(riskRes);
      setAlerts(alertRes);
      setActions(actRes);
      setClimateScenarios(climRes);
      setDataSources(dsRes);
      setEvaluationReport(evalRes);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Error connecting to MonsoonWatch backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) return;
    loadDashboardData();
  }, [selectedCity, riskMode, user]);

  useEffect(() => {
    if (workspace === 'citizen' && currentTab !== 'citizen-home' && currentTab !== 'risk-map' && currentTab !== 'alerts-actions') {
      setCurrentTab('citizen-home');
    }
    if (workspace === 'control-room' && currentTab === 'citizen-home') {
      setCurrentTab('command-center');
    }
  }, [workspace]);

  const handleSubmitComplaint = async (raw_text: string, landmark?: string) => {
    const res = await api.submitComplaint({ raw_text, landmark, city_id: selectedCity, reporter_email: user?.email });
    showToast(`Grievance #${res.tracking_number} ingested via ${res.language_detected}.`);
    // Refresh complaints, hotspots & duplicates
    const [cRes, dRes, hRes, rRes] = await Promise.all([
      api.getComplaints(selectedCity),
      api.getDuplicateCandidates(selectedCity),
      api.getHotspots(selectedCity),
      api.getRiskAssessments(selectedCity, riskMode),
    ]);
    setComplaints(cRes);
    setDuplicatePairs(dRes);
    setHotspots(hRes);
    setRiskAssessments(rRes);
    return res;
  };

  const handleResolveDuplicate = async (c1Id: number, c2Id: number, action: 'MERGE' | 'REJECT') => {
    await api.resolveDuplicate({ complaint_id_1: c1Id, complaint_id_2: c2Id, action });
    showToast(action === 'MERGE' ? 'Candidate complaints merged into linked incident.' : 'Records confirmed as distinct.');
    const [cRes, dRes] = await Promise.all([
      api.getComplaints(selectedCity),
      api.getDuplicateCandidates(selectedCity),
    ]);
    setComplaints(cRes);
    setDuplicatePairs(dRes);
  };

  const handleUpdateAction = async (actionId: number, status: string, assignedTo?: string, reason?: string) => {
    await api.updateAction(actionId, { status, assigned_to: assignedTo, reason });
    showToast(`Action #${actionId} updated to ${status}.`);
    const actRes = await api.getActions(selectedCity);
    setActions(actRes);
  };

  const handleAcknowledgeAction = async (actionId: number) => {
    await handleUpdateAction(actionId, 'ACKNOWLEDGED', 'Duty Officer Karthik', 'Acknowledged from Command Center');
  };

  const handleSimulateWhatIf = async (additionalRainMm: number, blockagePct: number) => {
    return api.simulateWhatIf({
      city_id: selectedCity,
      additional_rainfall_mm: additionalRainMm,
      drainage_blockage_pct: blockagePct,
    });
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#F4F7F5] flex items-center justify-center text-slate-500 gap-2">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
        Opening UrbanPulse…
      </div>
    );
  }

  if (!user) {
    return <LoginScreen />;
  }

  return (
    <div className={`min-h-screen flex flex-col font-sans selection:bg-emerald-500/30 ${workspace === 'citizen' ? 'bg-[#F4F7F5] text-slate-900' : 'bg-[#0B0F17] text-slate-100'}`}>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-emerald-500/60 text-emerald-300 text-xs px-4 py-2.5 rounded-lg shadow-xl flex items-center gap-2 animate-bounce">
          <ShieldAlert className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Navigation Bar */}
      <Navbar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        selectedCity={selectedCity}
        onCityChange={setSelectedCity}
        dataMode={dataMode}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {loading && (
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
            <span className="text-xs font-medium">{workspace === 'citizen' ? 'Loading your city…' : 'Synchronizing Urban Early Warning Feeds...'}</span>
          </div>
        )}

        {error && !loading && (
          <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/40 text-xs text-rose-300 flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>{error}</span>
            </div>
            <button
              onClick={loadDashboardData}
              className="bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 px-3 py-1 rounded transition cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && (
          <>
            {currentTab === 'citizen-home' && (
              <CitizenHomeView
                cityId={selectedCity}
                reporterEmail={user.email}
                complaints={complaints}
                warnings={warnings}
                onReportCreated={(complaint) => {
                  setComplaints((prev) => [complaint, ...prev]);
                  showToast(`Report ${complaint.tracking_number} filed.`);
                }}
              />
            )}

            {currentTab === 'command-center' && (
              <CommandCenterView
                analytics={analytics}
                warnings={warnings}
                riskAssessments={riskAssessments}
                hotspots={hotspots}
                actions={actions}
                complaints={complaints}
                onNavigateTab={setCurrentTab}
                onSelectZone={(zId) => setSelectedZoneId(zId)}
                onAcknowledgeAction={handleAcknowledgeAction}
              />
            )}

            {currentTab === 'risk-map' && (
              <div className={workspace === 'citizen' ? 'rounded-3xl bg-[#0B0F17] text-slate-100 p-3 overflow-hidden' : ''}>
              <UrbanRiskMapView
                zones={zones}
                assets={assets}
                observations={observations}
                historicalRecords={historicalRecords}
                complaints={complaints}
                hotspots={hotspots}
                riskAssessments={riskAssessments}
                selectedZoneId={selectedZoneId}
                onSelectZone={setSelectedZoneId}
              />
              </div>
            )}

            {currentTab === 'temporal-anomalies' && (
              <TemporalAnomalyExplorerView selectedCity={selectedCity} />
            )}

            {currentTab === 'cross-category' && (
              <CrossCategoryPatternsView selectedCity={selectedCity} />
            )}

            {currentTab === 'rainfall' && (
              <RainfallIntelligenceView
                observations={observations}
                analytics={analytics}
                warnings={warnings}
              />
            )}

            {currentTab === 'risk-engine' && (
              <RiskEngineView
                assessments={riskAssessments}
                currentMode={riskMode}
                onModeChange={setRiskMode}
                onSimulateWhatIf={handleSimulateWhatIf}
              />
            )}

            {currentTab === 'civic-intelligence' && (
              <CivicIntelligenceView
                complaints={complaints}
                duplicatePairs={duplicatePairs}
                onSubmitComplaint={handleSubmitComplaint}
                onResolveDuplicate={handleResolveDuplicate}
                onRefreshData={loadDashboardData}
              />
            )}

            {currentTab === 'hotspots-replay' && (
              <HotspotsReplayView hotspots={hotspots} />
            )}

            {currentTab === 'alerts-actions' && (
              <div className={workspace === 'citizen' ? 'rounded-3xl bg-[#0B0F17] text-slate-100 p-3 overflow-hidden' : ''}>
                {workspace === 'citizen' && (
                  <p className="text-sm text-slate-300 px-2 pb-3">These are the jobs city teams are already looking at. You do not need to manage them.</p>
                )}
                <AlertsActionsView
                  alerts={alerts}
                  actions={actions}
                  onUpdateAction={handleUpdateAction}
                />
              </div>
            )}

            {currentTab === 'climate' && (
              <ClimateStressView scenarios={climateScenarios} />
            )}

            {currentTab === 'datasources' && (
              <DataSourcesEvaluationView
                dataSources={dataSources}
                evaluationReport={evaluationReport}
              />
            )}
          </>
        )}
      </main>

      <AIAssistant cityId={selectedCity} />

      <footer className={`border-t py-4 px-6 text-xs flex flex-col sm:flex-row items-center justify-between gap-3 ${workspace === 'citizen' ? 'border-emerald-100 bg-white text-slate-500' : 'border-slate-800 bg-[#0B0F17] text-slate-500'}`}>
        <div className="flex items-center gap-2">
          <span className="font-semibold">UrbanPulse</span>
          <span>•</span>
          <span>{workspace === 'citizen' ? 'Snap a photo. We file the city report.' : 'Urban issue intelligence & early warning'}</span>
        </div>
        {workspace === 'control-room' && (
          <div className="flex items-center gap-4 text-[11px]">
            <span>Data: {dataMode}</span>
            <span>•</span>
            <span>MAD + Poisson anomaly detection</span>
            <span>•</span>
            <span>Human oversight required</span>
          </div>
        )}
      </footer>
    </div>
  );
}

export default App;
