"""
Buffer Overflow Protection for Django Application

This module provides comprehensive protection against buffer overflow attacks
by implementing input validation, size limits, and sanitization.
"""

from django.http import HttpResponseBadRequest
from django.core.exceptions import ValidationError
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging
import re
import json

logger = logging.getLogger('security')

# Configuration constants
MAX_REQUEST_SIZE = getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB
MAX_FIELD_LENGTH = getattr(settings, 'MAX_FIELD_LENGTH', 10000)  # 10KB per field
MAX_POST_FIELDS = getattr(settings, 'MAX_POST_FIELDS', 100)  # Max number of POST fields
MAX_HEADER_SIZE = getattr(settings, 'MAX_HEADER_SIZE', 8192)  # 8KB per header
MAX_URL_LENGTH = getattr(settings, 'MAX_URL_LENGTH', 2048)  # 2KB URL length

# Dangerous patterns that could indicate buffer overflow attempts
DANGEROUS_PATTERNS = [
    rb'\x00' * 100,  # Null byte flooding
    rb'A' * 1000,    # Character flooding
    rb'\x90' * 100,  # NOP sled (common in buffer overflows)
    rb'\xff' * 100,  # 0xFF flooding
    rb'%s' * 50,     # Format string attacks
    rb'%x' * 50,     # Format string attacks
    rb'/../' * 20,   # Path traversal flooding
    rb'<script' * 10, # Script injection flooding
]

class BufferOverflowProtectionMiddleware(MiddlewareMixin):
    """
    Middleware to protect against buffer overflow attacks
    """
    
    def process_request(self, request):
        """Check request for buffer overflow indicators"""
        try:
            # 1. Check total request size
            if hasattr(request, 'META') and 'CONTENT_LENGTH' in request.META:
                content_length_str = request.META.get('CONTENT_LENGTH', '0')
                try:
                    content_length = int(content_length_str) if content_length_str else 0
                    if content_length > MAX_REQUEST_SIZE:
                        logger.warning(f"Request size too large: {content_length} bytes from {self._get_client_ip(request)}")
                        return HttpResponseBadRequest("Request too large")
                except ValueError:
                    # Invalid content length, treat as 0
                    content_length = 0
            
            # 2. Check URL length
            if len(request.get_full_path()) > MAX_URL_LENGTH:
                logger.warning(f"URL too long: {len(request.get_full_path())} chars from {self._get_client_ip(request)}")
                return HttpResponseBadRequest("URL too long")
            
            # 3. Check headers for suspicious patterns
            for header_name, header_value in request.META.items():
                if isinstance(header_value, str):
                    # Check header size
                    if len(header_value) > MAX_HEADER_SIZE:
                        logger.warning(f"Header too long: {header_name} from {self._get_client_ip(request)}")
                        return HttpResponseBadRequest("Header too long")
                    
                    # Check for dangerous patterns
                    if self._contains_dangerous_pattern(header_value.encode('utf-8', errors='ignore')):
                        logger.warning(f"Dangerous pattern in header {header_name} from {self._get_client_ip(request)}")
                        return HttpResponseBadRequest("Invalid header content")
            
            # 4. Check POST data
            if request.method == 'POST':
                # Check number of POST fields
                if hasattr(request, 'POST') and len(request.POST) > MAX_POST_FIELDS:
                    logger.warning(f"Too many POST fields: {len(request.POST)} from {self._get_client_ip(request)}")
                    return HttpResponseBadRequest("Too many form fields")
                
                # Check individual field lengths
                for field_name, field_value in request.POST.items():
                    if isinstance(field_value, str) and len(field_value) > MAX_FIELD_LENGTH:
                        logger.warning(f"Field too long: {field_name} ({len(field_value)} chars) from {self._get_client_ip(request)}")
                        return HttpResponseBadRequest("Form field too long")
                    
                    # Check for dangerous patterns
                    if isinstance(field_value, str):
                        if self._contains_dangerous_pattern(field_value.encode('utf-8', errors='ignore')):
                            logger.warning(f"Dangerous pattern in field {field_name} from {self._get_client_ip(request)}")
                            return HttpResponseBadRequest("Invalid form content")
            
            return None
            
        except Exception as e:
            logger.error(f"Buffer overflow protection error: {e}")
            return HttpResponseBadRequest("Request processing error")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _contains_dangerous_pattern(self, data):
        """Check if data contains dangerous patterns"""
        for pattern in DANGEROUS_PATTERNS:
            if pattern in data:
                return True
        return False


def validate_input_length(value, max_length=MAX_FIELD_LENGTH, field_name="field"):
    """
    Validate input length to prevent buffer overflow
    """
    if isinstance(value, str):
        if len(value) > max_length:
            raise ValidationError(f"{field_name} is too long (max {max_length} characters)")
        
        # Check for null bytes
        if '\x00' in value:
            raise ValidationError(f"{field_name} contains invalid null bytes")
        
        # Check for dangerous patterns
        if _contains_dangerous_pattern_str(value):
            raise ValidationError(f"{field_name} contains potentially dangerous content")
    
    return value


def validate_numeric_input(value, min_val=None, max_val=None, field_name="field"):
    """
    Validate numeric input to prevent overflow
    """
    try:
        if isinstance(value, str):
            # Check for extremely long numeric strings
            if len(value) > 50:  # No legitimate number should be this long
                raise ValidationError(f"{field_name} numeric value too long")
            
            # Try to convert to number
            float_val = float(value)
            
            # Check ranges
            if min_val is not None and float_val < min_val:
                raise ValidationError(f"{field_name} must be at least {min_val}")
            
            if max_val is not None and float_val > max_val:
                raise ValidationError(f"{field_name} must be at most {max_val}")
                
        return value
    except ValueError:
        raise ValidationError(f"{field_name} must be a valid number")


def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal and buffer overflow
    """
    if not filename:
        return ""
    
    # Limit filename length
    if len(filename) > 255:
        filename = filename[:255]
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Remove path traversal attempts
    filename = re.sub(r'\.\.+', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    return filename


def _contains_dangerous_pattern_str(data):
    """Check if string data contains dangerous patterns"""
    try:
        byte_data = data.encode('utf-8', errors='ignore')
        for pattern in DANGEROUS_PATTERNS:
            if pattern in byte_data:
                return True
        return False
    except:
        return True  # If we can't check safely, assume dangerous


class SecureJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that prevents buffer overflow in JSON responses
    """
    def encode(self, obj):
        result = super().encode(obj)
        if len(result) > MAX_REQUEST_SIZE:
            raise ValueError("JSON response too large")
        return result


def secure_json_response(data):
    """
    Create a secure JSON response with size limits
    """
    try:
        json_str = json.dumps(data, cls=SecureJSONEncoder)
        return json_str
    except ValueError as e:
        logger.warning(f"JSON response too large: {e}")
        return json.dumps({"error": "Response too large"})


# Custom form field validators
class SecureCharField:
    """
    Secure character field with buffer overflow protection
    """
    def __init__(self, max_length=1000, field_name="field"):
        self.max_length = max_length
        self.field_name = field_name
    
    def __call__(self, value):
        return validate_input_length(value, self.max_length, self.field_name)


class SecureNumericField:
    """
    Secure numeric field with overflow protection
    """
    def __init__(self, min_val=None, max_val=None, field_name="field"):
        self.min_val = min_val
        self.max_val = max_val
        self.field_name = field_name
    
    def __call__(self, value):
        return validate_numeric_input(value, self.min_val, self.max_val, self.field_name)
