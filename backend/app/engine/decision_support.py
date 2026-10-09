"""
Decision Support and Action Prioritization Module for MonsoonWatch India.
Maintains a transparent, multi-criteria operational queue for municipal engineers,
disaster response coordinators, and field supervisors.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class DecisionSupportEngine:
    """Ranks and manages human operational decisions during flood events."""

    @classmethod
    def prioritize_actions(
        cls,
        city_id: str,
        risk_assessments: List[Dict[str, Any]],
        assets: List[Dict[str, Any]],
        complaints: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculates Priority Score (0 - 100) using transparent formula:
        Priority = 0.35 * RiskScore + 0.30 * AssetCriticality + 0.20 * CivicComplaints + 0.15 * TimeUrgency
        """
        actions = []
        action_id = 1

        # Map zone complaints count
        zone_complaint_counts: Dict[str, int] = {}
        for c in complaints:
            z = c.get("zone_id")
            if z:
                zone_complaint_counts[z] = zone_complaint_counts.get(z, 0) + 1

        # Map zone risk scores
        zone_risk_map = {r["zone_id"]: r for r in risk_assessments}

        # 1. Critical Asset Actions (Subways, Underpasses, Pumping Stations)
        for a in assets:
            z_id = a.get("zone_id")
            z_risk = zone_risk_map.get(z_id, {})
            risk_score = z_risk.get("overall_risk_score", 40.0)
            c_count = zone_complaint_counts.get(z_id, 0)

            # Asset criticality weight
            asset_type = a.get("asset_type", "OTHER")
            if asset_type in ["SUBWAY", "UNDERPASS"]:
                asset_crit = 95.0
                action_type = "INSPECT_SUBWAY"
                desc = f"Inspect flood barriers and automated sumps at {a['name']}. Restrict vehicular access if water level exceeds 15cm."
            elif asset_type == "PUMPING_STATION":
                asset_crit = 90.0
                action_type = "CLEAR_PUMP_STATION"
                desc = f"Verify diesel generator fuel and check inlet screens for plastic blockage at {a['name']}."
            elif asset_type == "CANAL_OUTFALL":
                asset_crit = 85.0
                action_type = "DESILT_CANAL_OUTLET"
                desc = f"Ensure tidal gates are operational and clear floating hyacinth at {a['name']}."
            elif asset_type == "HOSPITAL":
                asset_crit = 100.0
                action_type = "DEPLOY_MOBILE_PUMP"
                desc = f"Pre-position 100-HP dewatering trailer at emergency ambulance entrance of {a['name']}."
            else:
                asset_crit = 60.0
                action_type = "DISPATCH_DRAINAGE_CREW"
                desc = f"Field inspection of drainage line near {a['name']}."

            complaint_factor = min(100.0, c_count * 12.0)
            urgency = 90.0 if risk_score >= 70.0 else 60.0

            priority_score = round(
                0.35 * risk_score + 0.30 * asset_crit + 0.20 * complaint_factor + 0.15 * urgency,
                1
            )

            actions.append({
                "id": action_id,
                "city_id": city_id,
                "zone_id": z_id,
                "asset_id": a.get("id"),
                "action_type": action_type,
                "priority_score": priority_score,
                "priority_rank": 0,  # calculated after sort
                "location_name": a["name"],
                "description": desc,
                "evidence_basis": (
                    f"Zone Risk: {risk_score}/100, Asset Criticality: {asset_crit}/100, "
                    f"Nearby Active Complaints: {c_count}. Elevation: {a.get('elevation_m', 5.0)}m MSL."
                ),
                "status": "PENDING_REVIEW",
                "assigned_to": None,
                "assigned_at": None,
                "updated_at": datetime.utcnow()
            })
            action_id += 1

        # Sort descending by priority score and assign ranks
        actions.sort(key=lambda x: x["priority_score"], reverse=True)
        for rank, act in enumerate(actions, start=1):
            act["priority_rank"] = rank

        return actions
