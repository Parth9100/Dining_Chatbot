"""
Intent Detection Module - Rule-Based Pattern Matching

Implements a rule-based system for detecting user intents without ML/DL.
Uses keyword matching, regex patterns, and entity extraction.

Supported Intents:
- menu_query: User wants to see menu/dishes
- book_table: User wants to make a reservation
- cancel_booking: User wants to cancel a reservation
- check_availability: User wants to check table availability
- recommend: User wants dish recommendations
- greeting: User says hello/hi
- goodbye: User says bye/exit
- help: User needs assistance
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class Intent:
    """Represents a detected intent with confidence and entities."""
    name: str
    confidence: float
    entities: Dict[str, Any]
    raw_input: str


class IntentDetector:
    """
    Rule-based intent detection using keyword matching and regex patterns.
    
    Matching Process:
    1. Preprocess input (lowercase, normalize)
    2. Check for exact phrase matches (highest confidence)
    3. Check for keyword matches (medium confidence)
    4. Extract entities (dates, numbers, categories)
    5. Return best matching intent
    """
    
    def __init__(self):
        """Initialize intent patterns and entity extractors."""
        
        # Intent patterns: {intent_name: (phrases, keywords, patterns)}
        # Phrases give higher confidence than keywords
        self.intent_patterns = {
            'greeting': {
                'phrases': ['hello', 'hi there', 'good morning', 'good evening', 
                           'good afternoon', 'hey', 'hi'],
                'keywords': ['hello', 'hi', 'hey', 'greetings'],
                'patterns': [r'^hi\b', r'^hey\b', r'^hello\b']
            },
            'goodbye': {
                'phrases': ['bye', 'goodbye', 'see you', 'exit', 'quit', 'close'],
                'keywords': ['bye', 'goodbye', 'exit', 'quit', 'leave', 'done'],
                'patterns': [r'\b(bye|exit|quit)\b']
            },
            'help': {
                'phrases': ['help me', 'what can you do', 'how to use', 'commands'],
                'keywords': ['help', 'assist', 'support', 'guide', 'how'],
                'patterns': [r'\bhelp\b', r'what.*(can|do)']
            },
            'menu_query': {
                'phrases': ['show menu', 'see menu', 'view menu', 'what dishes',
                           'show me the menu', 'menu please', 'food menu',
                           'what do you have', 'what is available'],
                'keywords': ['menu', 'dishes', 'food', 'appetizers', 'desserts',
                            'beverages', 'main course', 'entrees', 'starters'],
                'patterns': [
                    r'show.*menu',
                    r'(list|view|see).*dishes',
                    r'what.*(dishes|food|serve)',
                    r'(vegetarian|vegan|non.?veg)',
                    r'under\s*\$?\d+',
                    r'less than\s*\$?\d+'
                ]
            },
            'book_table': {
                'phrases': ['book a table', 'reserve a table', 'make a reservation',
                           'i want to book', 'table for', 'need a table',
                           'book table', 'reserve table', 'reservation please'],
                'keywords': ['book', 'reserve', 'reservation', 'table'],
                'patterns': [
                    r'book.*table',
                    r'reserve.*table',
                    r'table\s+for\s+\d+',
                    r'reservation\s+for\s+\d+',
                    r'party\s+of\s+\d+'
                ]
            },
            'cancel_booking': {
                'phrases': ['cancel booking', 'cancel reservation', 'cancel my table',
                           'remove booking', 'delete reservation', 'cancel'],
                'keywords': ['cancel', 'remove', 'delete', 'undo'],
                'patterns': [
                    r'cancel.*(booking|reservation|table)',
                    r'(remove|delete).*(booking|reservation)'
                ]
            },
            'check_availability': {
                'phrases': ['check availability', 'is table available', 'available tables',
                           'free tables', 'any tables', 'what tables are free',
                           'show available', 'tables available'],
                'keywords': ['available', 'availability', 'free', 'open'],
                'patterns': [
                    r'(check|show|any).*availab',
                    r'(table|tables).*(available|free)',
                    r'what.*available',
                    r'is.*free'
                ]
            },
            'recommend': {
                'phrases': ['recommend something', 'suggest a dish', 'what should i order',
                           'best dishes', 'popular items', 'chef special',
                           'recommendation please', 'any suggestions'],
                'keywords': ['recommend', 'suggest', 'suggestion', 'popular', 
                            'best', 'favorite', 'special', 'try'],
                'patterns': [
                    r'(recommend|suggest)',
                    r'what.*should.*order',
                    r'(best|popular|top).*dish',
                    r'what.*(good|try)'
                ]
            }
        }
        
        # Entity patterns for extraction
        self.entity_patterns = {
            'date': [
                (r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'date'),
                (r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})', 'date'),
                (r'(today|tomorrow|tonight)', 'relative_date'),
                (r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', 'weekday'),
                (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}', 'month_date')
            ],
            'time': [
                (r'(\d{1,2}:\d{2}\s*(am|pm)?)', 'time'),
                (r'(\d{1,2}\s*(am|pm))', 'time'),
                (r'(noon|midnight|evening|morning|afternoon|night)', 'relative_time'),
                (r'(lunch|dinner|breakfast)', 'meal_time')
            ],
            'party_size': [
                (r'for\s+(\d+)\s*(people|persons|guests)?', 'party_size'),
                (r'party\s+of\s+(\d+)', 'party_size'),
                (r'table\s+for\s+(\d+)', 'party_size'),
                (r'(\d+)\s+guests', 'party_size'),
                (r'(\d+)\s+people', 'party_size')
            ],
            'price': [
                (r'under\s*\$?(\d+(?:\.\d{2})?)', 'max_price'),
                (r'less\s+than\s*\$?(\d+(?:\.\d{2})?)', 'max_price'),
                (r'below\s*\$?(\d+(?:\.\d{2})?)', 'max_price'),
                (r'above\s*\$?(\d+(?:\.\d{2})?)', 'min_price'),
                (r'over\s*\$?(\d+(?:\.\d{2})?)', 'min_price'),
                (r'\$(\d+(?:\.\d{2})?)\s*-\s*\$?(\d+(?:\.\d{2})?)', 'price_range')
            ],
            'category': [
                (r'\b(appetizer|appetizers|starter|starters)\b', 'Appetizers'),
                (r'\b(main|main course|entree|entrees)\b', 'Main Course'),
                (r'\b(dessert|desserts|sweet|sweets)\b', 'Desserts'),
                (r'\b(drink|drinks|beverage|beverages)\b', 'Beverages')
            ],
            'food_type': [
                (r'\b(veg|vegetarian)\b', 'Veg'),
                (r'\b(non.?veg|non.?vegetarian|meat)\b', 'Non-Veg'),
                (r'\b(vegan|plant.?based)\b', 'Vegan')
            ],
            'booking_id': [
                (r'booking\s*#?\s*(\w+)', 'booking_id'),
                (r'reservation\s*#?\s*(\w+)', 'booking_id'),
                (r'#(\w+)', 'booking_id')
            ]
        }
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess input text for matching.
        
        Args:
            text: Raw user input
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation except for special characters we need
        text = re.sub(r'[^\w\s\-\$\#\:\.]', '', text)
        
        return text
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from user input.
        
        Args:
            text: Preprocessed user input
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern, label in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if entity_type == 'category' or entity_type == 'food_type':
                        entities[entity_type] = label
                    elif entity_type == 'price' and label == 'price_range':
                        entities['min_price'] = float(match.group(1))
                        entities['max_price'] = float(match.group(2))
                    elif 'price' in label:
                        entities[label] = float(match.group(1))
                    elif entity_type == 'party_size':
                        entities['party_size'] = int(match.group(1))
                    else:
                        entities[entity_type] = match.group(1) if match.groups() else match.group(0)
        
        # Special handling for relative dates
        if entities.get('date') == 'today':
            from datetime import date
            entities['date'] = date.today().strftime('%Y-%m-%d')
        elif entities.get('date') == 'tomorrow':
            from datetime import date, timedelta
            entities['date'] = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        return entities
    
    def calculate_confidence(self, text: str, intent_name: str) -> float:
        """
        Calculate confidence score for an intent match.
        
        Scoring:
        - Exact phrase match: 0.9-1.0
        - Regex pattern match: 0.7-0.9
        - Keyword match: 0.5-0.7
        - Partial match: 0.3-0.5
        
        Args:
            text: Preprocessed user input
            intent_name: Name of intent to score
            
        Returns:
            Confidence score (0.0-1.0)
        """
        patterns = self.intent_patterns.get(intent_name, {})
        confidence = 0.0
        
        # Check phrase matches (highest confidence)
        phrases = patterns.get('phrases', [])
        for phrase in phrases:
            if phrase in text:
                # Exact phrase in text
                confidence = max(confidence, 0.95)
            elif phrase.replace(' ', '') in text.replace(' ', ''):
                # Phrase without spaces
                confidence = max(confidence, 0.85)
        
        # Check regex patterns (high confidence)
        regex_patterns = patterns.get('patterns', [])
        for pattern in regex_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                confidence = max(confidence, 0.8)
        
        # Check keyword matches (medium confidence)
        keywords = patterns.get('keywords', [])
        keyword_matches = sum(1 for kw in keywords if kw in text)
        if keyword_matches > 0:
            keyword_score = min(0.5 + (keyword_matches * 0.1), 0.7)
            confidence = max(confidence, keyword_score)
        
        return confidence
    
    def detect(self, user_input: str) -> Intent:
        """
        Detect the intent from user input.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Intent object with name, confidence, and entities
        """
        # Preprocess
        processed = self.preprocess(user_input)
        
        # Calculate confidence for each intent
        scores = {}
        for intent_name in self.intent_patterns:
            scores[intent_name] = self.calculate_confidence(processed, intent_name)
        
        # Get best intent
        best_intent = max(scores, key=scores.get)
        best_confidence = scores[best_intent]
        
        # Fallback to unknown if confidence too low
        if best_confidence < 0.3:
            best_intent = 'unknown'
            best_confidence = 0.0
        
        # Extract entities
        entities = self.extract_entities(processed)
        
        return Intent(
            name=best_intent,
            confidence=best_confidence,
            entities=entities,
            raw_input=user_input
        )
    
    def get_all_intents(self, user_input: str) -> List[Tuple[str, float]]:
        """
        Get all intents with their confidence scores (for debugging).
        
        Args:
            user_input: Raw user input
            
        Returns:
            List of (intent_name, confidence) tuples, sorted by confidence
        """
        processed = self.preprocess(user_input)
        scores = []
        
        for intent_name in self.intent_patterns:
            confidence = self.calculate_confidence(processed, intent_name)
            if confidence > 0:
                scores.append((intent_name, confidence))
        
        return sorted(scores, key=lambda x: x[1], reverse=True)


# Test function
def main():
    """Test the intent detector."""
    detector = IntentDetector()
    
    test_inputs = [
        "Hello there!",
        "Show me the menu",
        "I want vegetarian dishes under $15",
        "Book a table for 4 tomorrow at 7pm",
        "Cancel my reservation #12345",
        "Are there any tables available tonight?",
        "Recommend me something good",
        "What desserts do you have?",
        "bye",
        "asdfgh"  # Unknown
    ]
    
    print("=" * 60)
    print("Intent Detection Test")
    print("=" * 60)
    
    for input_text in test_inputs:
        intent = detector.detect(input_text)
        print(f"\nInput: '{input_text}'")
        print(f"  Intent: {intent.name} (confidence: {intent.confidence:.2f})")
        if intent.entities:
            print(f"  Entities: {intent.entities}")


if __name__ == "__main__":
    main()
