"""
Booking Handler
Handles table reservations: search, reserve, and confirm bookings.
Uses compressed data for efficient availability checks.
"""

import json
import random
import string
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from ..compression.decoder import DataDecompressor


class BookingHandler:
    """
    Handles all table booking operations.
    
    Capabilities:
    - Search available tables by date, time, and capacity
    - Create new reservations
    - Confirm pending bookings
    - Get booking details
    - List user's bookings
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize with data directory path."""
        self.decompressor = DataDecompressor(data_dir)
        
        # Bookings storage (in-memory with file persistence)
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        self.bookings_file = self.data_dir / "bookings.json"
        self.bookings = self._load_bookings()
    
    def _load_bookings(self) -> Dict[str, Dict]:
        """Load bookings from file."""
        if self.bookings_file.exists():
            with open(self.bookings_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_bookings(self):
        """Save bookings to file."""
        with open(self.bookings_file, 'w') as f:
            json.dump(self.bookings, f, indent=2)
    
    def _generate_booking_id(self) -> str:
        """Generate a unique booking ID."""
        chars = string.ascii_uppercase + string.digits
        while True:
            booking_id = 'BK' + ''.join(random.choices(chars, k=6))
            if booking_id not in self.bookings:
                return booking_id
    
    def search_available_tables(self,
                                date_str: str = None,
                                time_slot: str = None,
                                party_size: int = None) -> List[Dict[str, Any]]:
        """
        Search for available tables.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            time_slot: Time slot (e.g., '19:00-20:00')
            party_size: Number of guests
            
        Returns:
            List of available table slots
        """
        # Use today's date if not specified
        if not date_str:
            date_str = date.today().strftime('%Y-%m-%d')
        
        return self.decompressor.find_available_tables(
            date=date_str,
            time_slot=time_slot,
            min_capacity=party_size
        )
    
    def get_time_slots(self) -> List[str]:
        """Get list of available time slots."""
        return [
            "12:00-13:00",
            "13:00-14:00",
            "18:00-19:00",
            "19:00-20:00",
            "20:00-21:00"
        ]
    
    def make_reservation(self,
                        table_id: str,
                        date_str: str,
                        time_slot: str,
                        party_size: int,
                        customer_name: str = "Guest") -> Tuple[bool, str, Optional[str]]:
        """
        Make a table reservation.
        
        Args:
            table_id: ID of the table to reserve
            date_str: Date in YYYY-MM-DD format
            time_slot: Time slot
            party_size: Number of guests
            customer_name: Name for the reservation
            
        Returns:
            Tuple of (success, message, booking_id)
        """
        # Check if table is available
        available = self.search_available_tables(
            date_str=date_str,
            time_slot=time_slot
        )
        
        matching = [t for t in available if t['table_id'] == table_id]
        
        if not matching:
            return False, f"Sorry, table {table_id} is not available at that time.", None
        
        table = matching[0]
        
        if table['capacity'] < party_size:
            return False, f"Table {table_id} only seats {table['capacity']} people.", None
        
        # Create booking
        booking_id = self._generate_booking_id()
        
        booking = {
            'booking_id': booking_id,
            'table_id': table_id,
            'date': date_str,
            'time_slot': time_slot,
            'party_size': party_size,
            'customer_name': customer_name,
            'status': 'Confirmed',
            'created_at': datetime.now().isoformat()
        }
        
        # Update table status
        success = self.decompressor.update_table_status(
            table_id=table_id,
            date=date_str,
            time_slot=time_slot,
            new_status='Reserved'
        )
        
        if not success:
            return False, "Failed to update table status.", None
        
        # Save booking
        self.bookings[booking_id] = booking
        self._save_bookings()
        
        message = (
            f"✅ Reservation Confirmed!\n"
            f"   Booking ID: {booking_id}\n"
            f"   Table: {table_id} (seats {table['capacity']})\n"
            f"   Date: {date_str}\n"
            f"   Time: {time_slot}\n"
            f"   Party Size: {party_size}\n"
            f"   Name: {customer_name}"
        )
        
        return True, message, booking_id
    
    def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Get booking details by ID."""
        return self.bookings.get(booking_id.upper())
    
    def list_bookings(self, date_str: str = None) -> List[Dict[str, Any]]:
        """
        List all bookings, optionally filtered by date.
        
        Args:
            date_str: Optional date filter
            
        Returns:
            List of bookings
        """
        bookings = list(self.bookings.values())
        
        if date_str:
            bookings = [b for b in bookings if b['date'] == date_str]
        
        # Filter to only active bookings
        bookings = [b for b in bookings if b['status'] == 'Confirmed']
        
        return sorted(bookings, key=lambda x: (x['date'], x['time_slot']))
    
    def format_available_tables(self, tables: List[Dict], 
                                party_size: int = None) -> str:
        """Format available tables for display."""
        if not tables:
            return "No tables available matching your criteria."
        
        lines = ["🪑 Available Tables:\n"]
        
        # Group by capacity
        by_capacity = {}
        for table in tables:
            cap = table['capacity']
            if cap not in by_capacity:
                by_capacity[cap] = []
            by_capacity[cap].append(table)
        
        for capacity in sorted(by_capacity.keys()):
            if party_size and capacity < party_size:
                continue
            
            lines.append(f"\n📍 {capacity}-Seater Tables:")
            for table in by_capacity[capacity]:
                lines.append(
                    f"   • {table['table_id']} - {table['date']} at {table['time_slot']}"
                )
        
        return "\n".join(lines)
    
    def process_booking_request(self, entities: Dict[str, Any]) -> str:
        """
        Process a booking request from intent entities.
        
        Args:
            entities: Extracted entities from intent detection
            
        Returns:
            Response string
        """
        date_str = entities.get('date')
        time_slot = entities.get('time')
        party_size = entities.get('party_size')
        
        # If we don't have all required info, show available tables
        if not date_str:
            date_str = date.today().strftime('%Y-%m-%d')
        
        available = self.search_available_tables(
            date_str=date_str,
            time_slot=time_slot,
            party_size=party_size
        )
        
        if not available:
            return (
                "Sorry, no tables are available for your requirements.\n"
                "Try a different date, time, or party size."
            )
        
        # If we have complete info, try to book the best matching table
        if party_size:
            # Find smallest table that fits the party
            suitable = [t for t in available if t['capacity'] >= party_size]
            suitable = sorted(suitable, key=lambda x: x['capacity'])
            
            if suitable:
                best_table = suitable[0]
                
                # If we have time slot, make the reservation
                if time_slot:
                    success, message, _ = self.make_reservation(
                        table_id=best_table['table_id'],
                        date_str=date_str,
                        time_slot=time_slot,
                        party_size=party_size
                    )
                    return message
                
                # Show available time slots for this table
                table_slots = [t for t in available if t['table_id'] == best_table['table_id']]
                lines = [f"Table {best_table['table_id']} (seats {best_table['capacity']}) is available at:"]
                for slot in table_slots:
                    lines.append(f"   • {slot['time_slot']}")
                lines.append("\nPlease specify your preferred time to complete the booking.")
                return "\n".join(lines)
        
        # Show all available tables
        return self.format_available_tables(available, party_size)
