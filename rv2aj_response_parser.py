"""
RV-2AJ Response Parser Library

This library provides comprehensive parsing for all response types from the
Mitsubishi RV-2AJ robot controller, including:
- QoK: Success responses
- QeR: Error responses with error code lookup
- Q: Data/informational responses (position, status, etc.)

Usage:
    from rv2aj_response_parser import RV2AJResponseParser
    
    parser = RV2AJResponseParser()
    result = parser.parse("QoK")
    if result.is_success:
        print("Command succeeded!")
    
    result = parser.parse("QeR6020")
    if result.is_error:
        print(f"Error: {result.error_message}")
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum


class ResponseType(Enum):
    """Types of responses from the controller."""
    SUCCESS = "success"      # QoK
    ERROR = "error"          # QeR
    DATA = "data"            # Q with data
    UNKNOWN = "unknown"      # Unrecognized format


@dataclass
class ErrorInfo:
    """Detailed error information."""
    code: str
    level: str  # H (High), L (Low), C (Warning)
    message: str
    cause: Optional[str] = None
    measures: Optional[str] = None
    power_cycle_reset: Optional[bool] = None


@dataclass
class ParsedResponse:
    """
    Parsed response from the RV-2AJ controller.
    
    Attributes:
        raw: Original raw response string
        response_type: Type of response (success, error, data, unknown)
        success: True if QoK response
        error_code: Error code if QeR response
        error_info: Detailed error information if available
        data: Parsed data dictionary for data responses
        data_list: Raw list of semicolon-separated values
    """
    raw: str
    response_type: ResponseType
    success: bool = False
    error_code: Optional[str] = None
    error_info: Optional[ErrorInfo] = None
    data: Dict[str, Any] = field(default_factory=dict)
    data_list: List[str] = field(default_factory=list)
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.response_type == ResponseType.SUCCESS
    
    @property
    def is_error(self) -> bool:
        """Check if response indicates an error."""
        return self.response_type == ResponseType.ERROR
    
    @property
    def is_data(self) -> bool:
        """Check if response contains data."""
        return self.response_type == ResponseType.DATA
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if available."""
        if self.error_info:
            return self.error_info.message
        return None
    
    @property
    def error_level(self) -> Optional[str]:
        """Get error level (H/L/C) if available."""
        if self.error_info:
            return self.error_info.level
        return None
    
    def __str__(self) -> str:
        """String representation of parsed response."""
        if self.is_success:
            return f"Success: {self.raw}"
        elif self.is_error:
            msg = f"Error {self.error_code}: {self.error_message}" if self.error_info else f"Error: {self.raw}"
            return msg
        elif self.is_data:
            return f"Data: {self.data if self.data else self.raw}"
        else:
            return f"Unknown: {self.raw}"


