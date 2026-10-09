import React, { useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  Polygon,
  useMap
} from 'react-leaflet';
import L from 'leaflet';
import {
  Layers,
  Filter,
  Info,
  ShieldAlert,
  CloudRain,
  Flame,
  CheckCircle2,
  X,
  FileText
} from 'lucide-react';
import {
  Zone,
  VulnerableAsset,
  RainfallObservation,
  HistoricalWaterlogging,
  CivicComplaint,
  HotspotCluster,
  RiskAssessment
} from '../types';

// Custom Map center helper
const ChangeMapView = ({ center, zoom }: { center: [number, number]; zoom: number }) => {
  const map = useMap();
  map.setView(center, zoom);
  return null;
};

// Custom SVG-based Leaflet DivIcons to avoid broken asset URL issues in Vite
const createSvgIcon = (color: string, label: string) => {
  return L.divIcon({
    className: 'custom-leaflet-icon',
    html: `
      <div style="background-color: ${color}; width: 22px; height: 22px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold;">
        ${label}
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
};

const subwayIcon = createSvgIcon('#EF4444', 'S');
const pumpIcon = createSvgIcon('#06B6D4', 'P');
const hospitalIcon = createSvgIcon('#10B981', 'H');
const complaintIcon = createSvgIcon('#F59E0B', '!');
const stationIcon = createSvgIcon('#3B82F6', 'R');
const historicalIcon = createSvgIcon('#A855F7', 'H');

interface UrbanRiskMapViewProps {
  zones: Zone[];
  assets: VulnerableAsset[];
  observations: RainfallObservation[];
  historicalRecords: HistoricalWaterlogging[];
  complaints: CivicComplaint[];
  hotspots: HotspotCluster[];
  riskAssessments: RiskAssessment[];
  selectedZoneId: string | null;
  onSelectZone: (zoneId: string | null) => void;
}

export const UrbanRiskMapView: React.FC<UrbanRiskMapViewProps> = ({
  zones,
  assets,
  observations,
  historicalRecords,
  complaints,
  hotspots,
  riskAssessments,
  selectedZoneId,
  onSelectZone,
}) => {
  const INDIA_BOUNDS: [[number, number], [number, number]] = [[6.4, 68.0], [35.7, 97.5]];
  // Layer visibility toggles
  const [showWards, setShowWards] = useState(true);
  const [showStations, setShowStations] = useState(true);
  const [showAssets, setShowAssets] = useState(true);
  const [showComplaints, setShowComplaints] = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);
  const [showHistorical, setShowHistorical] = useState(true);

  // Risk filter
  const [riskFilter, setRiskFilter] = useState<string>('ALL');

  // Selected object for evidence drawer
  const [selectedAssessment, setSelectedAssessment] = useState<RiskAssessment | null>(null);

  // Map risk score to color
  const getRiskColor = (score: number) => {
    if (score >= 80) return '#EF4444'; // Red
    if (score >= 65) return '#F97316'; // Orange
    if (score >= 45) return '#F59E0B'; // Amber
    if (score >= 25) return '#10B981'; // Green
    return '#059669';
  };

  // Map assessment lookup
  const assessmentMap = new Map<string, RiskAssessment>();
  riskAssessments.forEach((r) => assessmentMap.set(r.zone_id, r));

  const handleZoneClick = (zoneId: string) => {
    onSelectZone(zoneId);
    const assessment = assessmentMap.get(zoneId);
    if (assessment) {
      setSelectedAssessment(assessment);
    }
  };

  // Filtered zones based on category
  const filteredZones = zones.filter((z) => {
    if (riskFilter === 'ALL') return true;
    const a = assessmentMap.get(z.id);
    return a?.risk_category === riskFilter;
  });

  return (
    <div className="relative h-[calc(100vh-140px)] min-h-[600px] w-full flex flex-col rounded-xl overflow-hidden border border-slate-800 bg-[#0B0F17]">
      {/* Top Map Toolbar: Layer Toggles & Filter */}
      <div className="p-3 bg-slate-900/90 backdrop-blur border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 z-10">
        <div className="w-full flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-white">Chennai impact map</h2>
            <p className="text-[11px] text-slate-400">Select a ward, hotspot, or asset to see the evidence behind the risk.</p>
          </div>
          <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-slate-800 px-2.5 py-1 text-[10px] text-slate-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Click any ward for details
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-500/10 px-2.5 py-1 text-[10px] text-blue-300">
            India-only view
          </span>
        </div>
        {/* Layer Toggles */}
        <div className="flex items-center gap-1.5 flex-wrap text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1 mr-1">
            <Layers className="w-3.5 h-3.5 text-emerald-400" /> Layers:
          </span>
          <button
            onClick={() => setShowWards(!showWards)}
            className={`px-2 py-1 rounded border transition cursor-pointer ${
              showWards ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            Ward Risk
          </button>
          <button
            onClick={() => setShowHotspots(!showHotspots)}
            className={`px-2 py-1 rounded border transition cursor-pointer ${
              showHotspots ? 'bg-rose-500/20 border-rose-500/50 text-rose-300' : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            Hotspots ({hotspots.length})
          </button>
          <button
            onClick={() => setShowAssets(!showAssets)}
            className={`px-2 py-1 rounded border transition cursor-pointer ${
              showAssets ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300' : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            Assets ({assets.length})
          </button>
          <button
            onClick={() => setShowStations(!showStations)}
            className={`px-2 py-1 rounded border transition cursor-pointer ${
              showStations ? 'bg-blue-500/20 border-blue-500/50 text-blue-300' : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            Rain Gauges ({observations.length})
          </button>
          <button
            onClick={() => setShowComplaints(!showComplaints)}
            className={`px-2 py-1 rounded border transition cursor-pointer ${
              showComplaints ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            Complaints ({complaints.length})
          </button>
          <button
            onClick={() => setShowHistorical(!showHistorical)}
            className={`px-2 py-1 rounded border transition cursor-pointer ${
              showHistorical ? 'bg-purple-500/20 border-purple-500/50 text-purple-300' : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            Historical ({historicalRecords.length})
          </button>
        </div>

        {/* Risk Filter dropdown */}
        <div className="flex items-center gap-2 text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-400">Risk Filter:</span>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-2 py-1 focus:outline-none cursor-pointer"
          >
            <option value="ALL">All Categories</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High Only</option>
            <option value="ELEVATED">Elevated</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Main Map Viewport */}
      <div className="relative flex-1 w-full h-full">
        <MapContainer
          center={[13.0827, 80.2707]}
          zoom={11}
          minZoom={4}
          maxBounds={INDIA_BOUNDS}
          maxBoundsViscosity={1}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%', background: '#0B0F17' }}
        >
          <ChangeMapView center={[13.0827, 80.2707]} zoom={11} />
          {/* OpenStreetMap tiles keep local demos key-free and reliable. */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* 1. Ward Risk Polygons */}
          {showWards &&
            filteredZones.map((z) => {
              const assessment = assessmentMap.get(z.id);
              const score = assessment?.overall_risk_score ?? 40;
              const color = getRiskColor(score);
              const isSelected = selectedZoneId === z.id;

              // Polygon coordinates from boundary_geojson or approximated square
              const d = 0.018;
              const positions: [number, number][] = [
                [z.center_lat - d, z.center_lon - d],
                [z.center_lat + d, z.center_lon - d],
                [z.center_lat + d, z.center_lon + d],
                [z.center_lat - d, z.center_lon + d],
              ];

              return (
                <Polygon
                  key={z.id}
                  positions={positions}
                  pathOptions={{
                    color: isSelected ? '#10B981' : color,
                    weight: isSelected ? 3 : 1.5,
                    fillColor: color,
                    fillOpacity: isSelected ? 0.45 : 0.25,
                  }}
                  eventHandlers={{
                    click: () => handleZoneClick(z.id),
                  }}
                >
                  <Popup>
                    <div className="text-xs space-y-1">
                      <div className="font-bold text-white">{z.name} (Zone {z.zone_number})</div>
                      <div>Modeled Risk Score: <strong style={{ color }}>{score}/100</strong></div>
                      <div>Category: <strong>{assessment?.risk_category ?? 'MODERATE'}</strong></div>
                      <div>Mean Elevation: {z.mean_elevation_m}m MSL</div>
                      <div>Impervious Surface: {Math.round(z.impervious_fraction * 100)}%</div>
                      <button
                        onClick={() => handleZoneClick(z.id)}
                        className="mt-2 text-emerald-400 hover:underline block cursor-pointer"
                      >
                        Open Full Evidence Panel &rarr;
                      </button>
                    </div>
                  </Popup>
                </Polygon>
              );
            })}

          {/* 2. Hotspot Cluster Circles */}
          {showHotspots &&
            hotspots.map((h) => (
              <Circle
                key={h.id}
                center={[h.center_lat, h.center_lon]}
                radius={h.radius_meters}
                pathOptions={{
                  color: '#EF4444',
                  fillColor: '#EF4444',
                  fillOpacity: 0.35,
                  dashArray: '4, 4',
                }}
              >
                <Popup>
                  <div className="text-xs space-y-1">
                    <div className="font-bold text-rose-400 flex items-center gap-1">
                      <Flame className="w-3.5 h-3.5" /> {h.cluster_name}
                    </div>
                    <div>Status: <span className="font-bold text-rose-400">{h.status}</span></div>
                    <div>Citizen Grievances: <strong>{h.complaint_count} reports</strong></div>
                    <div>Anomaly Ratio: <strong>{h.anomaly_ratio}x higher than baseline</strong></div>
                    <p className="text-slate-400 mt-1">{h.rainfall_evidence}</p>
                  </div>
                </Popup>
              </Circle>
            ))}

          {/* 3. Vulnerable Assets Markers */}
          {showAssets &&
            assets.map((a) => {
              const icon = a.asset_type === 'SUBWAY' ? subwayIcon : a.asset_type === 'PUMPING_STATION' ? pumpIcon : hospitalIcon;
              return (
                <Marker key={a.id} position={[a.lat, a.lon]} icon={icon}>
                  <Popup>
                    <div className="text-xs space-y-1">
                      <div className="font-bold text-white">{a.name}</div>
                      <div className="text-slate-300">Type: <span className="font-semibold">{a.asset_type}</span></div>
                      <div>Elevation: {a.elevation_m}m MSL</div>
                      <div>Threshold: {a.critical_threshold_mm} mm rainfall</div>
                      <p className="text-slate-400 mt-1">{a.description}</p>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {/* 4. Rain Gauges */}
          {showStations &&
            observations.map((o) => (
              <Marker key={o.id} position={[13.067, 80.243]} icon={stationIcon}>
                <Popup>
                  <div className="text-xs space-y-1">
                    <div className="font-bold text-blue-400 flex items-center gap-1">
                      <CloudRain className="w-3.5 h-3.5" /> {o.station_name}
                    </div>
                    <div>24h Total: <strong>{o.rainfall_24h_mm} mm</strong></div>
                    <div>3h Burst: <strong>{o.rainfall_3h_mm} mm</strong></div>
                    <div>Source: {o.source}</div>
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* 5. Civic Complaints */}
          {showComplaints &&
            complaints
              .filter((c): c is typeof c & { lat: number; lon: number } => c.lat != null && c.lon != null)
              .map((c) => (
                <Marker key={c.id} position={[c.lat, c.lon]} icon={complaintIcon}>
                <Popup>
                  <div className="text-xs space-y-1">
                    <div className="font-bold text-amber-400">Grievance #{c.tracking_number}</div>
                    <div className="text-white font-medium">{c.landmark ?? 'Reported Point'}</div>
                    <p className="text-slate-300">{c.raw_text}</p>
                    <div className="flex gap-2 text-[10px] text-slate-400">
                      <span>Category: {c.issue_category}</span>
                      <span>Severity: {c.severity_score}/5</span>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* 6. Historical Records */}
          {showHistorical &&
            historicalRecords.map((h) => (
              <Marker key={h.id} position={[h.lat, h.lon]} icon={historicalIcon}>
                <Popup>
                  <div className="text-xs space-y-1">
                    <div className="font-bold text-purple-400">Historical Inundation Ground Truth</div>
                    <div className="text-white font-medium">{h.location_name}</div>
                    <div>Event: <strong>{h.event_date}</strong></div>
                    <div>Recorded Water Depth: <strong>{h.flood_depth_cm} cm</strong></div>
                    <p className="text-slate-400">{h.disruption_type}</p>
                  </div>
                </Popup>
              </Marker>
            ))}
        </MapContainer>

        {/* Legend Overlay */}
        <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur border border-slate-800 rounded-lg p-3 text-xs z-10 shadow-lg hidden sm:block">
          <div className="font-bold text-slate-200 mb-2 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-emerald-400" /> Map Legend
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] text-slate-300">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500" />
              <span>Critical Risk (&ge;80)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-orange-500" />
              <span>High Risk (65-79)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500" />
              <span>Elevated (45-64)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-500" />
              <span>Moderate/Low (&lt;45)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full border border-dashed border-rose-400 bg-rose-500/30" />
              <span>Emerging Hotspot</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-600 text-[8px] text-white flex items-center justify-center font-bold">S</span>
              <span>Subway Underpass</span>
            </div>
          </div>
        </div>
      </div>

      {/* Slide-out Evidence & AI Explanation Panel (Module K) */}
      {selectedAssessment && (
        <div className="absolute top-0 right-0 h-full w-full sm:w-[420px] bg-slate-900/95 backdrop-blur border-l border-slate-800 p-5 z-20 overflow-y-auto shadow-2xl transition">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-base text-white">Location Evidence Panel</h3>
            </div>
            <button
              onClick={() => setSelectedAssessment(null)}
              className="text-slate-400 hover:text-white p-1 rounded-md transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-4 space-y-4 text-xs">
            {/* Zone header & score */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-400 text-[10px] uppercase font-semibold">Selected Locality</span>
                <h4 className="text-sm font-bold text-white">{selectedAssessment.zone_name ?? selectedAssessment.zone_id}</h4>
              </div>
              <div className="text-right">
                <span
                  className="text-xl font-bold"
                  style={{ color: getRiskColor(selectedAssessment.overall_risk_score) }}
                >
                  {selectedAssessment.overall_risk_score}/100
                </span>
                <div className="text-[10px] font-semibold text-slate-300 uppercase">
                  {selectedAssessment.risk_category} RISK
                </div>
              </div>
            </div>

            {/* Contributing Factor Breakdown */}
            <div>
              <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-emerald-400" />
                Contributing Physical Factors
              </h4>
              <div className="space-y-2">
                {selectedAssessment.contributing_factors?.map((f, i) => (
                  <div key={i} className="p-2.5 rounded bg-slate-950/70 border border-slate-800">
                    <div className="flex items-center justify-between font-medium text-slate-200">
                      <span>{f.factor_name}</span>
                      <span className="text-emerald-400">
                        {f.score} / {f.max_score} pts
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{f.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence & Data Completeness */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <span className="text-slate-400 text-[10px]">Confidence Index</span>
                <div className="text-base font-bold text-white">
                  {Math.round(selectedAssessment.confidence_score * 100)}%
                </div>
              </div>
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                <span className="text-slate-400 text-[10px]">Data Completeness</span>
                <div className="text-base font-bold text-emerald-400">
                  {selectedAssessment.data_completeness_pct}%
                </div>
              </div>
            </div>

            {/* Recommended Human Verification Action */}
            <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/40">
              <span className="text-emerald-400 font-bold uppercase text-[10px] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Recommended Human Verification
              </span>
              <p className="text-slate-200 mt-1 leading-relaxed">
                {selectedAssessment.recommended_action}
              </p>
            </div>

            {/* Scientific Limitations & Data Gaps */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-400">
              <span className="text-slate-300 font-semibold text-[10px] uppercase">
                Methodological Limitations
              </span>
              <p className="mt-1 text-[11px] leading-relaxed">
                {selectedAssessment.limitations_text}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
