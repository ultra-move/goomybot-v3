import uuid
from typing import List, Dict, Any, Optional

class LearnedBy:
    def __init__(self, id: uuid.UUID, pokemon_id: int, move_id: int):
        """
        Initializes a LearnedBy instance.

        Args:
            id (uuid.UUID): The unique identifier for this learned relationship.
            pokemon_id (int): The ID of the Pokémon that learns the move.
            move_id (int): The ID of the move that is learned.
        """
        self.id = id
        self.pokemon_id = pokemon_id
        self.move_id = move_id

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the LearnedBy instance to a dictionary, suitable for database insertion.
        Converts UUID 'id' to string.
        """
        data = self.__dict__.copy()
        data['id'] = str(data['id']) # Convert UUID to string for storage
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a LearnedBy instance from a dictionary (e.g., from a database row).
        Handles conversion of 'id' from string to UUID.
        """
        processed_data = data.copy()
        required_int_keys = ['pokemon_id', 'move_id'] 

        if 'id' in processed_data and processed_data['id'] is not None:
            if isinstance(processed_data['id'], str):
                try:
                    processed_data['id'] = uuid.UUID(processed_data['id'])
                except ValueError:
                    raise ValueError(f"LearnedBy.from_dict: Invalid UUID string for 'id'.")
            elif not isinstance(processed_data['id'], uuid.UUID):
                raise ValueError(f"LearnedBy.from_dict: 'id' has unexpected type {type(processed_data['id'])}. Expected UUID or string.")
        else:
            raise ValueError(f"LearnedBy.from_dict: Required field 'id' is missing or None.")

        for key in required_int_keys:
            if key not in processed_data or processed_data[key] is None:
                raise ValueError(f"LearnedBy.from_dict: Required field '{key}' is missing or None.")
            if not isinstance(processed_data[key], int):
                try:
                    processed_data[key] = int(processed_data[key])
                except (ValueError, TypeError):
                    raise ValueError(f"LearnedBy.from_dict: '{key}' must be an integer.")

        return cls(**processed_data)
    
    def __str__(self):
        return f"ID: {self.id}\nPokemon ID: {self.pokemon_id}"