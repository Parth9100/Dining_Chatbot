"""
Dining Reservation Chatbot - Main Loop (AI Enhanced)
Terminal-based conversational interface with Gemini AI and notifications.

Features:
- AI-powered intent detection (Gemini API)
- Rule-based fallback for offline use
- SMS notifications (Twilio)
- Email confirmations
- Menu browsing with filters
- Table booking and cancellation
- Dish recommendations
"""

from typing import Optional
from pathlib import Path

# Try to import AI detector, fall back to rule-based
try:
    from .intent.gemini_detector import HybridIntentDetector, Intent
    AI_AVAILABLE = True
except ImportError:
    from .intent.detector import IntentDetector as HybridIntentDetector, Intent
    AI_AVAILABLE = False

from .handlers.menu_handler import MenuHandler
from .handlers.booking_handler import BookingHandler
from .handlers.cancel_handler import CancelHandler
from .handlers.recommend_handler import RecommendHandler
from .compression.encoder import DataCompressor

# Try to import notifications
try:
    from .notifications import NotificationService
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False


class DiningChatbot:
    """
    Main chatbot class with AI-powered understanding and notifications.
    
    Architecture:
    1. User input -> AI Intent Detection (Gemini)
    2. Intent + Entities -> Appropriate Handler
    3. Handler Response -> User Output
    4. Booking events -> SMS/Email Notifications
    """
    
    def __init__(self, data_dir: str = None, config_path: str = None):
        """
        Initialize the chatbot with all components.
        
        Args:
            data_dir: Optional path to data directory
            config_path: Optional path to config.json
        """
        # Determine directories
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data"
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent.parent / "config.json"
        
        # Ensure data is compressed on first run
        self._ensure_compressed_data()
        
        # Initialize AI intent detector
        self.intent_detector = HybridIntentDetector(str(self.config_path))
        
        # Initialize handlers
        self.menu_handler = MenuHandler(str(self.data_dir))
        self.booking_handler = BookingHandler(str(self.data_dir))
        self.cancel_handler = CancelHandler(self.booking_handler, str(self.data_dir))
        self.recommend_handler = RecommendHandler(str(self.data_dir))
        
        # Initialize notification service
        if NOTIFICATIONS_AVAILABLE:
            self.notifications = NotificationService(str(self.config_path))
        else:
            self.notifications = None
        
        # Conversation state
        self.conversation_active = True
        self.last_intent: Optional[Intent] = None
        
        # User contact info (for notifications)
        self.user_phone: Optional[str] = None
        self.user_email: Optional[str] = None
    
    def _ensure_compressed_data(self):
        """Ensure compressed data files exist."""
        compressed_menu = self.data_dir / "compressed" / "menu_compressed.json"
        compressed_tables = self.data_dir / "compressed" / "tables_compressed.json"
        
        needs_compression = False
        
        if not compressed_menu.exists():
            needs_compression = True
        elif compressed_menu.exists():
            content = compressed_menu.read_text()
            if '"_comment"' in content:
                needs_compression = True
        
        if not compressed_tables.exists():
            needs_compression = True
        elif compressed_tables.exists():
            content = compressed_tables.read_text()
            if '"_comment"' in content:
                needs_compression = True
        
        if needs_compression:
            print("Initializing data compression...")
            compressor = DataCompressor(str(self.data_dir))
            compressor.compress_all()
            print()
    
    def get_greeting(self) -> str:
        """Get initial greeting message with AI status."""
        mode = self.intent_detector.get_mode() if hasattr(self.intent_detector, 'get_mode') else "Rule-based"
        
        # Notification status
        notif_status = ""
        if self.notifications:
            status = self.notifications.get_status()
            if status['sms_enabled'] or status['email_enabled']:
                notif_status = "\n  • 📱 Notifications enabled"
        
        return f"""
🍽️  Welcome to the Dining Reservation Chatbot!
🤖 Mode: {mode}{notif_status}

I can help you with:
  • 📋 Browse our menu (try: "show menu", "vegetarian dishes")
  • 🪑 Book a table (try: "book a table for 4")
  • ❌ Cancel reservations (try: "cancel booking #ID")
  • 💡 Get recommendations (try: "recommend something")
  • ℹ️  Check availability (try: "available tables")

Type 'help' for more commands, or 'bye' to exit.
────────────────────────────────────────────────────
"""
    
    def get_help_message(self) -> str:
        """Get help message with examples."""
        return """
📖 HOW TO USE THIS CHATBOT
════════════════════════════════════════

🍽️  MENU COMMANDS:
   • "show menu" - View full menu
   • "vegetarian dishes" - Filter by type
   • "appetizers under $10" - Filter by category and price
   • "what desserts do you have?" - Browse category

🪑 BOOKING COMMANDS:
   • "book a table for 4" - Start booking
   • "reserve table tomorrow at 7pm" - Specific booking
   • "available tables tonight" - Check availability

❌ CANCELLATION:
   • "cancel booking #BKXXXX" - Cancel by ID
   • "cancel my reservation" - See your bookings

💡 RECOMMENDATIONS:
   • "recommend something" - Get suggestions
   • "suggest a vegan dish" - Type-specific
   • "what's popular?" - Top dishes
   • "chef's special" - Special recommendation

📱 NOTIFICATIONS:
   • "set phone +1234567890" - Set phone for SMS
   • "set email user@example.com" - Set email for confirmations

ℹ️  OTHER:
   • "help" - Show this message
   • "bye" or "exit" - Close chatbot

════════════════════════════════════════
"""
    
    def _send_booking_notifications(self, booking: dict):
        """Send booking confirmation notifications."""
        if not self.notifications:
            return
        
        results = self.notifications.send_booking_notification(
            booking,
            phone=self.user_phone,
            email=self.user_email
        )
        
        if results:
            for channel, (success, message) in results.items():
                if success:
                    print(f"   📤 {channel.upper()}: Confirmation sent!")
    
    def _send_cancellation_notifications(self, booking: dict):
        """Send cancellation notifications."""
        if not self.notifications:
            return
        
        results = self.notifications.send_cancellation_notification(
            booking,
            phone=self.user_phone,
            email=self.user_email
        )
        
        if results:
            for channel, (success, message) in results.items():
                if success:
                    print(f"   📤 {channel.upper()}: Cancellation notice sent!")
    
    def _handle_contact_update(self, user_input: str) -> Optional[str]:
        """Handle phone/email updates."""
        import re
        
        # Check for phone number setting
        phone_match = re.search(r'set\s+phone\s+(\+?[\d\-\s]+)', user_input, re.IGNORECASE)
        if phone_match:
            self.user_phone = re.sub(r'[\s\-]', '', phone_match.group(1))
            return f"📱 Phone number set to: {self.user_phone}"
        
        # Check for email setting
        email_match = re.search(r'set\s+email\s+([\w\.\-]+@[\w\.\-]+)', user_input, re.IGNORECASE)
        if email_match:
            self.user_email = email_match.group(1)
            return f"📧 Email set to: {self.user_email}"
        
        return None
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and return appropriate response.
        
        Args:
            user_input: Raw user input string
            
        Returns:
            Response string to display
        """
        # Check for contact updates first
        contact_response = self._handle_contact_update(user_input)
        if contact_response:
            return contact_response
        
        # Detect intent (uses AI if available)
        intent = self.intent_detector.detect(user_input)
        self.last_intent = intent
        
        # Route to appropriate handler
        if intent.name == 'greeting':
            return "👋 Hello! How can I help you today? Try 'show menu' or 'book a table'."
        
        elif intent.name == 'goodbye':
            self.conversation_active = False
            return "👋 Thank you for visiting! Goodbye and see you soon!"
        
        elif intent.name == 'help':
            return self.get_help_message()
        
        elif intent.name == 'menu_query':
            return self.menu_handler.process_query(intent.entities)
        
        elif intent.name == 'book_table':
            response = self.booking_handler.process_booking_request(intent.entities)
            
            # Send notifications if booking was confirmed
            if "Confirmed" in response and self.booking_handler.bookings:
                # Get the latest booking
                latest_id = list(self.booking_handler.bookings.keys())[-1]
                booking = self.booking_handler.bookings[latest_id]
                self._send_booking_notifications(booking)
            
            return response
        
        elif intent.name == 'check_availability':
            tables = self.booking_handler.search_available_tables(
                date_str=intent.entities.get('date'),
                time_slot=intent.entities.get('time'),
                party_size=intent.entities.get('party_size')
            )
            return self.booking_handler.format_available_tables(
                tables, 
                intent.entities.get('party_size')
            )
        
        elif intent.name == 'cancel_booking':
            response = self.cancel_handler.process_cancellation(intent.entities)
            
            # Send cancellation notification
            if "Cancelled Successfully" in response:
                booking_id = intent.entities.get('booking_id', '')
                if booking_id:
                    booking = self.booking_handler.get_booking(booking_id)
                    if booking:
                        self._send_cancellation_notifications(booking)
            
            return response
        
        elif intent.name == 'recommend':
            return self.recommend_handler.process_recommendation(intent.entities)
        
        else:
            # Unknown intent
            return (
                "I'm not sure I understand. Could you rephrase that?\n\n"
                "Try commands like:\n"
                "  • 'show menu'\n"
                "  • 'book a table for 2'\n"
                "  • 'recommend something'\n"
                "  • 'help' for more options"
            )
    
    def run(self):
        """
        Main conversation loop.
        Runs until user says goodbye or types exit.
        """
        # Show greeting
        print(self.get_greeting())
        
        # Main loop
        while self.conversation_active:
            try:
                # Get user input
                user_input = input("\n🧑 You: ").strip()
                
                if not user_input:
                    continue
                
                # Process and respond
                response = self.process_input(user_input)
                
                # Display response
                print(f"\n🤖 Bot: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Please try again or type 'help' for assistance.")
    
    def get_response(self, user_input: str) -> str:
        """
        Get response without running the full loop.
        Useful for testing or integration.
        
        Args:
            user_input: User message
            
        Returns:
            Bot response
        """
        return self.process_input(user_input)


# Allow running as module
def main():
    """Entry point for running chatbot."""
    chatbot = DiningChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
