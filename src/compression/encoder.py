"""
Data Compression Module - Encoder
Implements Dictionary Encoding, Run-Length Encoding (RLE), and Bit Encoding
for efficient storage and fast queries of restaurant data.

Key Compression Techniques:
1. Dictionary Encoding: Maps repeated string values to integer IDs
2. RLE (Run-Length Encoding): Compresses consecutive repeated values
3. Bit Encoding: Converts categorical data to compact bit representations
"""

import json
import csv
from typing import Dict, List, Any, Tuple
from pathlib import Path


class DictionaryEncoder:
    """
    Dictionary Encoding: Maps unique string values to integer IDs.
    
    Example:
        ["Veg", "Non-Veg", "Veg", "Vegan", "Veg"]
        -> Dictionary: {"Veg": 0, "Non-Veg": 1, "Vegan": 2}
        -> Encoded: [0, 1, 0, 2, 0]
    
    Benefits:
        - Reduces storage for repeated strings
        - Enables faster comparisons (integer vs string)
    """
    
    def __init__(self):
        self.dictionary: Dict[str, int] = {}
        self.reverse_dict: Dict[int, str] = {}
        self.next_id: int = 0
    
    def encode_value(self, value: str) -> int:
        """Encode a single value, adding to dictionary if new."""
        if value not in self.dictionary:
            self.dictionary[value] = self.next_id
            self.reverse_dict[self.next_id] = value
            self.next_id += 1
        return self.dictionary[value]
    
    def encode_column(self, values: List[str]) -> Tuple[List[int], Dict[str, int]]:
        """
        Encode an entire column of values.
        
        Args:
            values: List of string values to encode
            
        Returns:
            Tuple of (encoded values list, dictionary mapping)
        """
        encoded = [self.encode_value(v) for v in values]
        return encoded, self.dictionary.copy()
    
    def get_dictionary(self) -> Dict[str, int]:
        """Return the current encoding dictionary."""
        return self.dictionary.copy()
    
    def reset(self):
        """Reset the encoder for a new column."""
        self.dictionary = {}
        self.reverse_dict = {}
        self.next_id = 0


class RLEEncoder:
    """
    Run-Length Encoding: Compresses consecutive repeated values.
    
    Example:
        [1, 1, 1, 2, 2, 3, 3, 3, 3]
        -> [(1, 3), (2, 2), (3, 4)]  # (value, count) pairs
    
    Benefits:
        - Very efficient for data with many consecutive duplicates
        - Common in table availability (many "Available" in a row)
    """
    
    @staticmethod
    def encode(values: List[Any]) -> List[Tuple[Any, int]]:
        """
        Encode a list using Run-Length Encoding.
        
        Args:
            values: List of values to encode
            
        Returns:
            List of (value, count) tuples
        """
        if not values:
            return []
        
        encoded = []
        current_value = values[0]
        count = 1
        
        for value in values[1:]:
            if value == current_value:
                count += 1
            else:
                encoded.append((current_value, count))
                current_value = value
                count = 1
        
        # Don't forget the last run
        encoded.append((current_value, count))
        return encoded
    
    @staticmethod
    def encode_to_list(values: List[Any]) -> List[List[Any]]:
        """
        Encode to JSON-serializable format.
        
        Returns:
            List of [value, count] lists (JSON-friendly)
        """
        encoded = RLEEncoder.encode(values)
        return [[v, c] for v, c in encoded]


