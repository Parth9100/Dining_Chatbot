"""
AI-Powered Intent Detection using Google Gemini API
Provides smarter natural language understanding compared to rule-based detection.
Falls back to rule-based if API is unavailable.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Intent:
    """Represents a detected intent with confidence and entities."""
    name: str
    confidence: float
    entities: Dict[str, Any]
    raw_input: str


class GeminiIntentDetector:
    """
    AI-powered intent detection using Google Gemini API.
    
    Benefits over rule-based:
    - Understands complex/ambiguous queries
    - Handles typos and variations
    - Extracts entities more accurately
    - Natural conversation understanding
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with config file path."""
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent.parent.parent / "config.json"
        
        self.api_key = None
        self.model = "gemini-2.0-flash"
        self.enabled = False
        
        self._load_config()
    
    def _load_config(self):
        """Load API configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                gemini_config = config.get('gemini', {})
                self.api_key = gemini_config.get('api_key')
                self.model = gemini_config.get('model', 'gemini-2.0-flash')
                
                if self.api_key and not self.api_key.startswith('YOUR_'):
                    self.enabled = True
        except Exception as e:
            print(f"Warning: Could not load Gemini config: {e}")
    
    def _create_prompt(self, user_input: str) -> str:
        """Create the prompt for Gemini to detect intent."""
        return f'''You are an intent detection system for a restaurant reservation chatbot.

Analyze the user message and respond with ONLY a JSON object (no markdown, no explanation).

Available intents:
- greeting: User says hello/hi
- goodbye: User wants to exit
- help: User needs assistance
- menu_query: User wants to see menu/dishes
- book_table: User wants to make a reservation
- cancel_booking: User wants to cancel
- check_availability: User checks table availability
- recommend: User wants dish recommendations
- unknown: Cannot determine intent

Extract these entities if present:
- category: Appetizers, Main Course, Desserts, Beverages
- food_type: Veg, Non-Veg, Vegan
- max_price: number (if user mentions "under $X")
- min_price: number (if user mentions "over $X")
- party_size: number of people
- date: YYYY-MM-DD format (convert "today", "tomorrow" to actual dates)
- time: time slot like "19:00-20:00" or "7pm"
- booking_id: booking reference number

Today's date is 2026-02-07.

User message: "{user_input}"

Respond with JSON only:
{{"intent": "intent_name", "confidence": 0.0-1.0, "entities": {{}}}}'''

    def detect(self, user_input: str) -> Intent:
        """
        Detect intent using Gemini API.
        
        Args:
            user_input: User's message
            
        Returns:
            Intent object with name, confidence, and entities
        """
        if not self.enabled:
            # Return unknown intent if API not configured
            return Intent(
                name="unknown",
                confidence=0.0,
                entities={},
                raw_input=user_input
            )
        
        try:
            # Prepare API request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": self._create_prompt(user_input)
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 256
                }
            }
            
            # Make request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            # Parse response
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Clean up response (remove markdown if present)
            text = text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1]
                text = text.rsplit('```', 1)[0]
            
            parsed = json.loads(text)
            
            return Intent(
                name=parsed.get('intent', 'unknown'),
                confidence=parsed.get('confidence', 0.8),
                entities=parsed.get('entities', {}),
                raw_input=user_input
            )
            
        except urllib.error.URLError as e:
            print(f"API Error: {e}")
            return Intent(name="unknown", confidence=0.0, entities={}, raw_input=user_input)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            return Intent(name="unknown", confidence=0.0, entities={}, raw_input=user_input)
        except Exception as e:
            print(f"Error: {e}")
            return Intent(name="unknown", confidence=0.0, entities={}, raw_input=user_input)


class HybridIntentDetector:
    """
    Hybrid detector that uses Gemini when available, falls back to rule-based.
    Best of both worlds: AI accuracy with offline reliability.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize both detectors."""
        self.gemini_detector = GeminiIntentDetector(config_path)
        
        # Import rule-based detector as fallback
        from .detector import IntentDetector as RuleBasedDetector
        self.rule_detector = RuleBasedDetector()
        
        self.use_ai = self.gemini_detector.enabled
    
    def detect(self, user_input: str) -> Intent:
        """
        Detect intent using AI if available, otherwise rule-based.
        
        Args:
            user_input: User's message
            
        Returns:
            Intent object
        """
        if self.use_ai:
            # Try AI first
            intent = self.gemini_detector.detect(user_input)
            
            # If AI returns unknown with low confidence, try rule-based
            if intent.name == "unknown" and intent.confidence < 0.3:
                return self.rule_detector.detect(user_input)
            
            return intent
        else:
            # Use rule-based
            return self.rule_detector.detect(user_input)
    
    def get_mode(self) -> str:
        """Get current detection mode."""
        return "AI (Gemini)" if self.use_ai else "Rule-based"


# Test function
def main():
    """Test the Gemini intent detector."""
    detector = HybridIntentDetector()
    
    print(f"Detection Mode: {detector.get_mode()}")
    print("=" * 50)
    
    test_inputs = [
        "Hi there!",
        "Show me vegetarian dishes under $15",
        "I want to book a table for 4 people tomorrow evening",
        "Cancel my booking #BK123",
        "What do you recommend?",
        "bye"
    ]
    
    for user_input in test_inputs:
        intent = detector.detect(user_input)
        print(f"\nInput: '{user_input}'")
        print(f"  Intent: {intent.name} ({intent.confidence:.0%})")
        if intent.entities:
            print(f"  Entities: {intent.entities}")


if __name__ == "__main__":
    main()
