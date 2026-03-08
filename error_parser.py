import json
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ParsedResponse:
    raw: str
    kind: str  # "ok" | "error" | "info" | "unknown"
    code: Optional[str] = None
    message: Optional[str] = None


class ErrorCodeParser:
    def __init__(self, json_path: str = "RV2AJ_Reference_JSONs/RV2AJ_ErrorCodes.json"):
        self.json_path = json_path
        self.error_map: Dict[str, str] = {}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        errors = data.get("errors", [])
        for entry in errors:
            code = entry.get("code")
            number = entry.get("number")
            message = entry.get("message")
            cause = entry.get("cause")
            measures = entry.get("measures")
            if code and message:
                parts = [message]
                if cause:
                    parts.append(f"Cause: {cause}")
                if measures:
                    parts.append(f"Measures: {measures}")
                text = " ".join(parts).strip()
                self.error_map[code] = text
                if number is not None:
                    self.error_map[str(number)] = text
        self._loaded = True

    def lookup(self, code: str) -> Optional[str]:
        self.load()
        return self.error_map.get(code)


def _extract_error_code(response: str) -> Optional[str]:
    # Example: QeR6020 -> 6020
    if not response:
        return None
    upper = response.upper()
    idx = upper.find("QER")
    if idx == -1:
        return None
    digits = "".join(ch for ch in response[idx + 3:] if ch.isdigit())
    if len(digits) >= 4:
        return digits[:4]
    if len(digits) >= 3:
        return digits.zfill(4)
    return None


def parse_response(response: str, parser: Optional[ErrorCodeParser] = None) -> ParsedResponse:
    raw = response.strip() if response else ""
    raw_upper = raw.upper()

    if "QER" in raw_upper:
        code = _extract_error_code(raw)
        message = None
        if parser and code:
            message = parser.lookup(code) or parser.lookup(f"H{code}")
        return ParsedResponse(raw=raw, kind="error", code=code, message=message)
    if "QOK" in raw_upper:
        return ParsedResponse(raw=raw, kind="ok")
    if "Q" in raw_upper:
        return ParsedResponse(raw=raw, kind="info")
    return ParsedResponse(raw=raw, kind="unknown")


if __name__ == "__main__":
    parser = ErrorCodeParser()
    sample = "QeR510000000"
    result = parse_response(sample, parser)
    print(result)
