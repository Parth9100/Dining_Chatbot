"""
Recommendation Handler
Provides dish recommendations based on preferences and popularity.
"""

import random
from typing import Dict, List, Any, Optional
from ..compression.decoder import DataDecompressor


class RecommendHandler:
    """
    Handles dish recommendations.
    
    Recommendation Strategies:
    - By category preference
    - By food type (Veg, Non-Veg, Vegan)
    - Popular/Top-rated dishes
    - Random chef's special
    - Budget-friendly options
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize with data directory path."""
        self.decompressor = DataDecompressor(data_dir)
        
        # Simulated popularity scores (in real system, would come from orders)
        # Higher score = more popular
        self.popularity_scores = {
            'D006': 95,  # Grilled Salmon
            'D009': 92,  # Beef Steak
            'D007': 88,  # Chicken Alfredo
            'D016': 90,  # Chocolate Lava Cake
            'D010': 85,  # Mushroom Risotto
            'D001': 82,  # Spring Rolls
            'D011': 80,  # Vegan Buddha Bowl
            'D017': 78,  # Cheesecake
            'D002': 75,  # Chicken Wings
            'D008': 72,  # Vegetable Stir Fry
        }
    
    def get_popular_dishes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most popular dishes.
        
        Args:
            limit: Maximum number of dishes to return
            
        Returns:
            List of popular dishes sorted by popularity
        """
        all_dishes = self.decompressor.get_all_menu_items()
        
        # Sort by popularity score
        dishes_with_scores = []
        for dish in all_dishes:
            score = self.popularity_scores.get(dish['dish_id'], 50)
            dishes_with_scores.append((dish, score))
        
        dishes_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [d[0] for d in dishes_with_scores[:limit]]
    
    def get_category_recommendation(self, category: str) -> List[Dict[str, Any]]:
        """
        Get top recommendations from a specific category.
        
        Args:
            category: Category name (Appetizers, Main Course, etc.)
            
        Returns:
            List of recommended dishes from that category
        """
        dishes = self.decompressor.filter_menu(category=category)
        
        # Sort by popularity within category
        dishes_with_scores = []
        for dish in dishes:
            score = self.popularity_scores.get(dish['dish_id'], 50)
            dishes_with_scores.append((dish, score))
        
        dishes_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [d[0] for d in dishes_with_scores[:3]]
    
    def get_type_recommendation(self, food_type: str) -> List[Dict[str, Any]]:
        """
        Get recommendations by food type.
        
        Args:
            food_type: Veg, Non-Veg, or Vegan
            
        Returns:
            List of recommended dishes of that type
        """
        dishes = self.decompressor.filter_menu(food_type=food_type)
        
        # Sort by popularity
        dishes_with_scores = []
        for dish in dishes:
            score = self.popularity_scores.get(dish['dish_id'], 50)
            dishes_with_scores.append((dish, score))
        
        dishes_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [d[0] for d in dishes_with_scores[:3]]
    
    def get_budget_recommendation(self, max_price: float) -> List[Dict[str, Any]]:
        """
        Get budget-friendly recommendations.
        
        Args:
            max_price: Maximum price
            
        Returns:
            List of dishes under the price limit, sorted by value
        """
        dishes = self.decompressor.filter_menu(max_price=max_price)
        
        # Sort by popularity (best value items tend to be popular)
        dishes_with_scores = []
        for dish in dishes:
            score = self.popularity_scores.get(dish['dish_id'], 50)
            dishes_with_scores.append((dish, score))
        
        dishes_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [d[0] for d in dishes_with_scores[:5]]
    
    def get_chefs_special(self) -> Dict[str, Any]:
        """
        Get a random chef's special (surprise recommendation).
        
        Returns:
            A randomly selected dish from the top rated items
        """
        popular = self.get_popular_dishes(limit=10)
        return random.choice(popular) if popular else None
    
    def get_complete_meal(self, food_type: str = None, 
                          budget: float = None) -> Dict[str, List[Dict]]:
        """
        Recommend a complete meal (appetizer + main + dessert + beverage).
        
        Args:
            food_type: Filter by Veg/Non-Veg/Vegan
            budget: Optional total budget
            
        Returns:
            Dictionary with categories and recommended dish for each
        """
        categories = ['Appetizers', 'Main Course', 'Desserts', 'Beverages']
        meal = {}
        
        for category in categories:
            dishes = self.decompressor.filter_menu(
                category=category,
                food_type=food_type
            )
            
            if budget:
                # Filter by approximate budget per category
                budget_per_item = budget / 4
                dishes = [d for d in dishes if d['price'] <= budget_per_item]
            
            if dishes:
                # Pick the most popular one
                dishes_with_scores = []
                for dish in dishes:
                    score = self.popularity_scores.get(dish['dish_id'], 50)
                    dishes_with_scores.append((dish, score))
                
                dishes_with_scores.sort(key=lambda x: x[1], reverse=True)
                meal[category] = dishes_with_scores[0][0]
        
        return meal
    
    def format_recommendation(self, dishes: List[Dict], 
                             title: str = "Our Recommendations") -> str:
        """Format recommendations for display."""
        if not dishes:
            return "No dishes match your preferences."
        
        lines = [f"⭐ {title}:\n"]
        
        for dish in dishes:
            score = self.popularity_scores.get(dish['dish_id'], 50)
            stars = "⭐" * min(5, score // 20)
            lines.append(
                f"   • {dish['name']} (${dish['price']:.2f}) {stars}\n"
                f"     {dish['category']} | {dish['type']} | ~{dish['prep_time']} min"
            )
        
        return "\n".join(lines)
    
    def format_complete_meal(self, meal: Dict[str, Dict], 
                            food_type: str = None) -> str:
        """Format complete meal recommendation."""
        lines = ["🍽️ Complete Meal Suggestion"]
        if food_type:
            lines[0] += f" ({food_type})"
        lines.append("=" * 35)
        
        total = 0
        category_emojis = {
            'Appetizers': '🥗',
            'Main Course': '🍝',
            'Desserts': '🍰',
            'Beverages': '🥤'
        }
        
        for category, dish in meal.items():
            emoji = category_emojis.get(category, '🍽️')
            lines.append(f"\n{emoji} {category}:")
            lines.append(f"   {dish['name']} - ${dish['price']:.2f}")
            total += dish['price']
        
        lines.append(f"\n{'='*35}")
        lines.append(f"💰 Total: ${total:.2f}")
        
        return "\n".join(lines)
    
    def process_recommendation(self, entities: Dict[str, Any]) -> str:
        """
        Process a recommendation request from intent entities.
        
        Args:
            entities: Extracted entities from intent detection
            
        Returns:
            Response string
        """
        category = entities.get('category')
        food_type = entities.get('food_type')
        max_price = entities.get('max_price')
        
        # Priority: specific category > food type > budget > general
        if category:
            dishes = self.get_category_recommendation(category)
            return self.format_recommendation(
                dishes, 
                f"Top {category} Picks"
            )
        
        if food_type:
            # Offer complete meal for food type
            meal = self.get_complete_meal(food_type=food_type)
            return self.format_complete_meal(meal, food_type)
        
        if max_price:
            dishes = self.get_budget_recommendation(max_price)
            return self.format_recommendation(
                dishes,
                f"Best Dishes Under ${max_price}"
            )
        
        # Default: show chef's special and popular items
        special = self.get_chefs_special()
        popular = self.get_popular_dishes(limit=3)
        
        lines = ["🌟 Chef's Special Today:"]
        if special:
            lines.append(f"   {special['name']} - ${special['price']:.2f}")
            lines.append(f"   {special['category']} | {special['type']}")
        
        lines.append("\n" + self.format_recommendation(popular, "Most Popular Dishes"))
        
        return "\n".join(lines)
