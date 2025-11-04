from __future__ import annotations

"""
Override Service
 - Utilitas generik untuk menerapkan override pada hasil endpoint.
 - Fokus langkah 2: merge logic (priority, replace/delta, deep-merge khusus array).
 - Langkah 3: guard & helper terkait konfigurasi (enable_overrides, use_overrides).
"""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request

from app.config.settings import settings


OverrideDoc = Dict[str, Any]


def _is_subset_or_empty(filter_values: Optional[List[str]], context_values: Optional[List[str]]) -> bool:
    if not filter_values:
        return True
    if not context_values:
        return False
    context_set = {v.lower() for v in context_values}
    return all((v or "").lower() in context_set for v in filter_values)


def _date_overlaps(start: Optional[str], end: Optional[str], ctx_start: Optional[str], ctx_end: Optional[str]) -> bool:
    # Simple lexicographical compare for YYYY-MM-DD
    if not start and not end:
        return True
    if ctx_start and end and ctx_start > end:
        return False
    if ctx_end and start and ctx_end < start:
        return False
    return True


def should_apply_overrides(request: Optional[Request]) -> bool:
    """Respect global flag and query param use_overrides=false."""
    if not settings.enable_overrides:
        return False
    if request is None:
        return True
    qp = request.query_params
    if qp.get("use_overrides") is None:
        return True
    return qp.get("use_overrides", "true").lower() != "false"


def select_applicable_overrides(
    overrides: List[OverrideDoc],
    *,
    scope_type: str,
    scope_id: str,
    module: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    post_urls: Optional[List[str]] = None,
) -> List[OverrideDoc]:
    """Filter dan urutkan override yang cocok dengan konteks permintaan."""
    candidates: List[Tuple[int, int, OverrideDoc]] = []  # (specificity, priority, doc)
    for doc in overrides:
        if not doc.get("enabled", True):
            continue
        if doc.get("scope_type") != scope_type:
            continue
        if str(doc.get("scope_id")) != str(scope_id):
            continue
        if doc.get("module") != module:
            continue

        flt = doc.get("filters", {}) or {}
        if not _date_overlaps(flt.get("start_date"), flt.get("end_date"), start_date, end_date):
            continue
        if not _is_subset_or_empty(flt.get("platforms"), platforms):
            continue
        if not _is_subset_or_empty(flt.get("post_urls"), post_urls):
            continue

        specificity = sum(1 for k in ["start_date", "end_date", "platforms", "post_urls"] if flt.get(k))
        priority = int(doc.get("priority", 0))
        candidates.append((specificity, priority, doc))

    # Sort: priority desc, specificity desc, updated_at desc (if present)
    candidates.sort(key=lambda t: (t[1], t[0], str(t[2].get("updated_at", ""))), reverse=True)
    return [c[2] for c in candidates]


def _deep_merge(a: Any, b: Any) -> Any:
    """Deep merge sederhana (b menimpa a)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = _deep_merge(a.get(k), v) if k in a else v
        return out
    return b


def _merge_list_by_key(base: List[Dict[str, Any]], delta: List[Dict[str, Any]], keys: List[str]) -> List[Dict[str, Any]]:
    idx = {"::".join(str(item.get(k)) for k in keys): i for i, item in enumerate(base)}
    result = list(base)
    for item in delta:
        composite = "::".join(str(item.get(k)) for k in keys)
        if composite in idx:
            i = idx[composite]
            result[i] = _deep_merge(result[i], item)
        else:
            result.append(item)
    return result


def _merge_module(base: Dict[str, Any], delta: Dict[str, Any], module: str) -> Dict[str, Any]:
    base_copy = dict(base or {})
    if module in {"timeline"} and "timeline" in delta and isinstance(delta["timeline"], list):
        merged = _merge_list_by_key(base_copy.get("timeline", []), delta["timeline"], ["date"])
        base_copy["timeline"] = merged
        # merge other top-level fields if any
        other = {k: v for k, v in delta.items() if k != "timeline"}
        base_copy = _deep_merge(base_copy, other)
        return base_copy

    if module in {"topics"} and "trending_topics" in delta:
        merged = _merge_list_by_key(base_copy.get("trending_topics", []), delta["trending_topics"], ["topic"]) 
        base_copy["trending_topics"] = merged
        other = {k: v for k, v in delta.items() if k != "trending_topics"}
        base_copy = _deep_merge(base_copy, other)
        return base_copy

    if module in {"emotions"} and isinstance(delta.get("emotions"), list):
        merged = _merge_list_by_key(base_copy.get("emotions", []), delta["emotions"], ["emotion"]) 
        base_copy["emotions"] = merged
        other = {k: v for k, v in delta.items() if k != "emotions"}
        base_copy = _deep_merge(base_copy, other)
        return base_copy

    if module in {"audience", "demographics"} and isinstance(delta.get("demographics"), list):
        merged = _merge_list_by_key(
            base_copy.get("demographics", []),
            delta["demographics"],
            ["category", "value", "platform"],
        )
        base_copy["demographics"] = merged
        other = {k: v for k, v in delta.items() if k != "demographics"}
        base_copy = _deep_merge(base_copy, other)
        return base_copy

    if module in {"performance"} and isinstance(delta.get("platform_breakdown"), list):
        merged = _merge_list_by_key(
            base_copy.get("platform_breakdown", []),
            delta["platform_breakdown"],
            ["platform"],
        )
        base_copy["platform_breakdown"] = merged
        other = {k: v for k, v in delta.items() if k != "platform_breakdown"}
        base_copy = _deep_merge(base_copy, other)
        return base_copy

    # Default: deep-merge
    return _deep_merge(base_copy, delta)


def apply_overrides(
    base_response: Dict[str, Any],
    overrides: List[OverrideDoc],
    module: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Terapkan list override ke base_response. Return (merged, applied_ids)."""
    result = dict(base_response or {})
    applied: List[str] = []
    for doc in overrides:
        mode = (doc.get("mode") or "delta").lower()
        payload = doc.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        if mode == "replace":
            result = payload
        else:
            result = _merge_module(result, payload, module)
        if doc.get("_id"):
            applied.append(str(doc["_id"]))
    return result, applied



