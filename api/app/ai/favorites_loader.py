"""Lee favoritos Surplus (tabla surplus_favorite_model), misma BD que el panel-admin."""
from __future__ import annotations

import psycopg2

from app.settings import get_settings


class FavoritesError(RuntimeError):
    pass


def load_favorite_candidates() -> list[dict]:
    url = (get_settings().surplus_database_url or "").strip()
    if not url:
        raise FavoritesError("Falta SURPLUS_DATABASE_URL")

    conn = psycopg2.connect(url, gssencmode="disable", connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT model_id, preference_rank, min_discount_pct, max_output_price
                FROM surplus_favorite_model
                WHERE enabled IS TRUE
                ORDER BY preference_rank ASC, model_id ASC
                """
            )
            out: list[dict] = []
            for model_id, rank, discount, price in cur.fetchall():
                mid = str(model_id or "").strip()
                if not mid:
                    continue
                item: dict = {
                    "model_id": mid,
                    "priority": int(rank) if rank is not None else len(out) + 1,
                }
                if price is not None:
                    try:
                        item["max_output_price"] = float(price)
                    except (TypeError, ValueError):
                        pass
                out.append(item)
            return out
    finally:
        conn.close()