from asyncio.log import logger
import random
from typing import Any, Dict
import uuid


class Trade:

    def __init__(self, id, local_id, user1, user2, user1_pokemon_id, user2_pokemon_id, user1_money, user2_money, user1_item, user2_item, active):
        if id:
            self.id = id
        else:
            self.id = uuid.uuid4()
        if local_id:
            self.local_id = local_id
        else:
            self.local_id = random.randrange(1,999)
        self.user1 = user1
        self.user2 = user2
        self.user1_pokemon_id: uuid = user1_pokemon_id
        self.user2_pokemon_id: uuid = user2_pokemon_id
        self.user1_money = user1_money
        self.user2_money = user2_money
        self.user1_item = user1_item
        self.user2_item = user2_item
        self.active = active

    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Pokemon instance from a dictionary (e.g., from a database row).
        Handles conversions for UUIDs, booleans, lists, and JSONB fields.
        """
        processed_data = data.copy()

        # --- UUID Handling (id) ---
        uuid_keys = ['id', 'user1_pokemon_id', 'user2_pokemon_id']
        for key in uuid_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = uuid.UUID(processed_data[key])
                    except ValueError:
                        logger.warning(f"Trade.from_dict: Invalid UUID string for {key}: '{processed_data[key]}'. Setting to None/generating new.")
                        if key == 'id':
                            processed_data[key] = uuid.uuid4() # Generate for ID if invalid
                        elif key == 'user_id':
                            # user_id is NOT NULL, so raise error if invalid/missing
                            raise ValueError(f"Trade.from_dict: 'user_id' is required and invalid.")
                        else:
                            processed_data[key] = None
                elif not isinstance(processed_data[key], uuid.UUID):
                    logger.warning(f"Trade.from_dict: {key} has unexpected type {type(processed_data[key])}. Setting to None/generating new.")
                    if key == 'id':
                        processed_data[key] = uuid.uuid4()
                    elif key == 'user_id':
                        raise ValueError(f"Trade.from_dict: 'user_id' is required and invalid.")
                    else:
                        processed_data[key] = None
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

        