class BitEncoder:
    """
    Bit Encoding: Converts categorical data to compact bit representations.
    
    Example (Type field with 3 categories):
        "Veg" -> 0b00 (0)
        "Non-Veg" -> 0b01 (1)  
        "Vegan" -> 0b10 (2)
    
    Example (Status field with 3 categories):
        "Available" -> 0b00 (0)
        "Reserved" -> 0b01 (1)
        "Occupied" -> 0b10 (2)
    
    Benefits:
        - Minimal storage for categorical data
        - Fast bitwise operations for filtering
    """
    
    def __init__(self, categories: List[str] = None):
        """
        Initialize with predefined categories or build dynamically.
        
        Args:
            categories: Optional list of all possible categories
        """
        self.categories = categories or []
        self.category_to_bits: Dict[str, int] = {}
        self.bits_to_category: Dict[int, str] = {}
        
        if categories:
            self._build_mapping()
    
    def _build_mapping(self):
        """Build the bit mapping from categories."""
        for i, cat in enumerate(self.categories):
            self.category_to_bits[cat] = i
            self.bits_to_category[i] = cat
    
    def encode_value(self, value: str) -> int:
        """Encode a single categorical value to bits."""
        if value not in self.category_to_bits:
            # Add new category dynamically
            new_bit = len(self.categories)
            self.categories.append(value)
            self.category_to_bits[value] = new_bit
            self.bits_to_category[new_bit] = value
        return self.category_to_bits[value]
    
    def encode_column(self, values: List[str]) -> Tuple[List[int], List[str]]:
        """
        Encode a column of categorical values.
        
        Returns:
            Tuple of (encoded bits list, categories list for decoding)
        """
        encoded = [self.encode_value(v) for v in values]
        return encoded, self.categories.copy()
    
    def pack_bits(self, values: List[int], bits_per_value: int = 2) -> bytes:
        """
        Pack multiple encoded values into bytes for maximum compression.
        
        Args:
            values: List of encoded integer values
            bits_per_value: Bits needed per value (2 for up to 4 categories)
            
        Returns:
            Packed bytes
        """
        if not values:
            return b''
        
        # Calculate how many values fit in one byte
        values_per_byte = 8 // bits_per_value
        packed = []
        
        for i in range(0, len(values), values_per_byte):
            byte_val = 0
            chunk = values[i:i + values_per_byte]
            for j, val in enumerate(chunk):
                byte_val |= (val & ((1 << bits_per_value) - 1)) << (j * bits_per_value)
            packed.append(byte_val)
        
        return bytes(packed)


