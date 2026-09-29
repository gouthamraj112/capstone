import json
import re
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import run
from app.core.database import db
from app.models.query import QueryRequest, QueryResponse
from app.services.llm_service import explain, numbers_are_evidence_backed

router = APIRouter()


# ─── Dataset Citation Registry ────────────────────────────────────────────────
_DATASET_REGISTRY = {
    "energy_data": {
        "name": "UCI Household Power Consumption",
        "collection": "energy_data",
        "description": "Minute-level electrical measurements from a single household in Sceaux, France (2006–2010).",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption",
        "fields": ["Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity"],
        "granularity": "1-minute intervals",
        "icon": "⚡",
    },
    "hourly_energy": {
        "name": "Hourly Aggregated Demand",
        "collection": "hourly_energy",
        "description": "Pre-aggregated hourly demand summaries derived from the raw minute-level household power data.",
        "source": "Internal – derived from UCI Household Power Consumption",
        "url": None,
        "fields": ["demand", "active_power_sum", "valid_samples"],
        "granularity": "1-hour intervals",
        "icon": "📊",
    },
    "anomalies": {
        "name": "Detected Anomaly Records",
        "collection": "anomalies",
        "description": "Flagged consumption anomalies produced by the rolling robust baseline algorithm (MAD-based z-score).",
        "source": "Internal – anomaly detection pipeline",
        "url": None,
        "fields": ["actual_value", "expected_value", "deviation", "severity"],
        "granularity": "Event-based",
        "icon": "🚨",
    },
    "daily_energy": {
        "name": "Daily Energy Summaries",
        "collection": "daily_energy",
        "description": "Day-level aggregates of total consumption, average demand, and peak demand.",
        "source": "Internal – derived from UCI Household Power Consumption",
        "url": None,
        "fields": ["total_kwh", "average_demand", "peak_demand"],
        "granularity": "1-day intervals",
        "icon": "📅",
    },
}


def build_citations(intent: str, energy_data: dict, anomaly_data: dict, forecast_data: dict, forecast_items: list) -> list[dict]:
    """Return dataset citations relevant to the current query intent and available data."""
    cited = set()

    # Always cite the primary energy source when we have any energy readings
    if energy_data.get("observations"):
        if energy_data.get("top_hours") or intent in ("hourly_analysis", "peak_demand", "insights",
                                                       "evening_increase", "weekday_weekend_comparison"):
            cited.add("hourly_energy")
        cited.add("energy_data")

    if anomaly_data.get("has_data") or intent == "anomaly_detection":
        cited.add("anomalies")
        cited.add("energy_data")

    if forecast_items or intent == "forecast":
        cited.add("hourly_energy")
        cited.add("energy_data")

    if not cited and energy_data:
        cited.add("energy_data")

    return [_DATASET_REGISTRY[k] for k in ("energy_data", "hourly_energy", "anomalies", "daily_energy") if k in cited]


def compute_per_query_evaluation(answer: str, evidence: list, confidence: float, intent: str, agents_used: list) -> dict:
    """Compute lightweight per-response quality metrics."""
    evidence_count = len(evidence)
    is_grounded = numbers_are_evidence_backed(answer, evidence) if evidence else True
    # Relevance: confidence & evidence availability
    relevance_score = round(min(1.0, confidence + (0.1 if evidence_count > 0 else 0)), 3)
    # Completeness: how many agents contributed data
    data_agents = [a for a in agents_used if a not in ("guardrail_agent",)]
    completeness = round(min(1.0, len(data_agents) / 3), 3) if data_agents else 0.0
    # Evidence density
    evidence_density = "High" if evidence_count >= 5 else "Medium" if evidence_count >= 2 else "Low"
    return {
        "confidence": round(confidence, 3),
        "evidence_count": evidence_count,
        "evidence_density": evidence_density,
        "is_grounded": is_grounded,
        "relevance_score": relevance_score,
        "completeness_score": completeness,
        "agents_used_count": len(agents_used),
        "intent_detected": intent,
        "quality": "High" if (is_grounded and confidence >= 0.7 and evidence_count >= 3)
                   else "Medium" if (is_grounded and confidence >= 0.4)
                   else "Low",
    }


