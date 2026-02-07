# 🍽️ Dining Reservation Chatbot

A Python-based chatbot for restaurant reservations using **compressed data structures** for efficient storage and fast queries. This project demonstrates intermediate-level AI concepts including rule-based intent detection, data compression, and modular design.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📋 **Menu Querying** | Browse menu with filters (category, type, price) |
| 🪑 **Table Booking** | Reserve tables by date, time, and party size |
| ❌ **Cancellations** | Cancel bookings and restore availability |
| 💡 **Recommendations** | Get dish suggestions based on preferences |
| 📊 **Availability Check** | View available tables in real-time |

## 🚀 Quick Start

```bash
# Navigate to project directory
cd dining-chatbot

# Run the chatbot
python main.py
```

No external dependencies required - uses Python standard library only!

## 🏗️ Architecture

```
dining-chatbot/
├── data/
│   ├── raw/                 # Original CSV data files
│   │   ├── menu.csv         # Restaurant menu (25 dishes)
│   │   └── tables.csv       # Table availability slots
│   └── compressed/          # Compressed JSON data
├── src/
│   ├── compression/         # Data encoding/decoding
│   │   ├── encoder.py       # Dictionary, RLE, Bit encoding
│   │   └── decoder.py       # Decompression utilities
│   ├── handlers/            # Feature handlers
│   │   ├── menu_handler.py
│   │   ├── booking_handler.py
│   │   ├── cancel_handler.py
│   │   └── recommend_handler.py
│   ├── intent/              # NLU components
│   │   └── detector.py      # Rule-based intent detection
│   └── chatbot.py           # Main conversation loop
├── tests/
│   └── test_all.py          # End-to-end tests
├── examples/
│   └── conversations.md     # Example dialogues
└── main.py                  # Entry point
```

## 📦 Data Compression Techniques

This project uses three compression methods for efficient data storage:

### 1. Dictionary Encoding
Maps repeated strings to integer IDs for faster comparisons.
```
["Veg", "Non-Veg", "Veg"] → [0, 1, 0] + Dictionary: {Veg: 0, Non-Veg: 1}
```

### 2. Run-Length Encoding (RLE)
Compresses consecutive repeated values.
```
[1, 1, 1, 2, 2, 3, 3, 3, 3] → [(1, 3), (2, 2), (3, 4)]
```

### 3. Bit Encoding
Converts categorical data to compact bit representations.
```
"Veg" → 0b00, "Non-Veg" → 0b01, "Vegan" → 0b10
```

## 🎯 Intent Detection

The chatbot uses **rule-based pattern matching** (no ML required):

| Intent | Example Phrases |
|--------|-----------------|
| `menu_query` | "show menu", "vegetarian dishes", "appetizers under $10" |
| `book_table` | "book a table for 4", "reserve tomorrow at 7pm" |
| `cancel_booking` | "cancel booking #BK123", "cancel my reservation" |
| `check_availability` | "available tables", "free tables tonight" |
| `recommend` | "recommend something", "what's popular?" |

## 💬 Example Usage

```
🧑 You: Show me vegetarian appetizers under $10

🤖 Bot: 🍽️  Appetizers | Veg | under $10:

• Spring Rolls ($8.99) - Veg, ~10 min
• Garlic Bread ($6.99) - Veg, ~8 min
• Soup of the Day ($7.49) - Veg, ~5 min
```

```
🧑 You: Book a table for 4 tomorrow at 7pm

🤖 Bot: ✅ Reservation Confirmed!
   Booking ID: BK7X2M9A
   Table: T003 (seats 4)
   Date: 2026-02-08
   Time: 19:00-20:00
   Party Size: 4
```

## 🧪 Running Tests

```bash
python tests/test_all.py
```

The test suite covers:
- ✅ Compression/Decompression round-trips
- ✅ Intent detection accuracy
- ✅ Handler functionality
- ✅ Chatbot integration

## 📚 Learning Outcomes

This project teaches:
1. **Data Compression** - Dictionary, RLE, and bit encoding
2. **NLU Basics** - Rule-based intent detection and entity extraction
3. **Modular Design** - Separating concerns into handlers
4. **State Management** - Booking persistence and updates
5. **Terminal UI** - Interactive conversation loops

## 🛠️ Extending the Project

Ideas for enhancement:
- Add SQLite database for persistent storage
- Implement user authentication
- Add price sorting options
- Integrate with a calendar API
- Add multi-language support

## 📝 License

MIT License - Feel free to use this project for learning!
