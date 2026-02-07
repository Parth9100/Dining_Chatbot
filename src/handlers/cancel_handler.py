"""
Cancellation Handler
Handles booking cancellations and restores table availability.
"""

from typing import Dict, Any, Optional, Tuple
from .booking_handler import BookingHandler


class CancelHandler:
    """
    Handles booking cancellations.
    
    Capabilities:
    - Cancel booking by ID
    - Restore table availability
    - Show cancellation confirmation
    """
    
    def __init__(self, booking_handler: BookingHandler = None, data_dir: str = None):
        """
        Initialize with booking handler.
        
        Args:
            booking_handler: Existing BookingHandler instance
            data_dir: Data directory path
        """
        if booking_handler:
            self.booking_handler = booking_handler
        else:
            self.booking_handler = BookingHandler(data_dir)
    
    def cancel_booking(self, booking_id: str) -> Tuple[bool, str]:
        """
        Cancel a booking and restore table availability.
        
        Args:
            booking_id: Booking ID to cancel
            
        Returns:
            Tuple of (success, message)
        """
        # Normalize booking ID
        booking_id = booking_id.upper().strip()
        
        # Remove common prefixes if user typed them
        if booking_id.startswith('#'):
            booking_id = booking_id[1:]
        
        # Get the booking
        booking = self.booking_handler.get_booking(booking_id)
        
        if not booking:
            return False, f"❌ Booking ID '{booking_id}' not found."
        
        if booking['status'] == 'Cancelled':
            return False, f"❌ Booking {booking_id} has already been cancelled."
        
        # Restore table availability
        success = self.booking_handler.decompressor.update_table_status(
            table_id=booking['table_id'],
            date=booking['date'],
            time_slot=booking['time_slot'],
            new_status='Available'
        )
        
        if not success:
            return False, "❌ Failed to restore table availability. Please try again."
        
        # Update booking status
        booking['status'] = 'Cancelled'
        self.booking_handler._save_bookings()
        
        message = (
            f"✅ Booking Cancelled Successfully!\n\n"
            f"   Booking ID: {booking_id}\n"
            f"   Table: {booking['table_id']}\n"
            f"   Date: {booking['date']}\n"
            f"   Time: {booking['time_slot']}\n\n"
            f"The table is now available for other guests."
        )
        
        return True, message
    
    def get_booking_for_cancellation(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """
        Get booking details for confirmation before cancelling.
        
        Args:
            booking_id: Booking ID to look up
            
        Returns:
            Booking details or None
        """
        return self.booking_handler.get_booking(booking_id)
    
    def format_booking_details(self, booking: Dict[str, Any]) -> str:
        """Format booking details for confirmation."""
        return (
            f"📋 Booking Details:\n"
            f"   ID: {booking['booking_id']}\n"
            f"   Table: {booking['table_id']}\n"
            f"   Date: {booking['date']}\n"
            f"   Time: {booking['time_slot']}\n"
            f"   Party Size: {booking['party_size']}\n"
            f"   Name: {booking['customer_name']}\n"
            f"   Status: {booking['status']}"
        )
    
    def process_cancellation(self, entities: Dict[str, Any]) -> str:
        """
        Process a cancellation request from intent entities.
        
        Args:
            entities: Extracted entities from intent detection
            
        Returns:
            Response string
        """
        booking_id = entities.get('booking_id')
        
        if not booking_id:
            # List recent bookings to help user find the ID
            bookings = self.booking_handler.list_bookings()
            
            if not bookings:
                return "You don't have any active bookings to cancel."
            
            lines = ["Please provide your booking ID to cancel.\n"]
            lines.append("Your current bookings:")
            for booking in bookings[:5]:  # Show max 5
                lines.append(
                    f"   • {booking['booking_id']} - "
                    f"{booking['date']} at {booking['time_slot']} "
                    f"(Table {booking['table_id']})"
                )
            lines.append("\nSay 'cancel #BOOKING_ID' to cancel a specific booking.")
            return "\n".join(lines)
        
        # Perform cancellation
        success, message = self.cancel_booking(booking_id)
        return message
