from typing import Any, Dict, List


class ActionSelectionResponse:
    def __init__(self, action: str, parameters: Dict[str, Any], reason: str = ""):
        self.action = action
        self.parameters = parameters
        self.reason = reason

    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "parameters": self.parameters,
            "reason": self.reason,
        }


class AnalysisResponse:
    def __init__(self, answer: str, action: str, success: bool = True, error: str = ""):
        self.answer = answer
        self.action = action
        self.success = success
        self.error = error

    def to_dict(self) -> Dict:
        result = {
            "answer": self.answer,
            "action": self.action,
            "success": self.success,
        }
        if self.error:
            result["error"] = self.error
        return result
