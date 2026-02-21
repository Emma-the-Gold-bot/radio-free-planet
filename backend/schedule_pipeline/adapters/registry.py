"""Adapter registry — maps adapter names to their fetch functions."""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from ..contracts import StationSchedule
from . import kexp, nts, somafm, fip, wfmu, html_generic, continuous, seed

AdapterFn = Callable[..., Awaitable[StationSchedule]]

_ADAPTERS: dict[str, AdapterFn] = {
    "kexp_api": kexp.fetch,
    "nts_api": nts.fetch,
    "somafm_api": somafm.fetch,
    "fip_api": fip.fetch,
    "wfmu_html": wfmu.fetch,
    "html_generic": html_generic.fetch,
    "continuous": continuous.fetch,
    "seed": seed.fetch,
}

# Tier -> default adapter mapping
_TIER_DEFAULTS: dict[str, str] = {
    "tier1_api": "seed",
    "tier2_html": "html_generic",
    "tier2_enriched": "continuous",
    "tier3_seed": "seed",
}


def get_adapter(adapter_name: str | None, tier: str) -> AdapterFn:
    if adapter_name and adapter_name in _ADAPTERS:
        return _ADAPTERS[adapter_name]
    default_name = _TIER_DEFAULTS.get(tier, "seed")
    return _ADAPTERS[default_name]


async def run_adapter(
    station: dict[str, Any],
    rules: dict[str, Any],
) -> StationSchedule:
    tier = rules.get("tier", "tier3_seed")
    adapter_name = rules.get("adapter")
    adapter_fn = get_adapter(adapter_name, tier)

    # Some adapters accept a rules kwarg
    import inspect
    sig = inspect.signature(adapter_fn)
    if "rules" in sig.parameters:
        return await adapter_fn(station, rules=rules)
    return await adapter_fn(station)
