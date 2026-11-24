"""Cliente del Surplus Satellite (POST /api/pick) con favoritos del panel."""
from __future__ import annotations

import time
from typing import Any

import requests

from app.ai.favorites_loader import FavoritesError, load_favorite_candidates
from app.settings import get_settings


class SatellitePickError(RuntimeError):
    pass


def pick_surplus_model_for_lookup(
    *,
    exclude_models: set[str] | None = None,
) -> str:
    s = get_settings()
    base = (s.surplus_satellite_base_url or "").strip().rstrip("/")
    if not base:
        raise SatellitePickError("Falta SURPLUS_SATELLITE_BASE_URL")

    try:
        candidates = load_favorite_candidates()
    except FavoritesError:
        # Sin BD: el satélite puede resolver favoritos por sí mismo
        candidates = []

    excluded = {m.strip() for m in (exclude_models or set()) if m.strip()}
    if candidates and excluded:
        candidates = [c for c in candidates if c.get("model_id") not in excluded]

    api_key = (s.surplusintelligence_api_key or "").strip()
    if not api_key:
        raise SatellitePickError("Falta SURPLUSINTELLIGENCE_API_KEY")

    payload: dict[str, Any] = {
        "api_key": api_key,
        "min_discount_pct": s.surplus_satellite_min_discount_pct,
        "verify_model": s.surplus_satellite_verify_model,
        "max_output_price_per_1m_usd": s.surplus_satellite_max_output_price_per_1m_usd,
    }
    if candidates:
        payload["models"] = candidates

    url = f"{base}/api/pick"
    timeout = s.surplus_satellite_pick_timeout_seconds
    last_detail = "sin respuesta"

    for attempt in range(1, s.surplus_satellite_pick_max_attempts + 1):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
        except requests.RequestException as exc:
            last_detail = f"red: {exc}"
            if attempt < s.surplus_satellite_pick_max_attempts:
                time.sleep(s.surplus_satellite_pick_retry_seconds)
                continue
            raise SatellitePickError(last_detail) from exc

        if resp.status_code == 200:
            data = resp.json()
            model_id = (data.get("model_id") or "").strip()
            if not model_id:
                raise SatellitePickError("Satélite devolvió 200 sin model_id")
            if model_id in excluded:
                excluded.add(model_id)
                payload["models"] = [c for c in candidates if c.get("model_id") not in excluded]
                continue
            return model_id

        if resp.status_code == 503 and attempt < s.surplus_satellite_pick_max_attempts:
            try:
                last_detail = str(resp.json().get("detail", resp.text))
            except ValueError:
                last_detail = resp.text[:200]
            time.sleep(s.surplus_satellite_pick_retry_seconds)
            continue

        try:
            err = resp.json()
            last_detail = err.get("detail") if isinstance(err.get("detail"), str) else resp.text
        except ValueError:
            last_detail = resp.text or f"HTTP {resp.status_code}"
        raise SatellitePickError(f"Satélite /api/pick ({resp.status_code}): {last_detail}")

    raise SatellitePickError(f"Satélite sin modelo disponible: {last_detail}")