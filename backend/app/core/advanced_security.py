"""
Advanced Security Module - Protection contre les attaques sophistiquées
Backdoors, Reverse Shells, Command Injection, Path Traversal, etc.
"""
import re
import os
import hashlib
import logging
from typing import Optional, Set, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# ============================================================================
# COMMAND INJECTION PROTECTION
# ============================================================================

# Patterns that indicate command injection attempts
COMMAND_INJECTION_PATTERNS = [
    r";\s*\w+",  # ;command
    r"\|\s*\w+",  # |command
    r"\|\|",  # ||
    r"&&",  # &&
    r"\$\(",  # $(command)
    r"`[^`]+`",  # `command`
    r"\$\{",  # ${var}
    r">\s*/",  # > /path (redirect to file)
    r">>\s*/",  # >> /path (append to file)
    r"<\s*/",  # < /path (read from file)
    r"\bnc\b.*-e",  # netcat reverse shell
    r"\bnetcat\b",
    r"\bbash\s+-i",  # bash interactive
    r"\bsh\s+-i",  # sh interactive
    r"\bpython\s+-c",  # python one-liner
    r"\bperl\s+-e",  # perl one-liner
    r"\bruby\s+-e",  # ruby one-liner
    r"\bphp\s+-r",  # php one-liner
    r"\bwget\b.*\|",  # wget piped
    r"\bcurl\b.*\|",  # curl piped
    r"\bchmod\b",  # chmod
    r"\bchown\b",  # chown
    r"\brm\s+-rf",  # rm -rf
    r"\bmkfifo\b",  # named pipe (reverse shell)
    r"/dev/tcp/",  # bash reverse shell
    r"/dev/udp/",  # bash reverse shell
    r"\beval\s*\(",  # eval()
    r"\bexec\s*\(",  # exec()
    r"\bsystem\s*\(",  # system()
    r"\bpopen\s*\(",  # popen()
    r"\bsubprocess",  # subprocess module
    r"\b__import__",  # dynamic import
    r"\bos\.system",  # os.system
    r"\bos\.popen",  # os.popen
    r"\bos\.exec",  # os.exec*
    r"\bos\.spawn",  # os.spawn*
    r"\bpty\.spawn",  # pty.spawn
]

# Reverse shell signatures
REVERSE_SHELL_PATTERNS = [
    r"bash\s+-i\s+>&\s*/dev/tcp",
    r"nc\s+-e\s+/bin/(ba)?sh",
    r"python\s+-c\s+['\"]import\s+socket",
    r"perl\s+-e\s+['\"]use\s+Socket",
    r"php\s+-r\s+['\"].*fsockopen",
    r"ruby\s+-rsocket\s+-e",
    r"socat\s+exec:",
    r"telnet\s+\S+\s+\d+\s*\|\s*/bin/(ba)?sh",
    r"mkfifo\s+/tmp/",
    r"0<&\d+-;\s*exec",
]


def detect_command_injection(text: str) -> bool:
    """Detect command injection attempts"""
    if not text:
        return False
    
    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_reverse_shell(text: str) -> bool:
    """Detect reverse shell attempts"""
    if not text:
        return False
    
    for pattern in REVERSE_SHELL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ============================================================================
# PATH TRAVERSAL PROTECTION
# ============================================================================

PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",  # ../
    r"\.\.\\",  # ..\
    r"%2e%2e%2f",  # URL encoded ../
    r"%2e%2e/",
    r"\.%2e/",
    r"%2e\./",
    r"\.\.%5c",  # URL encoded ..\
    r"%252e%252e",  # Double encoded
    r"/etc/passwd",
    r"/etc/shadow",
    r"/etc/hosts",
    r"/proc/self",
    r"/dev/null",
    r"c:\\windows",
    r"c:/windows",
    r"\\\\",  # UNC path
]


def detect_path_traversal(text: str) -> bool:
    """Detect path traversal attempts"""
    if not text:
        return False
    
    text_lower = text.lower()
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


# ============================================================================
# SUSPICIOUS PAYLOAD DETECTION
# ============================================================================

