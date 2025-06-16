from asyncio.log import logger
from typing import Any, Dict
import uuid


class Item:
    def __init__(self, id, user_id, name, quantity):
        if id:
            self.id = id
        else:
            self.id = uuid.uuid4()
        
        self.user_id = user_id
        self.name = name
        self.quantity = quantity
    
    @classmethod    
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Pokemon instance from a dictionary (e.g., from a database row).
        Handles conversions for UUIDs, booleans, lists, and JSONB fields.
        """
        processed_data = data.copy()

        # --- UUID Handling (id) ---
        uuid_keys = ['id']
        for key in uuid_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = uuid.UUID(processed_data[key])
                    except ValueError:
                        logger.warning(f"Item.from_dict: Invalid UUID string for {key}: '{processed_data[key]}'. Setting to None/generating new.")
                        if key == 'id':
                            processed_data[key] = uuid.uuid4() # Generate for ID if invalid
                        elif key == 'user_id':
                            # user_id is NOT NULL, so raise error if invalid/missing
                            raise ValueError(f"Item.from_dict: 'user_id' is required and invalid.")
                        else:
                            processed_data[key] = None
                elif not isinstance(processed_data[key], uuid.UUID):
                    logger.warning(f"Item.from_dict: {key} has unexpected type {type(processed_data[key])}. Setting to None/generating new.")
                    if key == 'id':
                        processed_data[key] = uuid.uuid4()
                    elif key == 'user_id':
                        raise ValueError(f"Item.from_dict: 'user_id' is required and invalid.")
                    else:
                        processed_data[key] = None
            elif key == 'id': # If id is missing, generate a new one
                processed_data[key] = uuid.uuid4()
            elif key == 'user_id': # If user_id is missing, it's a critical error
                raise ValueError(f"Item.from_dict: 'user_id' is a required field.")
            else: # Other optional UUIDs default to None if missing
                processed_data[key] = None

        # --- Integer Handling (pokedex_id, tier, level, exp, next_exp) ---
        int_keys = ['quantity']
        for key in int_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = int(processed_data[key])
                    except ValueError:
                        logger.warning(f"Item.from_dict: Could not convert '{key}' value '{processed_data[key]}' to int. Setting to default.")
                elif not isinstance(processed_data[key], int):
                    logger.warning(f"Item.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Setting to default.")
       
        return cls(**processed_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the item instance to a dictionary, suitable for database insertion
        or cache storage. Handles UUID and datetime conversions for storage.
        """
        data = self.__dict__.copy()
        
        # Convert UUID object to string for storage
        if data.get('id'):
            data['id'] = str(data['id'])
               
        return data
    
    def __str__(self):
        return (
            f"Name: {self.name}"
            f"Quantity: {self.quantity}"
        )