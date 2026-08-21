"""Source-aware CI runner, billing, and resource recommendations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gkd_task.canonical import CREDENTIAL_RE, digest_object, require_keys, require_sha256
from gkd_task.errors import TaskError

from .resources import PRESET_NAMES, classify_artifacts, select_preset


GOALS = ("speed-first", "balanced", "cost-aware")
VISIBILITIES = ("public", "private", "internal", "unknown")
RUNNER_KINDS = ("github-hosted", "self-hosted", "unknown")


def _string(value: Any, code: str, *, max_bytes: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > max_bytes or CREDENTIAL_RE.search(value):
        raise TaskError(code)
    return value


def _runner(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        value = {"kind": value}
    if not isinstance(value, dict) or not set(value).issubset({"provider", "kind", "capacity", "os", "verified"}):
        raise TaskError("RUNNER_FACTS_INVALID")
    kind = value.get("kind", "unknown")
    if kind not in RUNNER_KINDS:
        raise TaskError("RUNNER_FACTS_INVALID")
    capacity = value.get("capacity", "unknown")
    if capacity not in {"resource-constrained", "standard", "high-capacity", "unknown"}:
        raise TaskError("RUNNER_FACTS_INVALID")
    operating_system = value.get("os", "unknown")
    if operating_system not in {"linux", "macos", "windows", "unknown"}:
        raise TaskError("RUNNER_FACTS_INVALID")
    provider = value.get("provider", "github")
    if provider not in {"github", "unknown"}:
        raise TaskError("RUNNER_FACTS_INVALID")
    verified = value.get("verified", False)
    if not isinstance(verified, bool):
        raise TaskError("RUNNER_FACTS_INVALID")
    return {
        "provider": provider,
        "kind": kind,
        "capacity": capacity,
        "os": operating_system,
        "verified": verified,
    }


def _policy(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not set(value).issubset({"baseBranch", "requiredChecks", "policyDigest", "verified"}):
        raise TaskError("POLICY_FACTS_INVALID")
    branch = _string(value.get("baseBranch", "unknown"), "POLICY_FACTS_INVALID")
    checks = value.get("requiredChecks", [])
    if not isinstance(checks, list) or any(not isinstance(check, str) or not check for check in checks):
        raise TaskError("POLICY_FACTS_INVALID")
    if checks != sorted(set(checks)):
        raise TaskError("POLICY_FACTS_INVALID")
    digest = value.get("policyDigest")
    if digest is not None:
        require_sha256(digest, "POLICY_FACTS_INVALID")
    verified = value.get("verified", False)
    if not isinstance(verified, bool):
        raise TaskError("POLICY_FACTS_INVALID")
    return {
        "baseBranch": branch,
        "requiredChecks": list(checks),
        "policyDigest": digest,
        "verified": verified,
    }


def _billing(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not set(value).issubset({"source", "currency", "pricePerMinute", "verified", "checkedAt"}):
        raise TaskError("BILLING_FACTS_INVALID")
    source = value.get("source", "unknown")
    if source not in {"github-public-pricing", "provider-contract", "unknown"}:
        raise TaskError("BILLING_FACTS_INVALID")
    currency = value.get("currency")
    if currency is not None:
        currency = _string(currency, "BILLING_FACTS_INVALID", max_bytes=8)
    price = value.get("pricePerMinute")
    if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0):
        raise TaskError("BILLING_FACTS_INVALID")
    verified = value.get("verified", False)
    if not isinstance(verified, bool):
        raise TaskError("BILLING_FACTS_INVALID")
    checked_at = value.get("checkedAt")
    if checked_at is not None:
        checked_at = _string(checked_at, "BILLING_FACTS_INVALID", max_bytes=64)
    if verified and (source == "unknown" or price is None or currency is None or checked_at is None):
        raise TaskError("BILLING_FACTS_INVALID")
    return {
        "source": source,
        "currency": currency,
        "pricePerMinute": price if verified else None,
        "verified": verified,
        "checkedAt": checked_at if verified else None,
    }


def parse_ci_facts(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "visibility", "runner", "policy", "billing", "resource"}:
        raise TaskError("CI_FACTS_INVALID")
    if value["schemaVersion"] != 1:
        raise TaskError("CI_FACTS_INVALID")
    visibility = value["visibility"]
    if visibility not in VISIBILITIES:
        raise TaskError("VISIBILITY_FACTS_INVALID")
    resource = value["resource"]
    if not isinstance(resource, dict):
        raise TaskError("RESOURCE_FACTS_INVALID")
    runner = _runner(value["runner"])
    policy = _policy(value["policy"])
    billing = _billing(value["billing"])
    # select_preset performs the numeric and verification checks for resource facts.
    resource_copy = deepcopy(resource)
    resource_copy.pop("complete", None)
    resource_copy.setdefault("source", "unknown")
    resource_copy.setdefault("verified", False)
    selected_resource = select_preset(None, resource_copy)
    return {
        "schemaVersion": 1,
        "visibility": visibility,
        "runner": runner,
        "policy": policy,
        "billing": billing,
        "resource": selected_resource["resourceFacts"],
    }


def verify_runtime_price(value: dict[str, Any]) -> dict[str, Any]:
    billing = _billing(value)
    if billing["verified"]:
        return {
            "status": "verified",
            "source": billing["source"],
            "currency": billing["currency"],
            "pricePerMinute": billing["pricePerMinute"],
            "checkedAt": billing["checkedAt"],
        }
    return {
        "status": "unverified",
        "source": billing["source"],
        "currency": None,
        "pricePerMinute": None,
        "checkedAt": None,
    }


def _highest_supported_preset(facts: dict[str, Any]) -> str:
    resource = deepcopy(facts["resource"])
    resource.pop("complete", None)
    complete = all(resource.get(key) is not None for key in ("availableDiskBytes", "memoryBytes", "cpuCount")) and resource.get("verified") is True
    if not complete:
        return "resource-constrained"
    for name in ("high-capacity", "standard"):
        try:
            select_preset(name, resource)
        except TaskError:
            continue
        return name
    return "resource-constrained"


def recommend_ci(
    facts: dict[str, Any],
    goal: str,
    artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if goal not in GOALS:
        raise TaskError("RECOMMENDATION_GOAL_INVALID")
    normalized = parse_ci_facts(facts)
    resource_facts = deepcopy(normalized["resource"])
    resource_facts.pop("complete", None)
    if goal == "speed-first":
        preset_name = _highest_supported_preset(normalized)
    elif goal == "balanced":
        preset_name = "standard" if normalized["resource"]["complete"] else "resource-constrained"
    else:
        preset_name = "resource-constrained"
    try:
        plan = classify_artifacts(artifacts, preset_name, resource_facts) if artifacts is not None else None
    except TaskError as error:
        if error.code in {"RESOURCE_FACTS_REQUIRED", "RESOURCE_PRESET_UNSUPPORTED"}:
            preset_name = "resource-constrained"
            plan = classify_artifacts(artifacts, preset_name, resource_facts) if artifacts is not None else None
        else:
            raise
    price = verify_runtime_price(normalized["billing"])
    runner = normalized["runner"]
    if goal == "cost-aware" and price["status"] != "verified":
        runner_action = "retain-current-runner-unpriced"
        price_reason = "PRICE_VERIFICATION_REQUIRED"
    elif goal == "cost-aware":
        runner_action = "choose-lowest-verified-cost-runner"
        price_reason = "VERIFIED_RUNTIME_PRICE"
    elif goal == "speed-first":
        runner_action = "choose-highest-capacity-verified-runner"
        price_reason = "PRICE_NOT_USED_FOR_SPEED_GOAL"
    else:
        runner_action = "choose-standard-verified-runner"
        price_reason = "BALANCED_RESOURCE_AND_COST"
    recommendation = {
        "schemaVersion": 1,
        "goal": goal,
        "preset": preset_name,
        "runnerAction": runner_action,
        "price": price,
        "priceReason": price_reason,
        "visibility": normalized["visibility"],
        "runner": runner,
        "policy": normalized["policy"],
        "resource": resource_facts,
        "artifactPlan": plan,
        "outcome": "blocked" if plan is not None and plan["outcome"] == "blocked" else "recommended",
    }
    recommendation["recommendationDigest"] = digest_object({key: value for key, value in recommendation.items() if key != "recommendationDigest"})
    return recommendation


def validate_recommendation(value: dict[str, Any]) -> None:
    require_keys(
        value,
        {
            "schemaVersion",
            "goal",
            "preset",
            "runnerAction",
            "price",
            "priceReason",
            "visibility",
            "runner",
            "policy",
            "resource",
            "artifactPlan",
            "outcome",
            "recommendationDigest",
        },
        "RECOMMENDATION_INVALID",
    )
    if value["schemaVersion"] != 1 or value["goal"] not in GOALS or value["preset"] not in PRESET_NAMES:
        raise TaskError("RECOMMENDATION_INVALID")
    require_sha256(value["recommendationDigest"], "RECOMMENDATION_INVALID")
    expected = digest_object({key: current for key, current in value.items() if key != "recommendationDigest"})
    if value["recommendationDigest"] != expected:
        raise TaskError("RECOMMENDATION_INVALID")