SUSPICIOUS_PAYLOADS = [
    # PHP backdoors
    r"<\?php",
    r"<\?=",
    r"eval\s*\(\s*base64_decode",
    r"eval\s*\(\s*gzinflate",
    r"eval\s*\(\s*\$_",
    r"assert\s*\(\s*\$_",
    r"preg_replace.*\/e",
    r"create_function\s*\(",
    
    # Python backdoors
    r"__builtins__",
    r"__globals__",
    r"__class__",
    r"__mro__",
    r"__subclasses__",
    r"__getattribute__",
    r"importlib\.import_module",
    r"pickle\.loads",
    r"marshal\.loads",
    r"yaml\.load\s*\([^)]*Loader\s*=\s*None",
    r"yaml\.unsafe_load",
    
    # Serialization attacks
    r"O:\d+:\"",  # PHP serialized object
    r"rO0AB",  # Java serialized (base64)
    r"aced0005",  # Java serialized (hex)
    
    # Template injection
    r"\{\{\s*config",
    r"\{\{\s*self",
    r"\{\{\s*request",
    r"\{\%.*import.*\%\}",
    r"\$\{.*java\.lang",
    r"#\{.*Runtime",
    
    # LDAP injection
    r"\)\(\|",
    r"\*\)\(",
    
    # XXE
    r"<!ENTITY",
    r"<!DOCTYPE.*SYSTEM",
    r"file:///",
    r"expect://",
    r"php://filter",
    
    # SSRF
    r"gopher://",
    r"dict://",
    r"ftp://.*@",
    r"http://127\.0\.0\.1",
    r"http://localhost",
    r"http://0\.0\.0\.0",
    r"http://\[::1\]",
    r"http://169\.254\.",  # AWS metadata
    r"http://metadata\.",
]


def detect_suspicious_payload(text: str) -> Optional[str]:
    """Detect suspicious payloads. Returns matched pattern or None."""
    if not text:
        return None
    
    for pattern in SUSPICIOUS_PAYLOADS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return pattern
    return None


# ============================================================================
# FILE UPLOAD SECURITY
# ============================================================================

# Dangerous file extensions that should never be uploaded
DANGEROUS_EXTENSIONS = {
    # Executable
    '.exe', '.dll', '.so', '.dylib', '.bin', '.run',
    '.bat', '.cmd', '.com', '.msi', '.msp',
    '.ps1', '.psm1', '.psd1',  # PowerShell
    '.vbs', '.vbe', '.js', '.jse', '.ws', '.wsf', '.wsc', '.wsh',  # Windows Script
    
    # Server-side scripts
    '.php', '.php3', '.php4', '.php5', '.php7', '.phtml', '.phar',
    '.asp', '.aspx', '.ascx', '.ashx', '.asmx', '.cer',
    '.jsp', '.jspx', '.jsw', '.jsv', '.jspf',
    '.cgi', '.pl', '.py', '.rb', '.sh', '.bash',
    
    # Config files that could override server config
    '.htaccess', '.htpasswd', '.config', '.conf',
    
    # Other dangerous
    '.scr', '.pif', '.application', '.gadget',
    '.hta', '.cpl', '.msc', '.jar', '.war',
    '.swf',  # Flash
}

# Magic bytes for file type verification
FILE_SIGNATURES = {
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'\xff\xd8\xff': 'image/jpeg',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'%PDF': 'application/pdf',
    b'PK\x03\x04': 'application/zip',
    b'\x1f\x8b\x08': 'application/gzip',
}


def is_dangerous_extension(filename: str) -> bool:
    """Check if file has a dangerous extension"""
    if not filename:
        return False
    
    ext = Path(filename).suffix.lower()
    # Also check for double extensions like .php.jpg
    all_suffixes = ''.join(Path(filename).suffixes).lower()
    
    for dangerous in DANGEROUS_EXTENSIONS:
        if ext == dangerous or dangerous in all_suffixes:
            return True
    return False


def verify_file_signature(content: bytes, claimed_type: str) -> bool:
    """Verify file content matches claimed MIME type"""
    for signature, mime_type in FILE_SIGNATURES.items():
        if content.startswith(signature):
            # Check if claimed type matches or is compatible
            if claimed_type and mime_type.split('/')[0] in claimed_type:
                return True
            if claimed_type == mime_type:
                return True
    return False


# ============================================================================
# SESSION SECURITY
# ============================================================================