import unicodedata


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if not (unicodedata.category(c) == "Mn" and 0x0300 <= ord(c) <= 0x036F)
    )


def detect_language(text: str, preferred: str = "en") -> str:
    if preferred and preferred in {"es", "fr", "de", "zh", "hi"}:
        return preferred
    t = strip_accents(text.lower())
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return "zh"
    if any('\u0900' <= char <= '\u097f' for char in text):
        return "hi"
    if "\u00bf" in text or any(w in t for w in ["que ", "cual", "cuales", "demanda maxima", "horas tienen", "consumo", "pronostico", "fin de semana", "aumento", "inusual"]):
        return "es"
    if any(w in t for w in ["quelle ", "quelles ", "quel ", "demande de pointe", "pic ", "pic d", "prevision", "prochain", "inhabituel", "consommation"]):
        return "fr"
    if any(w in t for w in ["welche stunden", "hochste", "spitzenbedarf", "stromverbrauch", "prognose", "ungewohnlich", "was war", "spitzen"]):
        return "de"
    return "en"


def classify(question: str) -> tuple[str, int]:
    q = strip_accents(question.lower())
    forecast_kw = ("forecast", "expected demand", "next ", "pronost", "previs", "prochain", "prognose", "vorhersage", "预测", "预期", "未来", "पूर्वानुमान")
    if any(x in q for x in forecast_kw):
        match = re.search(r"(\d+)\s*(?:hours?|horas?|heures?|stunden?|小时|घंटे)?", q)
        return "forecast", min(168, max(1, int(match.group(1)))) if match and match.group(1) else 6
    if any(x in q for x in ("weekday", "weekend", "fin de semana", "laboral", "semaine", "wochenende", "werktag", "周末", "工作日", "सप्ताहांत")):
        return "weekday_weekend_comparison", 6
    if any(x in q for x in ("evening", "increase", "tarde", "noche", "aumento", "hausse", "soir", "abend", "anstieg", "晚上", "傍晚", "शाम", "बढ़ोतरी")):
        return "evening_increase", 6
    if any(x in q for x in ("anomal", "unusual", "inusual", "atipico", "inhabituel", "ungewohnlich", "异常", "असामान्य")):
        return "anomaly_detection", 6

    causal_markers = ("why", "reason", "cause", "causes", "because", "explain", "explanation", "due to", "higher than", "more electricity", "higher demand", "more demand", "more usage", "using more", "consume more")
    peak_usage_markers = ("peak", "peak hour", "peak hours", "highest demand", "rush hour", "high demand", "demand spike", "electricity usage", "electricity consumption", "power usage", "consumption")
    evening_markers = ("evening", "night", "after work", "dusk", "nighttime", "late afternoon", "18:00", "19:00", "20:00", "21:00", "pm")
    if any(marker in q for marker in causal_markers) and any(marker in q for marker in peak_usage_markers):
        if any(marker in q for marker in evening_markers) or "peak hour" in q or "peak hours" in q:
            return "evening_increase", 6
        return "insights", 6

    if any(x in q for x in ("peak demand", "peak electricity", "demand during the peak", "demanda maxima", "demande de pointe", "spitzenbedarf")):
        return "peak_demand", 6
    if any(x in q for x in ("hour", "hora", "heure", "stunde", "小时", "घंटे")):
        return "hourly_analysis", 6
    if any(x in q for x in ("peak", "highest", "maxim", "pico", "pic", "pointe", "crete", "spitze", "hochst", "峰值", "最高", "चरम")):
        return "peak_demand", 6
    return "insights", 6