class DataCompressor:
    """
    Main compression class that orchestrates all encoding types.
    Compresses menu and table data for efficient storage and queries.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize compressor with data directory path.
        
        Args:
            data_dir: Path to the data directory (containing raw/ and compressed/)
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to project data directory
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        self.raw_dir = self.data_dir / "raw"
        self.compressed_dir = self.data_dir / "compressed"
    
    def compress_menu(self) -> Dict[str, Any]:
        """
        Compress the menu.csv file using multiple encoding techniques.
        
        Compression Strategy:
        - Category: Dictionary encoding (few unique values)
        - Type: Bit encoding (Veg/Non-Veg/Vegan = 3 categories)
        - Price: Store as integers (cents) for faster comparison
        - Prep_Time: Store as-is (already integers)
        - Name: Dictionary encoding
        
        Returns:
            Compressed data structure
        """
        menu_path = self.raw_dir / "menu.csv"
        
        with open(menu_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Initialize encoders
        category_encoder = DictionaryEncoder()
        type_encoder = BitEncoder(["Veg", "Non-Veg", "Vegan"])
        name_encoder = DictionaryEncoder()
        
        # Extract and encode columns
        dish_ids = [row['Dish_ID'] for row in rows]
        names = [row['Name'] for row in rows]
        categories = [row['Category'] for row in rows]
        prices = [float(row['Price']) for row in rows]
        types = [row['Type'] for row in rows]
        prep_times = [int(row['Prep_Time']) for row in rows]
        
        # Apply encodings
        encoded_names, name_dict = name_encoder.encode_column(names)
        encoded_categories, category_dict = category_encoder.encode_column(categories)
        encoded_types, type_categories = type_encoder.encode_column(types)
        
        # Convert prices to cents (integers are faster)
        prices_cents = [int(p * 100) for p in prices]
        
        # Build compressed structure
        compressed = {
            "metadata": {
                "total_dishes": len(rows),
                "encoding_info": {
                    "name": "dictionary",
                    "category": "dictionary", 
                    "type": "bit",
                    "price": "cents_integer",
                    "prep_time": "raw_integer"
                }
            },
            "dictionaries": {
                "names": {v: k for k, v in name_dict.items()},  # Reverse for decoding
                "categories": {v: k for k, v in category_dict.items()},
                "types": type_categories
            },
            "data": {
                "dish_ids": dish_ids,
                "names": encoded_names,
                "categories": encoded_categories,
                "prices_cents": prices_cents,
                "types": encoded_types,
                "prep_times": prep_times
            }
        }
        
        # Save compressed data
        output_path = self.compressed_dir / "menu_compressed.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(compressed, f, indent=2)
        
        # Calculate compression stats
        original_size = menu_path.stat().st_size
        compressed_size = output_path.stat().st_size
        
        print(f"Menu Compression Complete:")
        print(f"  Original: {original_size} bytes")
        print(f"  Compressed: {compressed_size} bytes")
        print(f"  Ratio: {compressed_size/original_size:.2%}")
        
        return compressed
    
    def compress_tables(self) -> Dict[str, Any]:
        """
        Compress the tables.csv file using multiple encoding techniques.
        
        Compression Strategy:
        - Table_ID: Dictionary encoding
        - Date: Dictionary encoding (few unique dates)
        - Time_Slot: Dictionary encoding
        - Status: Bit encoding + RLE (many consecutive "Available")
        - Capacity: Store as-is (already integers)
        
        Returns:
            Compressed data structure
        """
        tables_path = self.raw_dir / "tables.csv"
        
        with open(tables_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Initialize encoders
        table_id_encoder = DictionaryEncoder()
        date_encoder = DictionaryEncoder()
        time_slot_encoder = DictionaryEncoder()
        status_encoder = BitEncoder(["Available", "Reserved", "Occupied"])
        
        # Extract columns
        table_ids = [row['Table_ID'] for row in rows]
        capacities = [int(row['Capacity']) for row in rows]
        dates = [row['Date'] for row in rows]
        time_slots = [row['Time_Slot'] for row in rows]
        statuses = [row['Status'] for row in rows]
        
        # Apply encodings
        encoded_table_ids, table_id_dict = table_id_encoder.encode_column(table_ids)
        encoded_dates, date_dict = date_encoder.encode_column(dates)
        encoded_time_slots, time_slot_dict = time_slot_encoder.encode_column(time_slots)
        encoded_statuses, status_categories = status_encoder.encode_column(statuses)
        
        # Apply RLE to status (often has consecutive same values)
        rle_statuses = RLEEncoder.encode_to_list(encoded_statuses)
        
        # Build compressed structure
        compressed = {
            "metadata": {
                "total_slots": len(rows),
                "encoding_info": {
                    "table_id": "dictionary",
                    "capacity": "raw_integer",
                    "date": "dictionary",
                    "time_slot": "dictionary",
                    "status": "bit+rle"
                }
            },
            "dictionaries": {
                "table_ids": {v: k for k, v in table_id_dict.items()},
                "dates": {v: k for k, v in date_dict.items()},
                "time_slots": {v: k for k, v in time_slot_dict.items()},
                "statuses": status_categories
            },
            "data": {
                "table_ids": encoded_table_ids,
                "capacities": capacities,
                "dates": encoded_dates,
                "time_slots": encoded_time_slots,
                "statuses_rle": rle_statuses
            }
        }
        
        # Save compressed data
        output_path = self.compressed_dir / "tables_compressed.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(compressed, f, indent=2)
        
        # Calculate compression stats
        original_size = tables_path.stat().st_size
        compressed_size = output_path.stat().st_size
        
        print(f"Tables Compression Complete:")
        print(f"  Original: {original_size} bytes")
        print(f"  Compressed: {compressed_size} bytes")
        print(f"  Ratio: {compressed_size/original_size:.2%}")
        
        return compressed
    
    def compress_all(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Compress all data files."""
        print("=" * 50)
        print("Starting Data Compression...")
        print("=" * 50)
        
        menu_data = self.compress_menu()
        print()
        tables_data = self.compress_tables()
        
        print()
        print("All data compressed successfully!")
        return menu_data, tables_data


# Convenience function for command-line usage
def main():
    """Compress all data when run as a script."""
    compressor = DataCompressor()
    compressor.compress_all()


if __name__ == "__main__":
    main()
