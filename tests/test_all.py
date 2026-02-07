"""
End-to-End Tests for Dining Reservation Chatbot
Tests all major components and their integration.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compression.encoder import (
    DictionaryEncoder, RLEEncoder, BitEncoder, DataCompressor
)
from src.compression.decoder import (
    DictionaryDecoder, RLEDecoder, BitDecoder, DataDecompressor
)
from src.intent.detector import IntentDetector
from src.handlers.menu_handler import MenuHandler
from src.handlers.booking_handler import BookingHandler
from src.handlers.cancel_handler import CancelHandler
from src.handlers.recommend_handler import RecommendHandler
from src.chatbot import DiningChatbot


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name: str, passed: bool, message: str = ""):
        self.tests.append((name, passed, message))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self):
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        for name, passed, message in self.tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}")
            if message and not passed:
                print(f"        {message}")
        
        print("\n" + "-" * 60)
        print(f"Total: {self.passed + self.failed} | Passed: {self.passed} | Failed: {self.failed}")
        print("=" * 60)


def test_compression():
    """Test compression/decompression round-trip."""
    results = TestResults()
    
    # Test Dictionary Encoder
    encoder = DictionaryEncoder()
    values = ["Apple", "Banana", "Apple", "Cherry", "Banana", "Apple"]
    encoded, dictionary = encoder.encode_column(values)
    
    results.add(
        "Dictionary Encoding",
        len(set(encoded)) == 3 and len(dictionary) == 3,
        f"Expected 3 unique values, got {len(set(encoded))}"
    )
    
    # Test Dictionary Decoder
    decoder = DictionaryDecoder({v: k for k, v in dictionary.items()})
    decoded = decoder.decode_column(encoded)
    
    results.add(
        "Dictionary Decoding",
        decoded == values,
        f"Decoded values don't match original"
    )
    
    # Test RLE Encoder
    rle_values = [1, 1, 1, 2, 2, 3, 3, 3, 3]
    rle_encoded = RLEEncoder.encode(rle_values)
    
    results.add(
        "RLE Encoding",
        rle_encoded == [(1, 3), (2, 2), (3, 4)],
        f"Unexpected RLE result: {rle_encoded}"
    )
    
    # Test RLE Decoder
    rle_decoded = RLEDecoder.decode(rle_encoded)
    
    results.add(
        "RLE Decoding",
        rle_decoded == rle_values,
        f"RLE decoded doesn't match original"
    )
    
    # Test RLE Random Access
    value_at_5 = RLEDecoder.decode_at_index(rle_encoded, 5)
    
    results.add(
        "RLE Random Access",
        value_at_5 == 3,
        f"Expected 3 at index 5, got {value_at_5}"
    )
    
    # Test Bit Encoder
    bit_encoder = BitEncoder(["Veg", "Non-Veg", "Vegan"])
    bit_values = ["Veg", "Non-Veg", "Vegan", "Veg"]
    bit_encoded, categories = bit_encoder.encode_column(bit_values)
    
    results.add(
        "Bit Encoding",
        bit_encoded == [0, 1, 2, 0],
        f"Unexpected bit encoding: {bit_encoded}"
    )
    
    # Test Bit Decoder
    bit_decoder = BitDecoder(categories)
    bit_decoded = bit_decoder.decode_column(bit_encoded)
    
    results.add(
        "Bit Decoding",
        bit_decoded == bit_values,
        f"Bit decoded doesn't match original"
    )
    
    return results


def test_data_compression():
    """Test actual data file compression."""
    results = TestResults()
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # Test Compressor
    try:
        compressor = DataCompressor(str(data_dir))
        menu_data = compressor.compress_menu()
        tables_data = compressor.compress_tables()
        
        results.add(
            "Menu Compression",
            menu_data['metadata']['total_dishes'] > 0,
            "No dishes in compressed menu"
        )
        
        results.add(
            "Tables Compression",
            tables_data['metadata']['total_slots'] > 0,
            "No slots in compressed tables"
        )
    except Exception as e:
        results.add("Data Compression", False, str(e))
    
    # Test Decompressor
    try:
        decompressor = DataDecompressor(str(data_dir))
        
        # Test menu decompression
        menu_items = decompressor.get_all_menu_items()
        results.add(
            "Menu Decompression",
            len(menu_items) > 0 and 'name' in menu_items[0],
            "Menu decompression failed"
        )
        
        # Test filtering
        veg_items = decompressor.filter_menu(food_type="Veg")
        results.add(
            "Menu Filtering",
            all(item['type'] == 'Veg' for item in veg_items),
            "Filter returned non-Veg items"
        )
        
        # Test tables decompression
        table_slots = decompressor.get_all_table_slots()
        results.add(
            "Tables Decompression",
            len(table_slots) > 0 and 'table_id' in table_slots[0],
            "Table decompression failed"
        )
        
        # Test availability search
        available = decompressor.find_available_tables()
        results.add(
            "Availability Search",
            all(t['status'] == 'Available' for t in available),
            "Found non-available tables"
        )
        
    except Exception as e:
        results.add("Data Decompression", False, str(e))
    
    return results


def test_intent_detection():
    """Test intent detection accuracy."""
    results = TestResults()
    
    detector = IntentDetector()
    
    # Test cases: (input, expected_intent)
    test_cases = [
        ("hello", "greeting"),
        ("hi there", "greeting"),
        ("bye", "goodbye"),
        ("exit", "goodbye"),
        ("help me", "help"),
        ("show menu", "menu_query"),
        ("vegetarian dishes", "menu_query"),
        ("appetizers under $10", "menu_query"),
        ("book a table for 4", "book_table"),
        ("reserve a table", "book_table"),
        ("cancel booking #123", "cancel_booking"),
        ("cancel my reservation", "cancel_booking"),
        ("available tables", "check_availability"),
        ("what tables are free", "check_availability"),
        ("recommend something", "recommend"),
        ("suggest a dish", "recommend"),
    ]
    
    for user_input, expected in test_cases:
        intent = detector.detect(user_input)
        passed = intent.name == expected
        results.add(
            f"Intent: '{user_input}'",
            passed,
            f"Expected '{expected}', got '{intent.name}'"
        )
    
    # Test entity extraction
    intent = detector.detect("book a table for 4 tomorrow")
    results.add(
        "Entity: Party Size",
        intent.entities.get('party_size') == 4,
        f"Expected party_size=4, got {intent.entities}"
    )
    
    intent = detector.detect("vegetarian dishes under $15")
    results.add(
        "Entity: Food Type",
        intent.entities.get('food_type') == 'Veg',
        f"Expected food_type='Veg', got {intent.entities}"
    )
    
    results.add(
        "Entity: Max Price",
        intent.entities.get('max_price') == 15.0,
        f"Expected max_price=15.0, got {intent.entities}"
    )
    
    return results


def test_handlers():
    """Test all handlers."""
    results = TestResults()
    
    data_dir = str(Path(__file__).parent.parent / "data")
    
    # Menu Handler
    try:
        menu = MenuHandler(data_dir)
        
        full_menu = menu.get_full_menu()
        results.add(
            "Menu: Full Menu",
            len(full_menu) > 0,
            "Empty menu returned"
        )
        
        filtered = menu.filter_menu(category="Appetizers")
        results.add(
            "Menu: Category Filter",
            all(item['category'] == 'Appetizers' for item in filtered),
            "Filter returned wrong category"
        )
        
        categories = menu.get_categories()
        results.add(
            "Menu: Get Categories",
            'Appetizers' in categories and 'Desserts' in categories,
            f"Missing categories: {categories}"
        )
        
    except Exception as e:
        results.add("Menu Handler", False, str(e))
    
    # Booking Handler
    try:
        booking = BookingHandler(data_dir)
        
        available = booking.search_available_tables()
        results.add(
            "Booking: Search Available",
            len(available) > 0,
            "No available tables found"
        )
        
        time_slots = booking.get_time_slots()
        results.add(
            "Booking: Time Slots",
            len(time_slots) > 0,
            "No time slots returned"
        )
        
    except Exception as e:
        results.add("Booking Handler", False, str(e))
    
    # Recommendation Handler
    try:
        recommend = RecommendHandler(data_dir)
        
        popular = recommend.get_popular_dishes(limit=5)
        results.add(
            "Recommend: Popular Dishes",
            len(popular) == 5,
            f"Expected 5 dishes, got {len(popular)}"
        )
        
        special = recommend.get_chefs_special()
        results.add(
            "Recommend: Chef's Special",
            special is not None and 'name' in special,
            "No chef's special returned"
        )
        
        meal = recommend.get_complete_meal(food_type="Veg")
        results.add(
            "Recommend: Complete Meal",
            len(meal) > 0,
            "Empty meal returned"
        )
        
    except Exception as e:
        results.add("Recommend Handler", False, str(e))
    
    return results


def test_chatbot_integration():
    """Test full chatbot integration."""
    results = TestResults()
    
    try:
        chatbot = DiningChatbot()
        
        # Test greeting
        response = chatbot.get_response("hello")
        results.add(
            "Chatbot: Greeting",
            "hello" in response.lower() or "help" in response.lower(),
            f"Unexpected greeting response"
        )
        
        # Test menu
        response = chatbot.get_response("show menu")
        results.add(
            "Chatbot: Menu Query",
            "menu" in response.lower() or "$" in response,
            f"Unexpected menu response"
        )
        
        # Test recommendations
        response = chatbot.get_response("recommend something")
        results.add(
            "Chatbot: Recommendation",
            "recommend" in response.lower() or "popular" in response.lower() or "$" in response,
            f"Unexpected recommendation response"
        )
        
        # Test availability
        response = chatbot.get_response("available tables")
        results.add(
            "Chatbot: Availability",
            "table" in response.lower() or "available" in response.lower(),
            f"Unexpected availability response"
        )
        
        # Test help
        response = chatbot.get_response("help")
        results.add(
            "Chatbot: Help",
            "menu" in response.lower() and "book" in response.lower(),
            f"Unexpected help response"
        )
        
        # Test unknown
        response = chatbot.get_response("asdfghjkl")
        results.add(
            "Chatbot: Unknown Intent",
            "understand" in response.lower() or "help" in response.lower(),
            f"Unexpected unknown response"
        )
        
    except Exception as e:
        results.add("Chatbot Integration", False, str(e))
    
    return results


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("DINING RESERVATION CHATBOT - TEST SUITE")
    print("=" * 60)
    
    all_results = TestResults()
    
    print("\n📦 Testing Compression/Decompression...")
    compression_results = test_compression()
    for t in compression_results.tests:
        all_results.add(t[0], t[1], t[2])
    
    print("\n📁 Testing Data File Compression...")
    data_results = test_data_compression()
    for t in data_results.tests:
        all_results.add(t[0], t[1], t[2])
    
    print("\n🎯 Testing Intent Detection...")
    intent_results = test_intent_detection()
    for t in intent_results.tests:
        all_results.add(t[0], t[1], t[2])
    
    print("\n🔧 Testing Handlers...")
    handler_results = test_handlers()
    for t in handler_results.tests:
        all_results.add(t[0], t[1], t[2])
    
    print("\n🤖 Testing Chatbot Integration...")
    chatbot_results = test_chatbot_integration()
    for t in chatbot_results.tests:
        all_results.add(t[0], t[1], t[2])
    
    # Print final summary
    all_results.summary()
    
    return all_results.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
