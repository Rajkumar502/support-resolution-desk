import re
from src.services.rules_manager import RulesManager

class GuardrailsService:
    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        """Checks text against prompt injection patterns, safely ignoring empty rules."""
        text_lower = text.lower()
        keywords = RulesManager.get_injection_keywords()
        
        # Filter out empty or whitespace-only strings to prevent matching everything
        valid_keywords = [kw.lower().strip() for kw in keywords if kw and kw.strip()]
        
        for keyword in valid_keywords:
            if keyword in text_lower:
                print(f"🚨 [GUARDRAIL] Triggered by keyword: '{keyword}'")
                return True
                
        return False

    @staticmethod
    def is_auto_responder(subject: str, text: str) -> bool:
        """Checks if email is an automated out-of-office notification."""
        subject_lower = subject.lower()
        auto_subjects = RulesManager.get_auto_responder_subjects()
        valid_subjects = [sub.lower().strip() for sub in auto_subjects if sub and sub.strip()]
        return any(sub in subject_lower for sub in valid_subjects)

    @staticmethod
    def mask_pii(text: str) -> str:
        """Masks phone numbers and emails for privacy compliance."""
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b', '[REDACTED_PHONE]', text)
        return text