def format_localized_fallback(lang: str, intent: str, energy_data: dict, anomaly_data: dict, forecast_data: dict, forecast_items: list, decision_data: dict, has_data: bool) -> str:
    if not has_data:
        if energy_data.get("analysis_day"):
            return f"No energy readings are available for {energy_data['analysis_day']} in the dataset."
        templates = {
            "es": "Aún no hay lecturas de energía disponibles. Ingeste el conjunto de datos de energía del hogar para generar resultados basados en evidencia.",
            "fr": "Aucune lecture d'énergie n'est encore disponible. Chargez les données du foyer pour générer des résultats étayés.",
            "de": "Noch keine Energiedaten verfügbar. Bitte laden Sie den Datensatz, um evidenzbasierte Ergebnisse zu erhalten.",
            "zh": "尚无可用的能源读数。请导入家庭用电数据集以生成有依据的分析结果。",
            "hi": "अभी तक कोई ऊर्जा डेटा उपलब्ध नहीं है। साक्ष्य-आधारित परिणाम उत्पन्न करने के लिए डेटासेट लोड करें।",
            "en": "No energy readings are available yet. Ingest the household power dataset to generate evidence-backed results."
        }
        return templates.get(lang, templates["en"])

    if lang == "en" and energy_data.get("analysis_day") and energy_data.get("submetering_period_average"):
        profile = energy_data["submetering_period_average"]
        kitchen = profile.get("Sub_metering_1")
        laundry = profile.get("Sub_metering_2")
        hvac = profile.get("Sub_metering_3")
        driver = energy_data.get("dominant_period_submeter", {}).get("label")
        if all(value is not None for value in (kitchen, laundry, hvac)) and driver:
            return (f"For {energy_data['analysis_day']}, average household demand was {energy_data.get('average_demand')} kW "
                    f"and the highest recorded demand was {energy_data.get('peak_demand')} kW. Average sub-meter readings that day were "
                    f"kitchen {kitchen} Wh per minute, laundry {laundry} Wh per minute, and heating/AC {hvac} Wh per minute. "
                    f"{driver} had the highest sub-meter reading, so it was the largest measured contributor on that day. "
                    "These readings identify the strongest sub-meter category; they do not prove a specific appliance caused the increase.")

    if intent == "forecast":
        n = len(forecast_items)
        if not forecast_items:
            err = forecast_data.get('error', 'not enough historical readings')
            return f"Forecast unavailable: {err}"
        if lang == "es":
            return f"Se generó un pronóstico estacional de {n} horas basado en el período completo de 24 horas más reciente."
        if lang == "fr":
            return f"Prévision saisonnière sur {n} heures générée à partir des 24 dernières heures observées."
        if lang == "de":
            return f"Saisonale {n}-Stunden-Prognose basierend auf dem letzten vollständigen 24-Stunden-Profil generiert."
        if lang == "zh":
            return f"根据最近完整的24小时数据生成了未来 {n} 小时的季节性预测。"
        if lang == "hi":
            return f"पिछले 24 घंटों की प्रोफाइल के आधार पर अगले {n} घंटे का पूर्वानुमान उत्पन्न किया गया।"
        return f"Generated a {n}-hour seasonal-naive forecast from the latest complete 24-hour period."

    if intent == "anomaly_detection":
        count = anomaly_data.get("count", 0)
        if lang == "es":
            return f"Se detectaron {count} periodos inusuales utilizando la línea base móvil robusta." if count else "No se observaron anomalías en los datos analizados."
        if lang == "fr":
            return f"{count} périodes inhabituelles détectées à l'aide de la référence mobile robuste." if count else "Aucune anomalie détectée."
        if lang == "de":
            return f"{count} ungewöhnliche Verbrauchsperioden anhand der robusten Baseline erkannt." if count else "Keine Anomalien erkannt."
        if lang == "zh":
            return f"使用滑动基线检测到 {count} 个异常用电时段。" if count else "未检测到用电异常。"
        if lang == "hi":
            return f"रोबस्ट बेसलाइन का उपयोग करके {count} असामान्य अवधियों का पता लगाया गया।" if count else "कोई असामान्यता नहीं पाई गई।"
        return f"Detected {count} unusual periods using the rolling robust baseline." if count else "No observations exceeded the configured robust anomaly threshold in the ingested data."

    if intent == "hourly_analysis" and energy_data.get("top_hours"):
        hours_text = ", ".join(f"{x['hour']:02d}:00 ({x['average']} kW)" for x in energy_data["top_hours"][:3])
        if lang == "es":
            return f"Las horas con mayor demanda promedio en los datos fueron: {hours_text}."
        if lang == "fr":
            return f"Les heures ayant la consommation moyenne la plus élevée sont: {hours_text}."
        if lang == "de":
            return f"Die Stunden mit dem höchsten Durchschnittsverbrauch waren: {hours_text}."
        if lang == "zh":
            return f"数据中平均用电需求最高的时段为：{hours_text}。"
        if lang == "hi":
            return f"डेटा में सबसे अधिक औसत मांग वाले घंटे थे: {hours_text}।"
        return f"The highest average-demand hours in the ingested data were {hours_text}."

    if intent == "weekday_weekend_comparison" and energy_data.get("weekday_average") is not None:
        wd = energy_data['weekday_average']
        we = energy_data['weekend_average']
        if lang == "es":
            return f"La demanda promedio fue de {wd} kW en días laborables y de {we} kW los fines de semana."
        if lang == "fr":
            return f"La demande moyenne était de {wd} kW en semaine et de {we} kW le week-end."
        if lang == "de":
            return f"Der Durchschnittsverbrauch lag an Werktagen bei {wd} kW und an Wochenenden bei {we} kW."
        if lang == "zh":
            return f"工作日平均用电需求为 {wd} kW，周末平均需求为 {we} kW。"
        if lang == "hi":
            return f"सप्ताह के दिनों में औसत मांग {wd} kW और सप्ताहांत में {we} kW रही।"
        return f"Mean demand averaged {wd} kW on weekdays and {we} kW on weekends."

    if intent == "evening_increase" and energy_data.get("evening_average") is not None:
        baseline = energy_data.get("average_demand")
        evening = energy_data["evening_average"]
        change = energy_data.get("evening_change_pct")
        change_text = f" ({change:+.1f}%)" if change is not None else ""
        submeter_profile = energy_data.get("submetering_evening_average", {})
        dominant = energy_data.get("dominant_submeter") or {}
        dominant_field = dominant.get("field")
        dominant_label = dominant.get("label")
        dominant_value = dominant.get("value")
        submeter_text = ""
        if submeter_profile and dominant_field and dominant_value is not None:
            kitchen = submeter_profile.get("Sub_metering_1", 0.0)
            laundry = submeter_profile.get("Sub_metering_2", 0.0)
            hvac = submeter_profile.get("Sub_metering_3", 0.0)
            submeter_text = f" The dataset's largest evening sub-meter reading was {dominant_label} ({dominant_field}), averaging {dominant_value} Wh per minute in the 18:00-20:59 window; kitchen averaged {kitchen} Wh per minute, laundry averaged {laundry} Wh per minute, and heating/AC averaged {hvac} Wh per minute. This identifies the largest measured sub-meter category, not a definitive appliance-level cause."

        rec = decision_data.get("recommendations", [{}])[0].get("text", "")
        if lang == "es":
            res = f"La demanda promedio de 18:00-20:59 fue de {evening} kW{change_text}; el promedio general fue de {baseline} kW.{submeter_text}"
            return f"{res} Se recomienda monitorear el período de 18:00-21:00 para optimización de carga." if rec else res
        if lang == "fr":
            res = f"La demande moyenne de 18h00 à 20h59 était de {evening} kW{change_text} contre une moyenne générale de {baseline} kW.{submeter_text}"
            return f"{res} Surveillez la période 18h00-21h00 pour la gestion de charge." if rec else res
        if lang == "de":
            res = f"Der Durchschnittsverbrauch von 18:00-20:59 lag bei {evening} kW{change_text}; Gesamtmittelwert: {baseline} kW.{submeter_text}"
            return f"{res} Überwachen Sie 18:00-21:00 Uhr zur Lastoptimierung." if rec else res
        if lang == "zh":
            res = f"18:00-20:59 的平均需求为 {evening} kW{change_text}；全期平均需求为 {baseline} kW。{submeter_text}"
            return f"{res} 建议监测 18:00-21:00 期间负荷以实施需求响应策略。" if rec else res
        if lang == "hi":
            res = f"18:00-20:59 के दौरान औसत मांग {evening} kW{change_text} थी; कुल औसत {baseline} kW था।{submeter_text}"
            return f"{res} लोड प्रबंधन रणनीतियों के लिए 18:00-21:00 अवधि की निगरानी करें।" if rec else res
        base_resp = f"Mean demand from 18:00-20:59 was {evening} kW{change_text}; the full-period mean was {baseline} kW.{submeter_text}"
        return f"{base_resp} {rec}".strip()

    # Default / Peak demand / Insights
    obs = energy_data.get('observations', 0)
    avg = energy_data.get('average_demand')
    peak = energy_data.get('peak_demand')
    peak_submeters = energy_data.get("peak_submetering", {})
    peak_driver = energy_data.get("peak_submeter_driver") or {}
    peak_reason = ""
    if peak_submeters and peak_driver and all(peak_submeters.get(field) is not None for field in ("Sub_metering_1", "Sub_metering_2", "Sub_metering_3")):
        peak_reason = (f" At that peak, sub-meter readings were kitchen {peak_submeters['Sub_metering_1']} Wh, "
                       f"laundry {peak_submeters['Sub_metering_2']} Wh, and heating/AC {peak_submeters['Sub_metering_3']} Wh. "
                       f"The largest recorded sub-meter load was {peak_driver['label']}; this identifies the strongest measured "
                       "contributor at the peak, not a definitive appliance-level cause.")
    rec = decision_data.get("recommendations", [{}])[0].get("text", "") if intent == "insights" else ""
    if lang == "es":
        res = f"Se analizaron {obs} lecturas. La demanda promedio fue de {avg} kW y la demanda máxima observada fue de {peak} kW."
        return f"{res} {rec}".strip()
    if lang == "fr":
        res = f"{obs} lectures analysées. La demande moyenne était de {avg} kW et la crête observée était de {peak} kW."
        return f"{res} {rec}".strip()
    if lang == "de":
        res = f"{obs} Messungen analysiert. Durchschnittsverbrauch: {avg} kW, Spitzenverbrauch: {peak} kW."
        return f"{res} {rec}".strip()
    if lang == "zh":
        res = f"已分析 {obs} 条读数。平均用电需求为 {avg} kW，最高峰值需求为 {peak} kW。"
        return f"{res} {rec}".strip()
    if lang == "hi":
        res = f"{obs} रीडिंग का विश्लेषण किया गया। औसत मांग {avg} kW और चरम मांग {peak} kW रही।"
        return f"{res} {rec}".strip()
    base_resp = f"Analyzed {obs} readings. Average demand was {avg} kW and observed peak demand was {peak} kW.{peak_reason}"
    return f"{base_resp} {rec}".strip()


