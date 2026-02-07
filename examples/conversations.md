# 💬 Example Conversation Flows

This document shows example interactions with the Dining Reservation Chatbot.

---

## 1. Menu Browsing

### Full Menu
```
🧑 You: show menu

🤖 Bot: 📋 OUR MENU

🍽️  APPETIZERS
------------------------------
  Spring Rolls               $  8.99  (Veg)
  Chicken Wings              $ 12.99  (Non-Veg)
  Garlic Bread               $  6.99  (Veg)
  Soup of the Day            $  7.49  (Veg)
  Shrimp Cocktail            $ 14.99  (Non-Veg)

🍽️  MAIN COURSE
------------------------------
  Grilled Salmon             $ 24.99  (Non-Veg)
  Chicken Alfredo            $ 18.99  (Non-Veg)
  Vegetable Stir Fry         $ 15.99  (Veg)
  ...
```

### Filtered Menu
```
🧑 You: I want vegetarian dishes under $15

🤖 Bot: 🍽️  Veg | under $15:

• Spring Rolls ($8.99) - Veg, ~10 min
• Garlic Bread ($6.99) - Veg, ~8 min
• Soup of the Day ($7.49) - Veg, ~5 min
• Fruit Sorbet ($6.99) - Vegan, ~3 min
• Fresh Lemonade ($4.99) - Vegan, ~3 min
```

### Category Browse
```
🧑 You: what desserts do you have?

🤖 Bot: 🍽️  Desserts:

• Chocolate Lava Cake ($9.99) - Veg, ~15 min
• Cheesecake ($8.99) - Veg, ~5 min
• Ice Cream Sundae ($7.49) - Veg, ~5 min
• Fruit Sorbet ($6.99) - Vegan, ~3 min
• Tiramisu ($10.99) - Veg, ~10 min
```

---

## 2. Table Booking

### Check Availability First
```
🧑 You: available tables tonight

🤖 Bot: 🪑 Available Tables:

📍 2-Seater Tables:
   • T001 - 2026-02-07 at 12:00-13:00
   • T001 - 2026-02-07 at 18:00-19:00
   • T001 - 2026-02-07 at 19:00-20:00

📍 4-Seater Tables:
   • T003 - 2026-02-07 at 12:00-13:00
   • T003 - 2026-02-07 at 18:00-19:00
   ...
```

### Make a Reservation
```
🧑 You: book a table for 4 tomorrow at 7pm

🤖 Bot: ✅ Reservation Confirmed!
   Booking ID: BK7X2M9A
   Table: T003 (seats 4)
   Date: 2026-02-08
   Time: 19:00-20:00
   Party Size: 4
   Name: Guest
```

### Partial Information Booking
```
🧑 You: I need a table for 6 people

🤖 Bot: Table T005 (seats 6) is available at:
   • 12:00-13:00
   • 13:00-14:00
   • 19:00-20:00
   • 20:00-21:00

Please specify your preferred time to complete the booking.

🧑 You: 7pm please

🤖 Bot: ✅ Reservation Confirmed!
   Booking ID: BK9K4N2P
   Table: T005 (seats 6)
   ...
```

---

## 3. Cancellations

### Cancel with Booking ID
```
🧑 You: cancel booking #BK7X2M9A

🤖 Bot: ✅ Booking Cancelled Successfully!

   Booking ID: BK7X2M9A
   Table: T003
   Date: 2026-02-08
   Time: 19:00-20:00

The table is now available for other guests.
```

### Cancel Without ID
```
🧑 You: cancel my reservation

🤖 Bot: Please provide your booking ID to cancel.

Your current bookings:
   • BK9K4N2P - 2026-02-08 at 19:00-20:00 (Table T005)

Say 'cancel #BOOKING_ID' to cancel a specific booking.
```

---

## 4. Recommendations

### General Recommendation
```
🧑 You: recommend something

🤖 Bot: 🌟 Chef's Special Today:
   Grilled Salmon - $24.99
   Main Course | Non-Veg

⭐ Most Popular Dishes:

   • Grilled Salmon ($24.99) ⭐⭐⭐⭐
     Main Course | Non-Veg | ~25 min
   • Beef Steak ($29.99) ⭐⭐⭐⭐
     Main Course | Non-Veg | ~30 min
   • Chocolate Lava Cake ($9.99) ⭐⭐⭐⭐
     Desserts | Veg | ~15 min
```

### Vegetarian Recommendation
```
🧑 You: suggest something vegan

🤖 Bot: 🍽️ Complete Meal Suggestion (Vegan)
===================================

🥗 Appetizers:
   Soup of the Day - $7.49

🍝 Main Course:
   Vegan Buddha Bowl - $14.99

🍰 Desserts:
   Fruit Sorbet - $6.99

🥤 Beverages:
   Fresh Lemonade - $4.99

===================================
💰 Total: $34.46
```

### Budget-Friendly
```
🧑 You: what's good under $10?

🤖 Bot: ⭐ Best Dishes Under $10:

   • Spring Rolls ($8.99) ⭐⭐⭐⭐
     Appetizers | Veg | ~10 min
   • Cheesecake ($8.99) ⭐⭐⭐
     Desserts | Veg | ~5 min
   • Soup of the Day ($7.49) ⭐⭐⭐
     Appetizers | Veg | ~5 min
```

---

## 5. Help & Navigation

### Get Help
```
🧑 You: help

🤖 Bot: 📖 HOW TO USE THIS CHATBOT
════════════════════════════════════════

🍽️  MENU COMMANDS:
   • "show menu" - View full menu
   • "vegetarian dishes" - Filter by type
   • "appetizers under $10" - Filter by category and price

🪑 BOOKING COMMANDS:
   • "book a table for 4" - Start booking
   • "reserve table tomorrow at 7pm" - Specific booking
   • "available tables tonight" - Check availability

❌ CANCELLATION:
   • "cancel booking #BKXXXX" - Cancel by ID

💡 RECOMMENDATIONS:
   • "recommend something" - Get suggestions
   • "suggest a vegan dish" - Type-specific

...
```

### Exit
```
🧑 You: bye

🤖 Bot: 👋 Thank you for visiting! Goodbye and see you soon!
```

---

## 6. Error Handling

### Unknown Input
```
🧑 You: asdfghjkl

🤖 Bot: I'm not sure I understand. Could you rephrase that?

Try commands like:
  • 'show menu'
  • 'book a table for 2'
  • 'recommend something'
  • 'help' for more options