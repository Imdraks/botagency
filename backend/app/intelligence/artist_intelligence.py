"""
Artist Intelligence Service — LLM-powered analysis.

Generates sophisticated AI summaries, SWOT, booking intelligence,
and predictions using GPT-4o-mini + statistical data.
"""
import json
import logging
import math
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.intelligence.prediction_service import ArtistPredictionService

logger = logging.getLogger(__name__)

# Max tokens for LLM analysis
MAX_TOKENS = 2000
LLM_TIMEOUT = 45.0


def _call_llm_sync(prompt: str, system: str = "Tu es un analyste expert de l'industrie musicale. Réponds uniquement en JSON valide.") -> Optional[str]:
    """Sync call to OpenAI API."""
    api_key = settings.openai_api_key
    if not api_key:
        logger.warning("No OpenAI API key, skipping LLM analysis")
        return None

    model = settings.openai_model or "gpt-4o-mini"
    try:
        with httpx.Client(timeout=LLM_TIMEOUT) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": MAX_TOKENS,
                    "temperature": 0.4,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None


def _parse_json(raw: str, default: Dict) -> Dict:
    """Parse JSON from LLM response, stripping markdown fences."""
    if not raw:
        return default
    raw = raw.strip()
    if raw.startswith("```"):
        import re
        raw = re.sub(r'^```(?:json)?\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM JSON: {e}")
        return default


def compute_statistical_predictions(
    db: Session,
    artist_name: str,
    workspace_id: int,
    ml: int,
    velocity: float,
) -> Dict[str, Any]:
    """
    Use ArtistPredictionService (EWMA) if enough snapshots,
    otherwise fall back to velocity-based formula.
    Returns dict with prediction fields.
    """
    result = {
        "growth_trend": "stable",
        "growth_rate_monthly": 0.0,
        "predicted_listeners_30d": ml,
        "predicted_listeners_90d": ml,
        "predicted_listeners_180d": ml,
        "confidence_score": 0.3,
        "growth_probability": 50.0,
        "prediction_method": "fallback",
    }

    if not ml:
        return result

    # Try EWMA prediction service
    try:
        svc = ArtistPredictionService(db)
        pred = svc.get_prediction(artist_name, workspace_id)

        if pred.is_valid and pred.snapshot_count >= 2:
            result["predicted_listeners_30d"] = pred.central.value_30d
            result["predicted_listeners_90d"] = pred.central.value_90d
            # 180d = extrapolate from central growth rate
            result["predicted_listeners_180d"] = max(0, int(ml * math.exp(pred.central.growth_rate * 180)))
            result["growth_rate_monthly"] = round(pred.central.growth_rate * 30 * 100, 2)
            result["confidence_score"] = pred.confidence_score / 100.0
            result["growth_probability"] = pred.growth_probability
            result["prediction_method"] = "ewma"

            # Growth trend from actual growth rate
            monthly_rate = pred.central.growth_rate * 30
            if monthly_rate > 0.05:
                result["growth_trend"] = "strong_growth"
            elif monthly_rate > 0.01:
                result["growth_trend"] = "growing"
            elif monthly_rate > -0.01:
                result["growth_trend"] = "stable"
            elif monthly_rate > -0.05:
                result["growth_trend"] = "declining"
            else:
                result["growth_trend"] = "sharp_decline"

            logger.info(
                f"EWMA prediction for {artist_name}: "
                f"30d={pred.central.value_30d}, 90d={pred.central.value_90d}, "
                f"conf={pred.confidence_score}, method=ewma"
            )
            return result
    except Exception as e:
        logger.warning(f"EWMA prediction failed for {artist_name}: {e}")

    # Fallback: velocity-based linear
    if velocity:
        result["growth_rate_monthly"] = round(velocity * 100, 1)
        result["predicted_listeners_30d"] = int(ml * (1 + velocity))
        result["predicted_listeners_90d"] = int(ml * (1 + velocity * 3))
        result["predicted_listeners_180d"] = int(ml * (1 + velocity * 6))
        result["prediction_method"] = "velocity_linear"

        if velocity > 0.05:
            result["growth_trend"] = "strong_growth"
        elif velocity > 0.01:
            result["growth_trend"] = "growing"
        elif velocity > -0.01:
            result["growth_trend"] = "stable"
        elif velocity > -0.05:
            result["growth_trend"] = "declining"
        else:
            result["growth_trend"] = "sharp_decline"

    return result


def compute_llm_intelligence(
    artist_name: str,
    tier: str,
    ml: int,
    spotify_followers: int,
    instagram_followers: int,
    tiktok_followers: int,
    youtube_subscribers: int,
    genres: List[str],
    country: Optional[str],
    velocity: float,
    growth_trend: str,
    predicted_30d: int,
    predicted_90d: int,
    fee_min: float,
    fee_max: float,
    score: int,
    drivers: List[Dict],
    penalties: List[Dict],
    signals: List[Dict],
) -> Dict[str, Any]:
    """
    Call LLM for rich qualitative analysis.
    Returns dict with AI fields for artist_analyses.
    """
    # Default fallback (rule-based)
    defaults = _build_rule_based_intelligence(
        artist_name, tier, ml, spotify_followers,
        instagram_followers, tiktok_followers, youtube_subscribers,
        velocity, growth_trend, score, fee_min, fee_max,
        drivers, penalties, signals,
    )

    # Build analysis prompt
    drivers_text = ", ".join([d.get("label", "") for d in (drivers or [])[:5]])
    penalties_text = ", ".join([p.get("label", "") for p in (penalties or [])[:5]])
    signals_text = ", ".join([
        s.get("type", "") if isinstance(s, dict) else str(s)
        for s in (signals or [])[:5]
    ])

    social_total = (instagram_followers or 0) + (tiktok_followers or 0) + (youtube_subscribers or 0)

    prompt = f"""Analyse cet artiste musical pour une agence de booking et donne ton analyse experte.

## DONNÉES ARTISTE
- Nom : {artist_name}
- Niveau : {tier}
- Pays : {country or "Non renseigné"}
- Genres : {", ".join(genres) if genres else "Non renseigné"}
- Monthly listeners Spotify : {ml:,}
- Followers Spotify : {spotify_followers:,}
- Instagram : {instagram_followers:,}
- TikTok : {tiktok_followers:,}
- YouTube : {youtube_subscribers:,}
- Total social : {social_total:,}
- Vélocité de croissance : {velocity:+.3f} ({growth_trend})
- Score de découverte : {score}/100
- Prédiction 30j : {predicted_30d:,} listeners
- Prédiction 90j : {predicted_90d:,} listeners
- Estimation cachet : {fee_min:,.0f}€ - {fee_max:,.0f}€

## SIGNAUX DÉTECTÉS
- Points forts : {drivers_text or "aucun"}
- Points faibles : {penalties_text or "aucun"}
- Signaux marché : {signals_text or "aucun"}

## FORMAT DE RÉPONSE (JSON strict)
Réponds avec ce JSON exact, en français :
{{
  "ai_summary": "Paragraphe de 3-5 phrases analysant le positionnement de l'artiste, son potentiel, et la recommandation pour l'agence. Sois spécifique et actionnable.",
  "strengths": ["Force 1", "Force 2", "Force 3"],
  "weaknesses": ["Faiblesse 1", "Faiblesse 2"],
  "opportunities": ["Opportunité 1", "Opportunité 2", "Opportunité 3"],
  "threats": ["Menace 1", "Menace 2"],
  "ai_recommendations": ["Recommandation actionnable 1", "Recommandation actionnable 2", "Recommandation actionnable 3"],
  "optimal_fee": <entier, cachet optimal recommandé en euros>,
  "negotiation_power": "low|medium|high",
  "best_booking_window": "description courte du meilleur moment pour booker",
  "event_type_fit": {{"Festival": <0-100>, "Concert": <0-100>, "Showcase": <0-100>, "Événement privé": <0-100>}},
  "territory_strength": {{"France": <0-100>, "Europe": <0-100>, "International": <0-100>}},
  "seasonal_demand": {{"Q1": <0.0-1.0>, "Q2": <0.0-1.0>, "Q3": <0.0-1.0>, "Q4": <0.0-1.0>}},
  "viral_potential": <float 0.0-1.0>,
  "best_platforms": ["plateforme1", "plateforme2"],
  "content_recommendations": ["Reco contenu 1", "Reco contenu 2"]
}}

Sois réaliste et basé sur les données. Pour le cachet, base-toi sur le marché français du live.
Pour les forces/faiblesses, analyse les vrais chiffres. Un artiste avec beaucoup de listeners mais peu de social a un problème d'engagement.
"""

    raw = _call_llm_sync(prompt)
    if not raw:
        logger.info(f"LLM unavailable, using rule-based intelligence for {artist_name}")
        return defaults

    parsed = _parse_json(raw, {})
    if not parsed:
        return defaults

    # Merge LLM output with type safety
    result = {}
    result["ai_summary"] = parsed.get("ai_summary") or defaults["ai_summary"]
    result["strengths"] = parsed.get("strengths") or defaults["strengths"]
    result["weaknesses"] = parsed.get("weaknesses") or defaults["weaknesses"]
    result["opportunities"] = parsed.get("opportunities") or defaults["opportunities"]
    result["threats"] = parsed.get("threats") or defaults["threats"]
    result["ai_recommendations"] = parsed.get("ai_recommendations") or defaults["ai_recommendations"]

    # Numeric fields with validation
    opt_fee = parsed.get("optimal_fee")
    result["optimal_fee"] = int(opt_fee) if opt_fee and isinstance(opt_fee, (int, float)) else defaults["optimal_fee"]

    neg = parsed.get("negotiation_power", "").lower()
    result["negotiation_power"] = neg if neg in ("low", "medium", "high") else defaults["negotiation_power"]

    result["best_booking_window"] = parsed.get("best_booking_window") or defaults["best_booking_window"]

    # Dict[str, float] fields
    for key in ("event_type_fit", "territory_strength", "seasonal_demand"):
        val = parsed.get(key)
        if isinstance(val, dict) and all(isinstance(v, (int, float)) for v in val.values()):
            result[key] = {k: float(v) for k, v in val.items()}
        else:
            result[key] = defaults[key]

    viral = parsed.get("viral_potential")
    result["viral_potential"] = float(viral) if isinstance(viral, (int, float)) and 0 <= viral <= 1 else defaults["viral_potential"]

    result["best_platforms"] = parsed.get("best_platforms") or defaults["best_platforms"]
    result["content_recommendations"] = parsed.get("content_recommendations") or defaults.get("content_recommendations", [])
    result["intelligence_method"] = "gpt"

    logger.info(f"LLM intelligence generated for {artist_name}")
    return result


def _build_rule_based_intelligence(
    artist_name: str,
    tier: str,
    ml: int,
    spotify_followers: int,
    instagram_followers: int,
    tiktok_followers: int,
    youtube_subscribers: int,
    velocity: float,
    growth_trend: str,
    score: int,
    fee_min: float,
    fee_max: float,
    drivers: List[Dict],
    penalties: List[Dict],
    signals: List[Dict],
) -> Dict[str, Any]:
    """Rule-based fallback when LLM is unavailable."""
    # Summary
    rec_map = {"BOOK": "signer", "WATCHLIST": "suivre", "WATCH": "suivre", "IGNORE": "passer"}
    drivers_text = ", ".join([d.get("label", "") for d in (drivers or [])[:3]])
    penalties_text = ", ".join([p.get("label", "") for p in (penalties or [])[:3]])

    summary = f"{artist_name} est un artiste de niveau {tier}"
    if ml:
        summary += f" avec {ml:,} auditeurs mensuels sur Spotify"
    summary += f". Score de découverte : {score}/100."
    if drivers_text:
        summary += f" Points forts : {drivers_text}."
    if penalties_text:
        summary += f" Points d'attention : {penalties_text}."

    # SWOT
    strengths = [d.get("label", "") for d in (drivers or []) if d.get("label")]
    weaknesses = [p.get("label", "") for p in (penalties or []) if p.get("label")]
    opportunities = [s if isinstance(s, str) else s.get("type", "") for s in (signals or []) if s]
    threats = []
    if velocity and velocity < -0.02:
        threats.append("Tendance à la baisse des auditeurs")

    # Booking
    optimal_fee = int((fee_min + fee_max) * 0.6) if fee_max else None
    neg_power = "high" if score >= 80 else "medium" if score >= 50 else "low"
    best_window = "Q4" if ml >= 100_000 else "Q2-Q3"

    if ml >= 500_000:
        event_fit = {"Festival": 90.0, "Concert": 85.0, "Showcase": 60.0, "Événement privé": 70.0}
    elif ml >= 100_000:
        event_fit = {"Festival": 70.0, "Concert": 80.0, "Showcase": 75.0, "Événement privé": 65.0}
    elif ml >= 10_000:
        event_fit = {"Festival": 40.0, "Concert": 60.0, "Showcase": 85.0, "Événement privé": 50.0}
    else:
        event_fit = {"Showcase": 80.0, "Événement privé": 60.0, "Concert": 40.0}

    # Platforms
    best_platforms = []
    if ml and ml > 0:
        best_platforms.append("Spotify")
    if instagram_followers and instagram_followers > 0:
        best_platforms.append("Instagram")
    if tiktok_followers and tiktok_followers > 0:
        best_platforms.append("TikTok")
    if youtube_subscribers and youtube_subscribers > 0:
        best_platforms.append("YouTube")
    if not best_platforms:
        best_platforms = ["Spotify", "Instagram"]

    viral = 0.8 if velocity and velocity > 0.05 else 0.5 if velocity and velocity > 0.01 else 0.2

    recs = []
    if score >= 60:
        recs.append(f"Score élevé ({score}/100) — explorer les opportunités de booking")
    if velocity and velocity > 0.03:
        recs.append("Croissance rapide — fenêtre d'opportunité ouverte")
    if fee_max and fee_max < 5000:
        recs.append("Cachet accessible — bon rapport qualité/prix")
    if not recs:
        recs.append("Continuer le suivi et réévaluer dans 30 jours")

    return {
        "ai_summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
        "ai_recommendations": recs,
        "optimal_fee": optimal_fee,
        "negotiation_power": neg_power,
        "best_booking_window": best_window,
        "event_type_fit": event_fit,
        "territory_strength": {"France": 80.0, "Europe": 40.0, "International": 20.0},
        "seasonal_demand": {"Q1": 0.3, "Q2": 0.5, "Q3": 0.8, "Q4": 0.9},
        "viral_potential": viral,
        "best_platforms": best_platforms,
        "content_recommendations": [],
        "intelligence_method": "rule_based",
    }
