"""
DankerChat - Multi-interface chat application with Flask backend and real-time messaging.

A modern chat application supporting web, CLI, and REST API interfaces with
real-time messaging via WebSocket, user authentication, and admin functionality.
"""

__version__ = "0.1.0"
__author__ = "DankerChat Team"
__email__ = "team@dankerchat.dev"
__description__ = (
    "Multi-interface chat application with Flask backend and real-time messaging"
)

# Import main components for easy access
try:
    from .client import DankerChatClient
    from .server import create_app
except ImportError:
    # Modules not yet implemented - this is expected during initial setup
    pass

__all__ = ["create_app", "DankerChatClient", "__version__"]