class SessionSecurityManager:
    """Track and validate sessions to prevent hijacking"""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.suspicious_ips: Dict[str, List[datetime]] = {}
    
    def create_session(self, token_hash: str, ip: str, user_agent: str):
        """Record session metadata"""
        self.sessions[token_hash] = {
            'ip': ip,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'last_seen': datetime.utcnow(),
        }
    
    def validate_session(self, token_hash: str, ip: str, user_agent: str) -> bool:
        """
        Validate session hasn't been hijacked.
        Returns False if suspicious activity detected.
        """
        if token_hash not in self.sessions:
            return True  # New session, will be created
        
        session = self.sessions[token_hash]
        
        # IP changed? Could be hijacking
        if session['ip'] != ip:
            logger.warning(f"Session IP changed: {session['ip']} -> {ip}")
            self._record_suspicious(ip)
            return False
        
        # User agent changed significantly? Suspicious
        if session['user_agent'] and user_agent:
            if self._ua_changed_significantly(session['user_agent'], user_agent):
                logger.warning(f"Session UA changed suspiciously")
                self._record_suspicious(ip)
                return False
        
        # Update last seen
        session['last_seen'] = datetime.utcnow()
        return True
    
    def _ua_changed_significantly(self, old_ua: str, new_ua: str) -> bool:
        """Check if user agent changed in a suspicious way"""
        # Extract browser/OS from UA
        old_parts = old_ua.lower().split()[:3]
        new_parts = new_ua.lower().split()[:3]
        
        # If first 3 words are completely different, suspicious
        if not any(p in new_parts for p in old_parts):
            return True
        return False
    
    def _record_suspicious(self, ip: str):
        """Record suspicious activity from IP"""
        if ip not in self.suspicious_ips:
            self.suspicious_ips[ip] = []
        self.suspicious_ips[ip].append(datetime.utcnow())
        
        # Clean old records
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.suspicious_ips[ip] = [
            t for t in self.suspicious_ips[ip] if t > cutoff
        ]
    
    def is_ip_suspicious(self, ip: str, threshold: int = 5) -> bool:
        """Check if IP has too many suspicious activities"""
        if ip not in self.suspicious_ips:
            return False
        return len(self.suspicious_ips[ip]) >= threshold
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove old sessions"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = [
            token for token, session in self.sessions.items()
            if session['last_seen'] < cutoff
        ]
        for token in to_remove:
            del self.sessions[token]


# Global session manager
session_manager = SessionSecurityManager()


# ============================================================================
# INTEGRITY MONITORING
# ============================================================================

