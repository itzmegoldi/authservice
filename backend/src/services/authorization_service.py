from __future__ import annotations

from typing import Any

from src.repositories.interfaces import PolicyRepository
from src.api.v1.schemas import AuthorizationDecision


class AuthorizationService:
    def __init__(self, policies: PolicyRepository) -> None:
        self.policies = policies

    def decide(
        self,
        claims: dict[str, Any],
        realm: str,
        resource: str,
        action: str,
        context: dict[str, Any],
    ) -> AuthorizationDecision:
        policies = self.policies.find_by_realm_resource_action(realm, resource, action)
        matched: list[str] = []
        allowed = False
        for policy in policies:
            if self._matches_condition(claims, policy.condition_json, context):
                matched.append(policy.name)
                allowed = policy.effect.upper() == "ALLOW"
        return AuthorizationDecision(allowed=allowed, matched_policies=matched)

    def _matches_condition(self, claims: dict[str, Any], condition: dict[str, Any], context: dict[str, Any]) -> bool:
        role = condition.get("role")
        if role is not None and role not in (claims.get("roles") or []):
            return False

        attribute_name = condition.get("attribute")
        expected = condition.get("equals")
        if attribute_name is not None and expected is not None:
            attributes = claims.get("attributes") or {}
            actual = context.get(str(attribute_name), attributes.get(str(attribute_name)))
            return actual == expected
        return True
