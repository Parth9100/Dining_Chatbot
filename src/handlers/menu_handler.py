"""
Menu Query Handler
Processes menu-related queries with filtering by category, type, and price.
Uses compressed data for efficient lookups.
"""

from typing import Dict, List, Any, Optional
from ..compression.decoder import DataDecompressor


class MenuHandler:
    """
    Handles all menu-related queries.
    
    Capabilities:
    - Show full menu
    - Filter by category (Appetizers, Main Course, Desserts, Beverages)
    - Filter by type (Veg, Non-Veg, Vegan)
    - Filter by price range
    - Get specific dish details
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize with data directory path."""
        self.decompressor = DataDecompressor(data_dir)
    
    def get_full_menu(self) -> Dict[str, List[Dict]]:
        """
        Get the complete menu organized by category.
        
        Returns:
            Dictionary with categories as keys and dish lists as values
        """
        items = self.decompressor.get_all_menu_items()
        
        # Organize by category
        menu_by_category = {}
        for item in items:
            category = item['category']
            if category not in menu_by_category:
                menu_by_category[category] = []
            menu_by_category[category].append(item)
        
        return menu_by_category
    
    def filter_menu(self, 
                   category: str = None,
                   food_type: str = None,
                   max_price: float = None,
                   min_price: float = None) -> List[Dict[str, Any]]:
        """
        Filter menu items based on criteria.
        
        Args:
            category: Filter by category name
            food_type: Filter by Veg/Non-Veg/Vegan
            max_price: Maximum price
            min_price: Minimum price
            
        Returns:
            List of matching menu items
        """
        return self.decompressor.filter_menu(
            category=category,
            food_type=food_type,
            max_price=max_price,
            min_price=min_price
        )
    
    def get_dish_by_id(self, dish_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific dish by its ID.
        
        Args:
            dish_id: Dish ID (e.g., 'D001')
            
        Returns:
            Dish details or None if not found
        """
        items = self.decompressor.get_all_menu_items()
        for item in items:
            if item['dish_id'] == dish_id:
                return item
        return None
    
    def search_by_name(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search dishes by name (partial match).
        
        Args:
            search_term: Term to search for in dish names
            
        Returns:
            List of matching dishes
        """
        items = self.decompressor.get_all_menu_items()
        search_lower = search_term.lower()
        return [item for item in items if search_lower in item['name'].lower()]
    
    def get_categories(self) -> List[str]:
        """Get list of all available categories."""
        items = self.decompressor.get_all_menu_items()
        categories = set(item['category'] for item in items)
        return sorted(list(categories))
    
    def format_menu_response(self, items: List[Dict], show_details: bool = True) -> str:
        """
        Format menu items as a user-friendly string.
        
        Args:
            items: List of menu items
            show_details: Whether to show prep time and type
            
        Returns:
            Formatted string for display
        """
        if not items:
            return "No dishes found matching your criteria."
        
        lines = []
        for item in items:
            if show_details:
                line = (f"• {item['name']} (${item['price']:.2f}) - "
                       f"{item['type']}, ~{item['prep_time']} min")
            else:
                line = f"• {item['name']} - ${item['price']:.2f}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def format_full_menu_response(self) -> str:
        """Format the complete menu organized by category."""
        menu = self.get_full_menu()
        
        lines = ["📋 OUR MENU\n"]
        
        # Order categories logically
        category_order = ['Appetizers', 'Main Course', 'Desserts', 'Beverages']
        
        for category in category_order:
            if category in menu:
                lines.append(f"\n🍽️  {category.upper()}")
                lines.append("-" * 30)
                for item in menu[category]:
                    lines.append(
                        f"  {item['name']:<25} ${item['price']:>6.2f}  "
                        f"({item['type']})"
                    )
        
        return "\n".join(lines)
    
    def process_query(self, entities: Dict[str, Any]) -> str:
        """
        Process a menu query based on extracted entities.
        
        Args:
            entities: Dictionary of extracted entities from intent detection
            
        Returns:
            Formatted response string
        """
        category = entities.get('category')
        food_type = entities.get('food_type')
        max_price = entities.get('max_price')
        min_price = entities.get('min_price')
        
        # If no filters, show full menu
        if not any([category, food_type, max_price, min_price]):
            return self.format_full_menu_response()
        
        # Apply filters
        items = self.filter_menu(
            category=category,
            food_type=food_type,
            max_price=max_price,
            min_price=min_price
        )
        
        # Build response header
        header_parts = []
        if category:
            header_parts.append(category)
        if food_type:
            header_parts.append(food_type)
        if max_price:
            header_parts.append(f"under ${max_price}")
        if min_price:
            header_parts.append(f"above ${min_price}")
        
        header = f"🍽️  {' | '.join(header_parts)}:" if header_parts else "🍽️  Menu:"
        
        return f"{header}\n\n{self.format_menu_response(items)}"
