"""
Intent Detection Module - Rule-based and AI-powered
"""

from .detector import IntentDetector

try:
    from .gemini_detector import GeminiIntentDetector, HybridIntentDetector
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

__all__ = ['IntentDetector']
if AI_AVAILABLE:
    __all__.extend(['GeminiIntentDetector', 'HybridIntentDetector'])
