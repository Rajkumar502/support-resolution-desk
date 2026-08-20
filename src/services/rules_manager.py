import json
from pathlib import Path

class RulesManager:
    _rules_path = Path(__file__).parent.parent / "config" / "rules.json"
    _cached_rules = None
    _last_mtime = 0

    @classmethod
    def _load_rules(cls) -> dict:
        """Loads rules from JSON with automatic hot-reloading if the file changes."""
        if not cls._rules_path.exists():
            return {}
        
        current_mtime = cls._rules_path.stat().st_mtime
        if cls._cached_rules is None or current_mtime > cls._last_mtime:
            with open(cls._rules_path, "r") as f:
                cls._cached_rules = json.load(f)
                cls._last_mtime = current_mtime
                
        return cls._cached_rules

    @classmethod
    def get_confidence_threshold(cls, category: str) -> float:
        """Retrieves the confidence threshold for a specific category."""
        rules = cls._load_rules()
        thresholds = rules.get("confidence_thresholds", {})
        return thresholds.get(category, thresholds.get("default", 0.85))

    @classmethod
    def get_injection_keywords(cls) -> list:
        """Retrieves active prompt injection keywords from rules config."""
        rules = cls._load_rules()
        return rules.get("guardrails", {}).get("injection_keywords", [])

    @classmethod
    def get_auto_responder_subjects(cls) -> list:
        """Retrieves auto-responder subject triggers from rules config."""
        rules = cls._load_rules()
        return rules.get("guardrails", {}).get("auto_responder_subjects", [])

    @classmethod
    def should_force_escalation(cls, category: str) -> bool:
        """Checks if a category must always be forced to human support."""
        rules = cls._load_rules()
        force_list = rules.get("escalation_triggers", {}).get("force_human_categories", [])
        return category in force_list