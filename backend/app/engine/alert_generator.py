"""
Explainable Risk Alert Generator for MonsoonWatch India.
Enforces strict separation across three alert classes:
1. Official Weather Alerts (IMD)
2. Model-Generated Impact Risk Signals
3. Civic Intelligence Anomaly Alerts
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta


class AlertGenerator:
    """Generates structured, evidence-grounded alerts for operational personnel."""

    @classmethod
    def generate_alerts(
        cls,
        city_id: str,
        official_warnings: List[Dict[str, Any]],
        risk_assessments: List[Dict[str, Any]],
        hotspots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        alerts = []
        alert_id = 1

        # 1. Official Weather Alerts (attributed directly to IMD)
        for w in official_warnings:
            alerts.append({
                "id": alert_id,
                "city_id": city_id,
                "zone_id": None,
                "alert_class": "OFFICIAL_WEATHER_ALERT",
                "severity": "CRITICAL" if w["warning_level"] in ["RED", "ORANGE"] else "WARNING",
                "title": f"[IMD {w['warning_level']} Alert] {w['headline']}",
                "location_name": f"{city_id.title()} Metropolitan Area",
                "valid_from": w.get("issued_at", datetime.utcnow()),
                "valid_to": w.get("valid_until", datetime.utcnow() + timedelta(hours=24)),
                "evidence_text": f"Official bulletin issued by {w.get('issuing_authority')}: {w.get('description')}",
                "contributing_factors": {"bulletin_level": w["warning_level"], "authority": w.get("issuing_authority")},
                "data_gaps": "IMD regional radar and automated weather stations. Radar coverage optimal within 150km radius.",
                "recommended_action": w.get("recommended_actions") or "Advise coastal and low-lying municipal teams to remain on standby.",
                "source_reference": w.get("source_url") or "India Meteorological Department (mausam.imd.gov.in)",
                "created_at": datetime.utcnow()
            })
            alert_id += 1

        # 2. Model-Generated Impact Risk Signals (for zones with Elevated, High, or Critical risk)
        for r in risk_assessments:
            score = r.get("overall_risk_score", 0.0)
            category = r.get("risk_category", "LOW")
            if category in ["HIGH", "CRITICAL"]:
                zone_name = r.get("zone_name", r.get("zone_id", "Ward"))
                factors = r.get("contributing_factors", [])
                top_factor_desc = factors[0].get("description") if factors else "Elevated forecast runoff"

                alerts.append({
                    "id": alert_id,
                    "city_id": city_id,
                    "zone_id": r.get("zone_id"),
                    "alert_class": "MODEL_IMPACT_RISK",
                    "severity": "CRITICAL" if category == "CRITICAL" else "WARNING",
                    "title": f"Urban Waterlogging Risk Signal: {zone_name} ({category})",
                    "location_name": zone_name,
                    "valid_from": datetime.utcnow(),
                    "valid_to": datetime.utcnow() + timedelta(hours=12),
                    "evidence_text": (
                        f"Modeled impact score is {score}/100. Primary driver: {top_factor_desc}. "
                        f"Data completeness is {r.get('data_completeness_pct', 90)}% with confidence {r.get('confidence_score', 0.85)}."
                    ),
                    "contributing_factors": {"factors": factors[:3]},
                    "data_gaps": r.get("limitations_text") or "Localized micro-drainage dimensions unverified by sensor.",
                    "recommended_action": r.get("recommended_action") or "Pre-position mobile pumps and clear inlet grates.",
                    "source_reference": f"MonsoonWatch Impact-Risk Engine ({r.get('version', 'v1.2.0')})",
                    "created_at": datetime.utcnow()
                })
                alert_id += 1

        # 3. Civic Intelligence Anomaly Alerts
        for h in hotspots:
            if h.get("status") == "EMERGING":
                alerts.append({
                    "id": alert_id,
                    "city_id": city_id,
                    "zone_id": h.get("zone_id"),
                    "alert_class": "CIVIC_ANOMALY",
                    "severity": "WARNING",
                    "title": f"Emerging Complaint Cluster: {h['cluster_name']}",
                    "location_name": h["cluster_name"],
                    "valid_from": datetime.utcnow(),
                    "valid_to": datetime.utcnow() + timedelta(hours=6),
                    "evidence_text": (
                        f"Detected {h['complaint_count']} citizen reports within {int(h['radius_meters'])}m. "
                        f"Anomaly ratio is {h['anomaly_ratio']}x higher than baseline rate ({h['baseline_normal_count']} normal)."
                    ),
                    "contributing_factors": {"anomaly_ratio": h["anomaly_ratio"], "reports": h["complaint_count"]},
                    "data_gaps": "Citizen reports represent reporting activity, requiring ground crew verification.",
                    "recommended_action": f"Dispatch rapid response van to inspect {h['cluster_name']} and verify drainage flow.",
                    "source_reference": "MonsoonWatch Civic Complaint Cluster Stream",
                    "created_at": datetime.utcnow()
                })
                alert_id += 1

        return alerts
