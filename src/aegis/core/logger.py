# src/aegis/core/logger.py
#
# DEPRECATED: This module is retained only for backward compatibility.
# All new code should use aegis.logger.event_logger.EventLogger and
# aegis.core.constants.EventType directly.
#
# The duplicate EventType enum that was here has been removed to
# prevent silent import conflicts with core.constants.EventType.

import logging
from aegis.core.constants import EventType
from aegis.logger.event_logger import EventLogger as _EventLogger, get_event_logger

# Re-export for backward compatibility
__all__ = ['EventType', 'get_event_logger']