class IntegrityMonitor:
    """Monitor critical files for unauthorized changes"""
    
    def __init__(self, critical_paths: List[str] = None):
        self.critical_paths = critical_paths or []
        self.file_hashes: Dict[str, str] = {}
        self.last_check = datetime.utcnow()
    
    def add_critical_path(self, path: str):
        """Add a path to monitor"""
        self.critical_paths.append(path)
        self._hash_file(path)
    
    def _hash_file(self, path: str) -> Optional[str]:
        """Calculate SHA256 hash of file"""
        try:
            with open(path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (IOError, OSError):
            return None
    
    def initialize(self):
        """Hash all critical files"""
        for path in self.critical_paths:
            file_hash = self._hash_file(path)
            if file_hash:
                self.file_hashes[path] = file_hash
                logger.info(f"Integrity baseline set for: {path}")
    
    def check_integrity(self) -> List[str]:
        """Check if any critical files have changed. Returns list of modified files."""
        modified = []
        
        for path in self.critical_paths:
            current_hash = self._hash_file(path)
            if current_hash is None:
                # File deleted or inaccessible
                if path in self.file_hashes:
                    logger.critical(f"INTEGRITY ALERT: File missing: {path}")
                    modified.append(path)
            elif path not in self.file_hashes:
                # New file
                self.file_hashes[path] = current_hash
            elif current_hash != self.file_hashes[path]:
                # File modified
                logger.critical(f"INTEGRITY ALERT: File modified: {path}")
                modified.append(path)
        
        self.last_check = datetime.utcnow()
        return modified


# ============================================================================
# ADVANCED SECURITY MIDDLEWARE
# ============================================================================

class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security checks for all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Get request details
        path = request.url.path
        query = str(request.query_params)
        ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # 1. Check for path traversal in URL
        if detect_path_traversal(path) or detect_path_traversal(query):
            logger.critical(f"PATH TRAVERSAL BLOCKED: {path} from {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # 2. Check for command injection in query params
        if detect_command_injection(query):
            logger.critical(f"COMMAND INJECTION BLOCKED: {query} from {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # 3. Check for reverse shell attempts
        if detect_reverse_shell(query):
            logger.critical(f"REVERSE SHELL BLOCKED: {query} from {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # 4. Check suspicious payloads
        payload_match = detect_suspicious_payload(query)
        if payload_match:
            logger.critical(f"SUSPICIOUS PAYLOAD BLOCKED: {payload_match} from {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # 5. Check if IP is marked as suspicious
        if session_manager.is_ip_suspicious(ip):
            logger.warning(f"SUSPICIOUS IP BLOCKED: {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access temporarily blocked"}
            )
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"


class FileUploadSecurityMiddleware(BaseHTTPMiddleware):
    """Security checks for file uploads"""
    
    UPLOAD_PATHS = ["/api/v1/assets", "/api/v1/drive"]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Only check upload endpoints
        if not any(path.startswith(p) for p in self.UPLOAD_PATHS):
            return await call_next(request)
        
        if request.method != "POST":
            return await call_next(request)
        
        # Check content type
        content_type = request.headers.get("Content-Type", "")
        
        # For multipart form data (file uploads)
        if "multipart/form-data" in content_type:
            # We can't easily read the body here without breaking the request
            # The file validation should be done in the endpoint
            pass
        
        return await call_next(request)


# ============================================================================
# HONEYPOT ENDPOINTS
# ============================================================================

HONEYPOT_PATHS = {
    "/admin.php",
    "/wp-admin",
    "/wp-login.php",
    "/administrator",
    "/phpmyadmin",
    "/phpMyAdmin",
    "/pma",
    "/mysql",
    "/adminer.php",
    "/backup.sql",
    "/db.sql",
    "/database.sql",
    "/dump.sql",
    "/.git/config",
    "/.env",
    "/.svn/entries",
    "/config.php",
    "/configuration.php",
    "/settings.php",
    "/shell.php",
    "/c99.php",
    "/r57.php",
    "/b374k.php",
    "/webshell.php",
    "/cmd.php",
    "/upload.php",
    "/eval.php",
    "/backdoor.php",
}


class HoneypotMiddleware(BaseHTTPMiddleware):
    """
    Honeypot endpoints to detect attackers.
    Anyone accessing these is definitely malicious.
    """
    
    def __init__(self, app, blocked_ips: set = None):
        super().__init__(app)
        self.blocked_ips: Set[str] = blocked_ips or set()
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path.lower()
        ip = self._get_client_ip(request)
        
        # Check if accessing honeypot
        if path in HONEYPOT_PATHS or any(path.endswith(hp) for hp in HONEYPOT_PATHS):
            logger.critical(f"HONEYPOT TRIGGERED: {path} from {ip}")
            
            # Block this IP
            self.blocked_ips.add(ip)
            
            # Return fake 404 to not reveal honeypot
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"}
            )
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            logger.warning(f"BLOCKED IP attempted access: {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ============================================================================
# EXPORT SECURITY FUNCTIONS FOR ENDPOINT USE
# ============================================================================

def validate_file_upload(filename: str, content: bytes, max_size_mb: int = 10) -> tuple[bool, str]:
    """
    Validate file upload for security.
    Returns (is_valid, error_message)
    """
    # Check file size
    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        return False, f"File too large (max {max_size_mb}MB)"
    
    # Check extension
    if is_dangerous_extension(filename):
        logger.warning(f"Dangerous file upload blocked: {filename}")
        return False, "File type not allowed"
    
    # Check for null bytes in filename (bypass attempt)
    if '\x00' in filename:
        logger.warning(f"Null byte in filename blocked: {filename!r}")
        return False, "Invalid filename"
    
    # Check content for PHP/script tags
    try:
        content_preview = content[:1024].decode('utf-8', errors='ignore')
        if detect_suspicious_payload(content_preview):
            logger.warning(f"Suspicious content in upload: {filename}")
            return False, "Suspicious file content detected"
    except:
        pass
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other attacks"""
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Remove other dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Ensure it's not empty
    if not filename or filename.strip() == '':
        filename = 'unnamed_file'
    
    return filename