import uuid
from app.services.guardrail_service import check_guardrails


def generate_pictorial_data(intent: str, energy_data: dict, anomaly_data: dict, forecast_data: dict, forecast_items: list, evidence: list):
    has_data = bool(energy_data.get("observations") or anomaly_data.get("has_data") or forecast_data.get("has_data") or forecast_items)
    if not has_data:
        return None, None, []

    if intent == "forecast" and forecast_items:
        items = []
        for f in forecast_items:
            ts = f.get("timestamp")
            if hasattr(ts, "strftime"):
                label = ts.strftime("%H:%M")
            elif isinstance(ts, str) and len(ts) >= 16:
                label = ts[11:16]
            else:
                label = str(ts)
            items.append({
                "label": label,
                "demand": round(float(f.get("predicted_demand", 0)), 3),
                "lower_bound": round(float(f.get("lower_bound", 0)), 3),
                "upper_bound": round(float(f.get("upper_bound", 0)), 3),
                "unit": "kW"
            })
        return "forecast", f"Demand Forecast ({len(items)}h Horizon)", items

    if intent == "weekday_weekend_comparison":
        weekday = energy_data.get("weekday_average")
        weekend = energy_data.get("weekend_average")
        if weekday is not None or weekend is not None:
            items = [
                {"label": "Weekday", "demand": round(float(weekday or 0), 3), "category": "Weekday", "color": "#22d3ee", "unit": "kW"},
                {"label": "Weekend", "demand": round(float(weekend or 0), 3), "category": "Weekend", "color": "#a78bfa", "unit": "kW"}
            ]
            return "comparison", "Weekday vs Weekend Demand", items

    if intent == "evening_increase":
        baseline = energy_data.get("average_demand")
        evening = energy_data.get("evening_average")
        if evening is not None or baseline is not None:
            items = [
                {"label": "Full-Day Baseline", "demand": round(float(baseline or 0), 3), "category": "Baseline", "color": "#2dd4bf", "unit": "kW"},
                {"label": "Evening Peak (18-21h)", "demand": round(float(evening or 0), 3), "category": "Evening", "color": "#f59e0b", "unit": "kW"}
            ]
            return "comparison", "Evening Peak vs Baseline Demand", items

    if intent == "hourly_analysis":
        top_hours = energy_data.get("top_hours", [])
        if top_hours:
            items = [{"label": f"{item['hour']:02d}:00", "demand": round(float(item["average"]), 3), "unit": "kW"} for item in top_hours]
            return "hourly", "Peak Demand by Hour of Day", items

    if intent == "peak_demand":
        peaks = [e for e in evidence if "demand" in e or "actual_value" in e]
        if peaks:
            items = []
            for idx, p in enumerate(peaks[:8]):
                ts = str(p.get("timestamp", ""))
                lbl = ts[11:16] if len(ts) >= 16 else ts[-5:] if len(ts) >= 5 else f"Peak {idx+1}"
                val = p.get("demand", p.get("actual_value", p.get("value", 0)))
                items.append({"label": lbl, "demand": round(float(val), 3), "unit": "kW"})
            return "bar", "Top Peak Demand Records", items
        elif energy_data.get("top_hours"):
            items = [{"label": f"{item['hour']:02d}:00", "demand": round(float(item["average"]), 3), "unit": "kW"} for item in energy_data.get("top_hours", [])]
            return "bar", "Peak Demand by Hour", items

    if intent == "anomaly_detection":
        anomalies = [e for e in evidence if "actual_value" in e or "anomaly_score" in e]
        if anomalies:
            items = []
            for idx, a in enumerate(anomalies[:8]):
                ts = str(a.get("timestamp", ""))
                lbl = ts[11:16] if len(ts) >= 16 else f"#{idx+1}"
                items.append({
                    "label": lbl,
                    "actual": round(float(a.get("actual_value", 0)), 3),
                    "expected": round(float(a.get("expected_value", 0)), 3),
                    "deviation": round(float(a.get("deviation", 0)), 3),
                    "severity": a.get("severity", "medium"),
                    "unit": "kW"
                })
            return "anomaly", "Detected Consumption Anomalies", items

    # General overview / insights fallback
    items = []
    if energy_data.get("average_demand") is not None:
        items.append({"label": "Mean Demand", "demand": round(float(energy_data["average_demand"]), 3), "color": "#22d3ee", "unit": "kW"})
    if energy_data.get("peak_demand") is not None:
        items.append({"label": "Peak Demand", "demand": round(float(energy_data["peak_demand"]), 3), "color": "#f43f5e", "unit": "kW"})
    if energy_data.get("evening_average") is not None:
        items.append({"label": "Evening Mean", "demand": round(float(energy_data["evening_average"]), 3), "color": "#f59e0b", "unit": "kW"})
    if energy_data.get("weekday_average") is not None:
        items.append({"label": "Weekday Mean", "demand": round(float(energy_data["weekday_average"]), 3), "color": "#38bdf8", "unit": "kW"})
    if energy_data.get("weekend_average") is not None:
        items.append({"label": "Weekend Mean", "demand": round(float(energy_data["weekend_average"]), 3), "color": "#a78bfa", "unit": "kW"})

    if items:
        return "overview", "Smart Grid Demand Profile", items

    if forecast_items:
        items = [
            {"label": str(f.get("timestamp", ""))[-8:-3] or f"t+{i}", "demand": round(float(f.get("predicted_demand", 0)), 3), "unit": "kW"}
            for i, f in enumerate(forecast_items[:6])
        ]
        return "forecast", "Demand Forecast", items

    return None, None, []


