import json
from typing import Any, Dict


class Move:

    def __init__(self, id, name, accuracy, damage_class, power, pp, priority, stat_changes, type_name, contest_type):
        self.id = id
        self.name = name
        self.accuracy = accuracy
        self.damage_class = damage_class
        self.power = power
        self.pp = pp
        self.priority = priority
        self.stat_changes = stat_changes
        self.type_name = type_name
        self.contest_type = contest_type

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Move instance to a dictionary, suitable for database insertion.
        Handles conversion of 'stat_changes' to a JSON string for JSONB storage.
        """
        data = self.__dict__.copy()

        # Convert 'stat_changes' list of dicts to a JSON string for JSONB column
        # psycopg2 can often handle dicts/lists directly if the adapter is set up,
        # but explicitly dumping is safer and more portable.
        if isinstance(data.get('stat_changes'), list):
            data['stat_changes'] = json.dumps(data['stat_changes'])
        else:
            # Ensure it's an empty JSON array if not a list or None
            data['stat_changes'] = json.dumps([])

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Move instance from a dictionary (e.g., from a database row).
        Handles conversion of 'stat_changes' from JSON string back to a list of dicts.
        """
        processed_data = data.copy()

        # Handle 'stat_changes' from JSONB column
        if 'stat_changes' in processed_data and processed_data['stat_changes'] is not None:
            if isinstance(processed_data['stat_changes'], str):
                try:
                    # Attempt to parse JSON string
                    parsed_changes = json.loads(processed_data['stat_changes'])
                    if isinstance(parsed_changes, list):
                        processed_data['stat_changes'] = parsed_changes
                    else:
                        # If it's not a list after parsing, default to empty list
                        print(f"Warning: 'stat_changes' JSON parsed to non-list type {type(parsed_changes)}. Defaulting to empty list.")
                        processed_data['stat_changes'] = []
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse JSON string for 'stat_changes'. Defaulting to empty list.")
                    processed_data['stat_changes'] = []
            elif isinstance(processed_data['stat_changes'], list):
                # If it's already a list (e.g., if the DB driver parsed JSONB), use it directly
                pass
            else:
                print(f"Warning: 'stat_changes' has unexpected type {type(processed_data['stat_changes'])}. Defaulting to empty list.")
                processed_data['stat_changes'] = []
        else:
            processed_data['stat_changes'] = [] # Default to empty list if missing or None

        # Ensure required fields are present and have correct types
        required_keys = ['id', 'name', 'pp', 'priority', 'damage_class', 'type_name', 'contest_type']
        for key in required_keys:
            if key not in processed_data or processed_data[key] is None:
                raise ValueError(f"Move.from_dict: Required field '{key}' is missing or None.")

        # Ensure 'id', 'pp', 'priority' are integers
        for key in ['id', 'pp', 'priority']:
            if not isinstance(processed_data[key], int):
                try:
                    processed_data[key] = int(processed_data[key])
                except (ValueError, TypeError):
                    raise ValueError(f"Move.from_dict: '{key}' must be an integer.")

        # 'accuracy' and 'power' can be None, so no strict type enforcement beyond what's handled by int() if present
        if 'accuracy' in processed_data and processed_data['accuracy'] is not None and not isinstance(processed_data['accuracy'], int):
            try:
                processed_data['accuracy'] = int(processed_data['accuracy'])
            except (ValueError, TypeError):
                processed_data['accuracy'] = None # Set to None if conversion fails

        if 'power' in processed_data and processed_data['power'] is not None and not isinstance(processed_data['power'], int):
            try:
                processed_data['power'] = int(processed_data['power'])
            except (ValueError, TypeError):
                processed_data['power'] = None # Set to None if conversion fails

        return cls(**processed_data)