class RV2AJResponseParser:
    """
    Comprehensive parser for RV-2AJ controller responses.
    
    Handles all response types and provides error code lookup from the error codes JSON.
    """
    
    def __init__(self, error_codes_path: str = "RV2AJ_Reference_JSONs/RV2AJ_ErrorCodes.json"):
        """
        Initialize the response parser.
        
        Args:
            error_codes_path: Path to the error codes JSON file
        """
        self.error_codes_path = error_codes_path
        self.error_map: Dict[str, ErrorInfo] = {}
        self._loaded = False
    
    def load_error_codes(self) -> None:
        """Load error codes from JSON file."""
        if self._loaded:
            return
        
        try:
            error_file = Path(self.error_codes_path)
            if not error_file.exists():
                print(f"Warning: Error codes file not found: {self.error_codes_path}")
                self._loaded = True
                return
            
            with open(error_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            errors = data.get("errors", [])
            for entry in errors:
                code = entry.get("code")
                number = entry.get("number")
                level = entry.get("level", "")
                message = entry.get("message", "")
                cause = entry.get("cause")
                measures = entry.get("measures")
                power_cycle = entry.get("power_cycle_reset")
                
                if code:
                    error_info = ErrorInfo(
                        code=code,
                        level=level,
                        message=message,
                        cause=cause,
                        measures=measures,
                        power_cycle_reset=power_cycle
                    )
                    
                    # Store by full code (e.g., "H1110")
                    self.error_map[code] = error_info
                    
                    # Also store by number only (e.g., "1110")
                    if number is not None:
                        self.error_map[str(number)] = error_info
            
            self._loaded = True
            
        except Exception as e:
            print(f"Warning: Failed to load error codes: {e}")
            self._loaded = True
    
    def lookup_error(self, code: str) -> Optional[ErrorInfo]:
        """
        Look up error information by code.
        
        Args:
            code: Error code (e.g., "1110" or "H1110")
            
        Returns:
            ErrorInfo object if found, None otherwise
        """
        self.load_error_codes()
        
        # Try direct lookup
        if code in self.error_map:
            return self.error_map[code]
        
        # Try with level prefixes
        for level in ['H', 'L', 'C']:
            full_code = f"{level}{code}"
            if full_code in self.error_map:
                return self.error_map[full_code]
        
        return None
    
    def _extract_error_code(self, response: str) -> Optional[str]:
        """
        Extract error code from QeR response.
        
        Args:
            response: Raw response string (e.g., "QeR6020")
            
        Returns:
            Error code as string (e.g., "6020")
        """
        if not response:
            return None

        upper = response.upper()
        idx = upper.find("QER")
        if idx == -1:
            return None
        
        # Extract digits after first "QeR" occurrence
        digits = "".join(ch for ch in response[idx + 3:] if ch.isdigit())
        
        if len(digits) >= 4:
            return digits[:4]
        elif len(digits) >= 3:
            return digits.zfill(4)
        
        return None
    
    def _parse_semicolon_data(self, data_part: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parse semicolon-delimited data.
        
        Args:
            data_part: Data portion of response after "QoK" or "Q"
            
        Returns:
            Tuple of (list of values, dictionary of key-value pairs)
        """
        # Split by semicolon
        parts = [p.strip() for p in data_part.split(';') if p.strip()]
        
        # Try to create key-value pairs
        data_dict = {}
        i = 0
        while i < len(parts) - 1:
            key = parts[i]
            value = parts[i + 1]
            
            # Skip invalid keys (like empty strings or special markers)
            if key and not key.startswith('*'):
                data_dict[key] = value
            
            i += 2
        
        return parts, data_dict
    
    def parse(self, response: str) -> ParsedResponse:
        """
        Parse a response from the RV-2AJ controller.
        
        Args:
            response: Raw response string from controller
            
        Returns:
            ParsedResponse object with parsed data
        """
        raw = response.strip() if response else ""
        raw_upper = raw.upper()
        
        if not raw:
            return ParsedResponse(
                raw=raw,
                response_type=ResponseType.UNKNOWN
            )
        
        # QeR (anywhere) - Error response
        if "QER" in raw_upper:
            error_code = self._extract_error_code(raw)
            error_info = None
            
            if error_code:
                error_info = self.lookup_error(error_code)
            
            return ParsedResponse(
                raw=raw,
                response_type=ResponseType.ERROR,
                success=False,
                error_code=error_code,
                error_info=error_info
            )

        # QoK (anywhere) - Success response
        if "QOK" in raw_upper:
            qok_idx = raw_upper.find("QOK")
            data_part = raw[qok_idx + 3:]

            # If trailing QoK appears again at end, strip it
            if data_part.upper().endswith("QOK"):
                data_part = data_part[:-3]

            data_list, data_dict = [], {}
            
            if data_part:
                data_list, data_dict = self._parse_semicolon_data(data_part)
            
            return ParsedResponse(
                raw=raw,
                response_type=ResponseType.SUCCESS,
                success=True,
                data_list=data_list,
                data=data_dict
            )
        
        # Q - Data response
        elif "Q" in raw_upper:
            data_part = raw[1:]
            data_list, data_dict = self._parse_semicolon_data(data_part)
            
            return ParsedResponse(
                raw=raw,
                response_type=ResponseType.DATA,
                success=True,
                data_list=data_list,
                data=data_dict
            )
        
        # Unknown format
        else:
            return ParsedResponse(
                raw=raw,
                response_type=ResponseType.UNKNOWN
            )
    
    def parse_position(self, response: str) -> Optional[Dict[str, float]]:
        """
        Parse position data from JPOSF response.
        
        Args:
            response: Response from JPOSF command (e.g., "QoK;J1;10.5;J2;-5.3;...")
            
        Returns:
            Dictionary mapping joint names to angles, or None if parsing fails
        """
        parsed = self.parse(response)
        
        if not (parsed.is_success or parsed.is_data):
            return None
        
        positions = {}
        for key, value in parsed.data.items():
            # Check if key is a joint name (J1, J2, etc.)
            if key.startswith('J') and len(key) == 2:
                try:
                    positions[key] = float(value)
                except (ValueError, TypeError):
                    continue
        
        return positions if positions else None
    
    def parse_coordinates(self, response: str) -> Optional[Dict[str, float]]:
        """
        Parse coordinate data from WH (Where) response.
        
        Args:
            response: Response from WH command (e.g., "QoK;X;100.5;Y;200.3;Z;300.1;...")
            
        Returns:
            Dictionary mapping coordinate names to values, or None if parsing fails
        """
        parsed = self.parse(response)
        
        if not (parsed.is_success or parsed.is_data):
            return None
        
        coords = {}
        for key, value in parsed.data.items():
            # Common coordinate keys: X, Y, Z, A, B, C
            if key in ['X', 'Y', 'Z', 'A', 'B', 'C']:
                try:
                    coords[key] = float(value)
                except (ValueError, TypeError):
                    continue
        
        return coords if coords else None
    
    def extract_value(self, response: str) -> Optional[str]:
        """
        Extract a single value from a response.
        Useful for commands that return a single value.
        
        Args:
            response: Response from controller
            
        Returns:
            First data value as string, or None if not available
        """
        parsed = self.parse(response)
        
        if parsed.data_list and len(parsed.data_list) > 0:
            return parsed.data_list[0]
        
        return None


# Convenience functions for common use cases
def is_success(response: str) -> bool:
    """Check if response indicates success."""
    text = response.strip().upper()
    return "QOK" in text and "QER" not in text


def is_error(response: str) -> bool:
    """Check if response indicates an error."""
    return "QER" in response.strip().upper()


def get_error_code(response: str) -> Optional[str]:
    """Extract error code from error response."""
    if not is_error(response):
        return None
    
    digits = "".join(ch for ch in response[3:] if ch.isdigit())
    if len(digits) >= 4:
        return digits[:4]
    elif len(digits) >= 3:
        return digits.zfill(4)
    return None


# Example usage and testing
if __name__ == "__main__":
    parser = RV2AJResponseParser()
    
    print("="*60)
    print("RV-2AJ Response Parser - Examples")
    print("="*60)
    
    # Test success response
    print("\n1. Success Response:")
    result = parser.parse("QoK")
    print(f"   Raw: {result.raw}")
    print(f"   Type: {result.response_type.value}")
    print(f"   Is Success: {result.is_success}")
    print(f"   String: {result}")
    
    # Test error response
    print("\n2. Error Response:")
    result = parser.parse("QeR6020")
    print(f"   Raw: {result.raw}")
    print(f"   Type: {result.response_type.value}")
    print(f"   Is Error: {result.is_error}")
    print(f"   Error Code: {result.error_code}")
    if result.error_info:
        print(f"   Error Level: {result.error_info.level}")
        print(f"   Message: {result.error_info.message}")
        print(f"   Cause: {result.error_info.cause}")
        print(f"   Measures: {result.error_info.measures}")
    print(f"   String: {result}")
    
    # Test position data
    print("\n3. Position Data Response:")
    result = parser.parse("QoK;J1;10.50;J2;-5.30;J3;45.00;J5;0.00;J6;90.00")
    print(f"   Raw: {result.raw}")
    print(f"   Type: {result.response_type.value}")
    print(f"   Data Dict: {result.data}")
    positions = parser.parse_position(result.raw)
    if positions:
        print(f"   Positions: {positions}")
    
    # Test coordinate data
    print("\n4. Coordinate Data Response:")
    result = parser.parse("QoK;X;100.5;Y;200.3;Z;300.1;A;0.0;B;0.0;C;90.0")
    print(f"   Raw: {result.raw}")
    print(f"   Data Dict: {result.data}")
    coords = parser.parse_coordinates(result.raw)
    if coords:
        print(f"   Coordinates: {coords}")
    
    # Test simple data response
    print("\n5. Simple Data Response:")
    result = parser.parse("Q;1;2;3")
    print(f"   Raw: {result.raw}")
    print(f"   Type: {result.response_type.value}")
    print(f"   Data List: {result.data_list}")
    
    # Test convenience functions
    print("\n6. Convenience Functions:")
    print(f"   is_success('QoK'): {is_success('QoK')}")
    print(f"   is_error('QeR1110'): {is_error('QeR1110')}")
    print(f"   get_error_code('QeR1110'): {get_error_code('QeR1110')}")
    
    print("\n" + "="*60)
