"""Custom exceptions for Edge Module."""


class EdgeModuleException(Exception):
    """Base exception for all edge module errors."""
    pass


# ═══════════════════════════════════════════════════════════════
# Camera Exceptions
# ═══════════════════════════════════════════════════════════════

class CameraException(EdgeModuleException):
    """Base for camera-related errors."""
    pass


class CameraNotFoundException(CameraException):
    """No camera device found."""
    pass


class CameraInitializationError(CameraException):
    """Camera failed to initialize."""
    pass


class CameraDisconnectionError(CameraException):
    """Camera disconnected during operation."""
    pass


# ═══════════════════════════════════════════════════════════════
# Queue Exceptions
# ═══════════════════════════════════════════════════════════════

class QueueException(EdgeModuleException):
    """Base for queue-related errors."""
    pass


class FrameQueueFullError(QueueException):
    """Frame queue at capacity."""
    pass


class EventQueueFullError(QueueException):
    """Event queue at capacity."""
    pass


# ═══════════════════════════════════════════════════════════════
# Network Exceptions
# ═══════════════════════════════════════════════════════════════

class NetworkException(EdgeModuleException):
    """Base for network-related errors."""
    pass


class BackendConnectionError(NetworkException):
    """Cannot connect to backend."""
    pass


class BackendTimeoutError(NetworkException):
    """Backend request timed out."""
    pass


class BackendError(NetworkException):
    """Backend returned error response."""
    pass


class BackendClientError(BackendError):
    """4xx client error from backend."""
    
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Client error {status_code}: {message}")


class BackendServerError(BackendError):
    """5xx server error from backend."""
    
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Server error {status_code}: {message}")


# ═══════════════════════════════════════════════════════════════
# Resource Exceptions
# ═══════════════════════════════════════════════════════════════

class ResourceException(EdgeModuleException):
    """Base for resource-related errors."""
    pass


class OutOfMemoryError(ResourceException):
    """System out of memory."""
    pass


class DiskFullError(ResourceException):
    """Disk space exhausted."""
    pass
