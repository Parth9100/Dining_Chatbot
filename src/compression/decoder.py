"""
Data Decompression Module - Decoder
Implements reverse operations for Dictionary, RLE, and Bit decoding.
Supports selective decompression for efficient queries.

Key Features:
1. On-demand decompression (only decode what's needed)
2. Fast lookups using reverse dictionaries
3. Efficient RLE expansion for specific indices
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class DictionaryDecoder:
    """
    Decodes dictionary-encoded values back to original strings.
    
    Example:
        Dictionary: {0: "Veg", 1: "Non-Veg", 2: "Vegan"}
        Encoded: [0, 1, 0, 2, 0]
        -> Decoded: ["Veg", "Non-Veg", "Veg", "Vegan", "Veg"]
    """
    
    def __init__(self, dictionary: Dict[int, str]):
        """
        Initialize with reverse dictionary (int -> string).
        
        Args:
            dictionary: Mapping from integer IDs to original strings
        """
        # Ensure keys are integers (JSON loads them as strings)
        self.dictionary = {int(k): v for k, v in dictionary.items()}
    
    def decode_value(self, encoded: int) -> str:
        """Decode a single encoded value."""
        return self.dictionary.get(encoded, f"UNKNOWN_{encoded}")
    
    def decode_column(self, encoded_values: List[int]) -> List[str]:
        """Decode an entire column of encoded values."""
        return [self.decode_value(v) for v in encoded_values]
    
    def decode_at_index(self, encoded_values: List[int], index: int) -> str:
        """Decode only a specific index (for selective decompression)."""
        if 0 <= index < len(encoded_values):
            return self.decode_value(encoded_values[index])
        raise IndexError(f"Index {index} out of range")


class RLEDecoder:
    """
    Decodes Run-Length Encoded data back to original sequence.
    
    Example:
        Encoded: [(1, 3), (2, 2), (3, 4)]
        -> Decoded: [1, 1, 1, 2, 2, 3, 3, 3, 3]
    
    Also supports efficient random access without full expansion.
    """
    
    @staticmethod
    def decode(encoded: List[Tuple[Any, int]]) -> List[Any]:
        """
        Fully decode RLE data.
        
        Args:
            encoded: List of (value, count) tuples or [value, count] lists
            
        Returns:
            Expanded list of values
        """
        decoded = []
        for item in encoded:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                value, count = item
                decoded.extend([value] * count)
        return decoded
    
    @staticmethod
    def decode_at_index(encoded: List[Tuple[Any, int]], index: int) -> Any:
        """
        Get value at specific index WITHOUT fully expanding.
        Much faster for sparse access patterns.
        
        Args:
            encoded: RLE encoded data
            index: Position to retrieve
            
        Returns:
            Value at the specified index
        """
        current_pos = 0
        for item in encoded:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                value, count = item
                if current_pos + count > index:
                    return value
                current_pos += count
        raise IndexError(f"Index {index} out of range")
    
    @staticmethod
    def decode_range(encoded: List[Tuple[Any, int]], start: int, end: int) -> List[Any]:
        """
        Decode only a specific range of indices.
        
        Args:
            encoded: RLE encoded data
            start: Start index (inclusive)
            end: End index (exclusive)
            
        Returns:
            Values in the specified range
        """
        result = []
        current_pos = 0
        
        for item in encoded:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                value, count = item
                run_start = current_pos
                run_end = current_pos + count
                
                # Check if this run overlaps with our range
                if run_end > start and run_start < end:
                    # Calculate overlap
                    overlap_start = max(run_start, start)
                    overlap_end = min(run_end, end)
                    result.extend([value] * (overlap_end - overlap_start))
                
                current_pos = run_end
                
                # Early exit if we've passed the end
                if current_pos >= end:
                    break
        
        return result


class BitDecoder:
    """
    Decodes bit-encoded categorical data.
    
    Example:
        Categories: ["Veg", "Non-Veg", "Vegan"]
        Encoded: [0, 1, 0, 2, 0]
        -> Decoded: ["Veg", "Non-Veg", "Veg", "Vegan", "Veg"]
    """
    
    def __init__(self, categories: List[str]):
        """
        Initialize with the list of categories.
        
        Args:
            categories: List where index = bit value
        """
        self.categories = categories
    
    def decode_value(self, bit_value: int) -> str:
        """Decode a single bit value to category."""
        if 0 <= bit_value < len(self.categories):
            return self.categories[bit_value]
        return f"UNKNOWN_{bit_value}"
    
    def decode_column(self, encoded_values: List[int]) -> List[str]:
        """Decode an entire column."""
        return [self.decode_value(v) for v in encoded_values]
    
    def unpack_bits(self, packed: bytes, count: int, bits_per_value: int = 2) -> List[int]:
        """
        Unpack bit-packed data.
        
        Args:
            packed: Packed bytes
            count: Number of values to unpack
            bits_per_value: Bits per value (2 for up to 4 categories)
            
        Returns:
            List of unpacked values
        """
        values = []
        values_per_byte = 8 // bits_per_value
        mask = (1 << bits_per_value) - 1
        
        for byte_val in packed:
            for j in range(values_per_byte):
                if len(values) >= count:
                    break
                val = (byte_val >> (j * bits_per_value)) & mask
                values.append(val)
        
        return values[:count]


class DataDecompressor:
    """
    Main decompression class that handles on-demand data decoding.
    Optimized for fast queries by decompressing only needed data.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize decompressor with data directory path.
        
        Args:
            data_dir: Path to the data directory
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        self.compressed_dir = self.data_dir / "compressed"
        
        # Cached compressed data
        self._menu_data: Optional[Dict] = None
        self._tables_data: Optional[Dict] = None
        
        # Cached decoders
        self._menu_decoders: Dict[str, Any] = {}
        self._tables_decoders: Dict[str, Any] = {}
    
    def _load_menu_data(self) -> Dict[str, Any]:
        """Load and cache compressed menu data."""
        if self._menu_data is None:
            menu_path = self.compressed_dir / "menu_compressed.json"
            with open(menu_path, 'r', encoding='utf-8') as f:
                self._menu_data = json.load(f)
            
            # Initialize decoders
            dicts = self._menu_data['dictionaries']
            self._menu_decoders = {
                'names': DictionaryDecoder(dicts['names']),
                'categories': DictionaryDecoder(dicts['categories']),
                'types': BitDecoder(dicts['types'])
            }
        
        return self._menu_data
    
    def _load_tables_data(self) -> Dict[str, Any]:
        """Load and cache compressed tables data."""
        if self._tables_data is None:
            tables_path = self.compressed_dir / "tables_compressed.json"
            with open(tables_path, 'r', encoding='utf-8') as f:
                self._tables_data = json.load(f)
            
            # Initialize decoders
            dicts = self._tables_data['dictionaries']
            self._tables_decoders = {
                'table_ids': DictionaryDecoder(dicts['table_ids']),
                'dates': DictionaryDecoder(dicts['dates']),
                'time_slots': DictionaryDecoder(dicts['time_slots']),
                'statuses': BitDecoder(dicts['statuses'])
            }
        
        return self._tables_data
    
    def get_menu_item(self, index: int) -> Dict[str, Any]:
        """
        Get a single menu item by index (selective decompression).
        
        Args:
            index: Index of the menu item
            
        Returns:
            Dictionary with full menu item details
        """
        data = self._load_menu_data()
        items = data['data']
        
        if index < 0 or index >= len(items['dish_ids']):
            raise IndexError(f"Menu item index {index} out of range")
        
        return {
            'dish_id': items['dish_ids'][index],
            'name': self._menu_decoders['names'].decode_value(items['names'][index]),
            'category': self._menu_decoders['categories'].decode_value(items['categories'][index]),
            'price': items['prices_cents'][index] / 100,  # Convert back to dollars
            'type': self._menu_decoders['types'].decode_value(items['types'][index]),
            'prep_time': items['prep_times'][index]
        }
    
    def get_all_menu_items(self) -> List[Dict[str, Any]]:
        """Get all menu items (full decompression)."""
        data = self._load_menu_data()
        count = data['metadata']['total_dishes']
        return [self.get_menu_item(i) for i in range(count)]
    
    def filter_menu(self, 
                    category: str = None, 
                    food_type: str = None,
                    max_price: float = None,
                    min_price: float = None) -> List[Dict[str, Any]]:
        """
        Filter menu items efficiently using encoded data.
        
        Args:
            category: Filter by category (Appetizers, Main Course, etc.)
            food_type: Filter by type (Veg, Non-Veg, Vegan)
            max_price: Maximum price filter
            min_price: Minimum price filter
            
        Returns:
            List of matching menu items
        """
        data = self._load_menu_data()
        items = data['data']
        dicts = data['dictionaries']
        
        # Get encoded filter values for fast comparison
        category_code = None
        type_code = None
        
        if category:
            # Find category code
            for code, cat in dicts['categories'].items():
                if cat.lower() == category.lower():
                    category_code = int(code)
                    break
        
        if food_type:
            # Find type code
            for i, t in enumerate(dicts['types']):
                if t.lower() == food_type.lower():
                    type_code = i
                    break
        
        # Convert price to cents for comparison
        max_cents = int(max_price * 100) if max_price else None
        min_cents = int(min_price * 100) if min_price else None
        
        # Filter using encoded values (fast integer comparisons)
        results = []
        for i in range(len(items['dish_ids'])):
            # Check category
            if category_code is not None and items['categories'][i] != category_code:
                continue
            
            # Check type
            if type_code is not None and items['types'][i] != type_code:
                continue
            
            # Check price range
            price = items['prices_cents'][i]
            if max_cents is not None and price > max_cents:
                continue
            if min_cents is not None and price < min_cents:
                continue
            
            # Passed all filters - decompress this item
            results.append(self.get_menu_item(i))
        
        return results
    
    def get_table_slot(self, index: int) -> Dict[str, Any]:
        """
        Get a single table slot by index.
        
        Args:
            index: Index of the table slot
            
        Returns:
            Dictionary with table slot details
        """
        data = self._load_tables_data()
        items = data['data']
        
        # Expand RLE status for this index
        status_encoded = RLEDecoder.decode_at_index(items['statuses_rle'], index)
        
        return {
            'table_id': self._tables_decoders['table_ids'].decode_value(items['table_ids'][index]),
            'capacity': items['capacities'][index],
            'date': self._tables_decoders['dates'].decode_value(items['dates'][index]),
            'time_slot': self._tables_decoders['time_slots'].decode_value(items['time_slots'][index]),
            'status': self._tables_decoders['statuses'].decode_value(status_encoded)
        }
    
    def get_all_table_slots(self) -> List[Dict[str, Any]]:
        """Get all table slots (full decompression)."""
        data = self._load_tables_data()
        count = data['metadata']['total_slots']
        return [self.get_table_slot(i) for i in range(count)]
    
    def find_available_tables(self,
                              date: str = None,
                              time_slot: str = None,
                              min_capacity: int = None) -> List[Dict[str, Any]]:
        """
        Find available tables efficiently.
        
        Args:
            date: Filter by date (YYYY-MM-DD)
            time_slot: Filter by time slot (HH:MM-HH:MM)
            min_capacity: Minimum required capacity
            
        Returns:
            List of available table slots
        """
        data = self._load_tables_data()
        items = data['data']
        dicts = data['dictionaries']
        
        # Get encoded filter values
        date_code = None
        time_code = None
        
        if date:
            for code, d in dicts['dates'].items():
                if d == date:
                    date_code = int(code)
                    break
        
        if time_slot:
            for code, t in dicts['time_slots'].items():
                if t == time_slot:
                    time_code = int(code)
                    break
        
        # Expand RLE statuses (needed for filtering)
        all_statuses = RLEDecoder.decode(items['statuses_rle'])
        
        # Available status code is 0
        available_code = 0
        
        results = []
        for i in range(len(items['table_ids'])):
            # Check if available
            if all_statuses[i] != available_code:
                continue
            
            # Check date
            if date_code is not None and items['dates'][i] != date_code:
                continue
            
            # Check time slot
            if time_code is not None and items['time_slots'][i] != time_code:
                continue
            
            # Check capacity
            if min_capacity is not None and items['capacities'][i] < min_capacity:
                continue
            
            # Passed all filters
            results.append(self.get_table_slot(i))
        
        return results
    
    def update_table_status(self, table_id: str, date: str, time_slot: str, 
                           new_status: str) -> bool:
        """
        Update a table's status (for booking/cancellation).
        Note: This requires re-encoding and saving.
        
        Args:
            table_id: Table ID to update
            date: Date of the slot
            time_slot: Time slot to update
            new_status: New status (Available, Reserved, Occupied)
            
        Returns:
            True if updated successfully
        """
        data = self._load_tables_data()
        items = data['data']
        dicts = data['dictionaries']
        
        # Find the matching slot
        target_index = None
        
        # Get encoded values for comparison
        table_code = None
        date_code = None
        time_code = None
        
        for code, tid in dicts['table_ids'].items():
            if tid == table_id:
                table_code = int(code)
                break
        
        for code, d in dicts['dates'].items():
            if d == date:
                date_code = int(code)
                break
        
        for code, t in dicts['time_slots'].items():
            if t == time_slot:
                time_code = int(code)
                break
        
        if table_code is None or date_code is None or time_code is None:
            return False
        
        # Find matching index
        for i in range(len(items['table_ids'])):
            if (items['table_ids'][i] == table_code and
                items['dates'][i] == date_code and
                items['time_slots'][i] == time_code):
                target_index = i
                break
        
        if target_index is None:
            return False
        
        # Expand RLE, update, and re-encode
        all_statuses = RLEDecoder.decode(items['statuses_rle'])
        
        # Get new status code
        new_status_code = dicts['statuses'].index(new_status) if new_status in dicts['statuses'] else 0
        all_statuses[target_index] = new_status_code
        
        # Re-encode with RLE
        from .encoder import RLEEncoder
        items['statuses_rle'] = RLEEncoder.encode_to_list(all_statuses)
        
        # Save updated data
        tables_path = self.compressed_dir / "tables_compressed.json"
        with open(tables_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Clear cache to reload on next access
        self._tables_data = None
        self._tables_decoders = {}
        
        return True


# Convenience function
def main():
    """Test decompression when run as a script."""
    decompressor = DataDecompressor()
    
    print("=" * 50)
    print("Testing Menu Decompression")
    print("=" * 50)
    
    # Test single item
    print("\nFirst menu item:")
    item = decompressor.get_menu_item(0)
    print(f"  {item}")
    
    # Test filter
    print("\nVegetarian Appetizers under $10:")
    items = decompressor.filter_menu(category="Appetizers", food_type="Veg", max_price=10)
    for item in items:
        print(f"  {item['name']}: ${item['price']}")
    
    print("\n" + "=" * 50)
    print("Testing Table Decompression")
    print("=" * 50)
    
    # Test available tables
    print("\nAvailable tables for 4+ people:")
    tables = decompressor.find_available_tables(min_capacity=4)
    for table in tables[:5]:  # Show first 5
        print(f"  {table['table_id']} (Cap: {table['capacity']}) - {table['date']} {table['time_slot']}")


if __name__ == "__main__":
    main()
