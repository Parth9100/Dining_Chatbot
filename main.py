"""
Dining Reservation Chatbot - Main Entry Point
Run this file to start the chatbot.
"""

from src.chatbot import DiningChatbot


def main():
    """Initialize and run the dining reservation chatbot."""
    print("=" * 50)
    print("  Welcome to the Dining Reservation Chatbot!")
    print("=" * 50)
    print()
    
    chatbot = DiningChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