@router.post("/query", response_model=QueryResponse)
def query(body: QueryRequest):
    normalized = body.question.lower()
    restricted = ("api key", "system prompt", "system instructions", "execute arbitrary", "run python", "execute python",
                  "delete all", "drop database", "direct access to the database", "query mongodb directly")
    if any(term in normalized for term in restricted):
        raise HTTPException(400, "That request is outside the assistant's supported analytics tasks.")

    lang = detect_language(body.question, body.language)

    # Apply Guardrail Check
    is_allowed, intent_override, guardrail_msg, suggestions = check_guardrails(body.question, language=lang)
    if not is_allowed:
        trace_id = uuid.uuid4().hex[:24]
        is_greeting = intent_override == "greeting"
        response_payload = {
            "success": True,
            "question": body.question,
            "intent": intent_override or "out_of_scope",
            "answer": guardrail_msg,
            "warning": None if is_greeting else guardrail_msg,
            "agents_used": ["guardrail_agent"],
            "evidence": [],
            "chart_data": [],
            "chart_type": None,
            "chart_title": None,
            "confidence": 1.0 if is_greeting else 0.0,
            "trace_id": trace_id,
            "llm_provider": "guardrail",
            "language": lang,
            "is_relevant": is_greeting,
            "suggested_queries": suggestions,
        }
        try:
            db.query_history.insert_one({
                "trace_id": trace_id,
                "question": body.question,
                "intent": intent_override or "out_of_scope",
                "language": lang,
                "answer": guardrail_msg,
                "confidence": 1.0 if is_greeting else 0.0,
                "llm_provider": "guardrail",
                "agents_used": ["guardrail_agent"],
                "evidence_count": 0,
                "is_relevant": is_greeting,
                "created_at": datetime.now(timezone.utc),
            })
        except Exception:
            pass
        return response_payload

    intent, hours = classify(body.question)
    lowered_question = strip_accents(body.question.lower())
    asks_for_reason = any(term in lowered_question for term in ("why", "reason", "cause", "explain", "increase", "increased", "rising", "spike"))
    asks_about_energy = any(term in lowered_question for term in ("energy", "electricity", "consumption", "usage", "demand", "power", "peak"))
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", body.question)
    selected_day = body.start_date or (date_match.group(1) if date_match else None)
    if asks_for_reason and asks_about_energy and not selected_day:
        trace_id = uuid.uuid4().hex[:24]
        return {"success": True, "question": body.question, "intent": "period_clarification",
                "answer": "Which day would you like me to analyze? Please provide the date as YYYY-MM-DD. I’ll answer using readings for that day available in the dataset.",
                "warning": None, "agents_used": [], "evidence": [], "chart_data": [],
                "chart_type": None, "chart_title": None, "confidence": 1.0,
                "trace_id": trace_id, "llm_provider": "clarification", "language": lang,
                "is_relevant": True, "suggested_queries": []}
    if selected_day:
        try:
            selected = datetime.strptime(selected_day[:10], "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(422, "Please provide the day as a valid YYYY-MM-DD date.") from exc
        selected_day = selected.strftime("%Y-%m-%d")
        body.start_date = selected_day
        body.end_date = (selected + timedelta(days=1) - timedelta(microseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")
    try:
        trace_id, messages, trace = run(body.question, intent, hours, body.start_date, body.end_date)
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc))

    raw_evidence = [item for message in messages for item in message.get("evidence", [])]
    evidence = []
    seen = set()
    for item in raw_evidence:
        key = json.dumps(item, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            evidence.append(item)

    energy_data = next((m.get("data", {}) for m in messages if m.get("task") == "energy_analysis"), {})
    anomaly_data = next((m.get("data", {}) for m in messages if m.get("task") == "anomaly_analysis"), {})
    decision_data = next((m.get("data", {}) for m in messages if m.get("task") == "recommendation"), {})
    forecast_message = next((m for m in messages if m.get("task") == "forecast"), {})
    forecast_data = forecast_message.get("data", {})
    forecast_items = forecast_message.get("evidence", [])
    failed = next((m for m in messages if m.get("task") == "agent_failure"), None)

    if failed:
        fallback = failed.get("data", {}).get("error", "An analysis step failed.")
        answer, provider = fallback, "analytics_fallback"
        return {"success": False, "question": body.question, "intent": intent, "answer": answer,
                "warning": None, "agents_used": [m["source_agent"] for m in messages], "evidence": evidence,
                "chart_data": [], "chart_type": None, "chart_title": None, "confidence": 0.0,
                "trace_id": trace_id, "llm_provider": provider,
                "language": lang, "is_relevant": True, "suggested_queries": []}

    has_data = bool(energy_data.get("observations") or anomaly_data.get("has_data") or forecast_data.get("has_data") or forecast_items)
    fallback = format_localized_fallback(lang, intent, energy_data, anomaly_data, forecast_data, forecast_items, decision_data, has_data)

    answer, provider = explain(body.question, evidence, fallback, language=lang)
    confidence = min((m.get("confidence", 0) for m in messages), default=0)

    chart_type, chart_title, chart_data = generate_pictorial_data(intent, energy_data, anomaly_data, forecast_data, forecast_items, evidence)

    # Persist query to query_history collection
    try:
        db.query_history.insert_one({
            "trace_id": trace_id,
            "question": body.question,
            "intent": intent,
            "language": lang,
            "answer": answer,
            "confidence": confidence,
            "llm_provider": provider,
            "agents_used": [m["source_agent"] for m in messages],
            "evidence_count": len(evidence),
            "is_relevant": True,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        pass

    agents_used_list = [m["source_agent"] for m in messages]
    citations = build_citations(intent, energy_data, anomaly_data, forecast_data, forecast_items)
    evaluation = compute_per_query_evaluation(answer, evidence, confidence, intent, agents_used_list)

    return {"success": True, "question": body.question, "intent": intent, "answer": answer,
            "warning": None,
            "agents_used": agents_used_list, "evidence": evidence,
            "chart_data": chart_data, "chart_type": chart_type, "chart_title": chart_title,
            "confidence": confidence,
            "trace_id": trace_id, "llm_provider": provider, "language": lang,
            "is_relevant": True, "suggested_queries": [],
            "citations": citations, "evaluation": evaluation}
