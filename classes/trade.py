from asyncio.log import logger
import uuid
import json
import random
from typing import Any, Dict, List, Optional

class Trade:
    """ Trade commands
    .trade @user
    .trade join <local_id>
    .trade add pokemon <local_id>
    .trade add item <item_name> <item_quantity>
    .trade add money <amount>
    .trade confirm <local_id>
    .trade cancel <local_id>
    """
    def __init__(self, id: Optional[uuid.UUID] = None, local_id: Optional[int] = None,
                 user1: Optional[Dict[str, Any]] = None, user2: Optional[Dict[str, Any]] = None,
                 status: str = ''):
        self.id = id if id is not None else uuid.uuid4()
        self.local_id = local_id if local_id is not None else random.randrange(1, 999)
        # Initialize user1 and user2 with the new structure including 'money' and 'confirmed'
        # user1 and user2 now store 'pokemon' as a list of dicts directly in memory
        self.user1 = user1 if user1 is not None else {'user_id': None, 'pokemon': [], 'items': [], 'money': 0, 'confirmed': False}
        self.user2 = user2 if user2 is not None else {'user_id': None, 'pokemon': [], 'items': [], 'money': 0, 'confirmed': False}
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        # Helper function to serialize user data for JSON (including nested UUIDs)
        def serialize_user_data_internal(user_data: Dict[str, Any]) -> Dict[str, Any]:
            serialized = user_data.copy()
            
            # user_id (int), money (int), and confirmed (bool) serialize directly to JSON.
            # No special conversion needed here.

            # Convert 'pokemon' from list of dicts (with UUIDs) to list of dicts (with string UUIDs)
            # The 'name' is already a string, so it's copied directly.
            if 'pokemon' in serialized and serialized['pokemon'] is not None:
                serialized_pokemon = []
                for p in serialized['pokemon']:
                    serialized_p = p.copy()
                    if 'id' in serialized_p and serialized_p['id'] is not None:
                        serialized_p['id'] = str(serialized_p['id'])
                    # 'name' is assumed to be a string and is copied directly
                    serialized_pokemon.append(serialized_p)
                serialized['pokemon'] = serialized_pokemon
            
            if 'items' in serialized and serialized['items'] is not None:
                # Items is a list of dictionaries. Iterate through each item.
                serialized_items = []
                for item in serialized['items']:
                    serialized_item = item.copy()
                    if 'id' in serialized_item and serialized_item['id'] is not None:
                        # Convert item 'id' (UUID) to string
                        serialized_item['id'] = str(serialized_item['id'])
                    # 'name' and 'quantity' (int) serialize directly without issue.
                    serialized_items.append(serialized_item)
                serialized['items'] = serialized_items
            return serialized

        # Apply internal serialization, then JSON dump user1 and user2
        # This means user1 and user2 will be JSON strings in the returned dict
        return {
            'id': str(self.id), # Ensure main Trade ID (UUID) is converted to string
            'local_id': self.local_id,
            'user1': json.dumps(serialize_user_data_internal(self.user1)), # JSON serialize user1
            'user2': json.dumps(serialize_user_data_internal(self.user2)), # JSON serialize user2
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        # Handle the main Trade 'id' field, allowing it to be a string or a UUID object
        trade_id = data.get('id')
        if isinstance(trade_id, str):
            try:
                trade_id = uuid.UUID(trade_id)
            except ValueError:
                logger.error(f"Invalid UUID string for trade ID: {trade_id}. Generating new UUID.")
                trade_id = uuid.uuid4()
        elif trade_id is None:
            trade_id = uuid.uuid4()

        # Helper function to deserialize user data (handling potential JSON strings or dicts)
        def deserialize_user_data(user_data: Any) -> Dict[str, Any]:
            # If user_data is a string, assume it's JSON and parse it first
            if isinstance(user_data, str):
                try:
                    user_data = json.loads(user_data)
                except json.JSONDecodeError:
                    logger.error(f"Could not decode JSON for user data: {user_data}. Returning default structure.")
                    return {'user_id': None, 'pokemon': [], 'items': [], 'money': 0, 'confirmed': False}

            # Ensure it's a dict before proceeding
            if not isinstance(user_data, dict):
                logger.error(f"User data is not a dictionary after deserialization: {user_data}. Returning default structure.")
                return {'user_id': None, 'pokemon': [], 'items': [], 'money': 0, 'confirmed': False}

            deserialized = user_data.copy()

            # Convert user_id to int if it exists and is not None
            if 'user_id' in deserialized and deserialized['user_id'] is not None:
                try:
                    deserialized['user_id'] = int(deserialized['user_id'])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert user_id '{deserialized['user_id']}' to int. Setting to None.")
                    deserialized['user_id'] = None
            
            # Convert money to int if it exists and is not None
            if 'money' in deserialized and deserialized['money'] is not None:
                try:
                    deserialized['money'] = int(deserialized['money']) 
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert money '{deserialized['money']}' to int. Setting to 0.")
                    deserialized['money'] = 0 # Default money to 0 on error
            else: # Ensure 'money' key exists with a default if missing or None
                deserialized['money'] = 0

            # Convert confirmed to bool if it exists and is not None
            if 'confirmed' in deserialized and deserialized['confirmed'] is not None:
                if isinstance(deserialized['confirmed'], str):
                    deserialized['confirmed'] = deserialized['confirmed'].lower() == 'true'
                elif not isinstance(deserialized['confirmed'], bool):
                    logger.warning(f"Could not convert confirmed '{deserialized['confirmed']}' to bool. Setting to False.")
                    deserialized['confirmed'] = False
            else:
                deserialized['confirmed'] = False

            # Handle 'pokemon' list (new structure)
            if 'pokemon' in deserialized and deserialized['pokemon'] is not None:
                if not isinstance(deserialized['pokemon'], list):
                    logger.warning(f"pokemon is not a list: {deserialized['pokemon']}. Initializing as empty list.")
                    deserialized['pokemon'] = []
                deserialized_pokemon = []
                for p_data in deserialized['pokemon']:
                    if not isinstance(p_data, dict):
                        logger.warning(f"Pokemon data is not a dictionary: {p_data}. Skipping.")
                        continue
                    deserialized_p = p_data.copy()
                    if 'id' in deserialized_p and deserialized_p['id'] is not None:
                        try:
                            deserialized_p['id'] = uuid.UUID(deserialized_p['id'])
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid UUID string for pokemon ID: {deserialized_p['id']}. Skipping.")
                            continue # Skip this pokemon if ID is invalid
                    else: # If 'id' is missing or None, this pokemon entry is invalid
                        logger.warning(f"Pokemon entry is missing 'id': {p_data}. Skipping.")
                        continue
                    
                    # IMPORTANT: Assume 'name' is already present in the data from the database
                    # If 'name' is missing, it implies a data integrity issue or old data format.
                    # You might add a default or log an error here if a name is truly mandatory.
                    if 'name' not in deserialized_p or deserialized_p['name'] is None:
                        logger.warning(f"Pokemon with ID {deserialized_p.get('id', 'N/A')} is missing a 'name'. Setting to 'Unknown'.")
                        deserialized_p['name'] = "Unknown" # Provide a default if name is unexpectedly missing
                        
                    deserialized_pokemon.append(deserialized_p)
                deserialized['pokemon'] = deserialized_pokemon
            # Handle old 'pokemon_ids' for backward compatibility during deserialization
            # THIS SECTION IS ONLY FOR MIGRATION. ONCE ALL DATA IS MIGRATED, YOU CAN REMOVE IT.
            elif 'pokemon_ids' in deserialized and deserialized['pokemon_ids'] is not None:
                logger.info("Found 'pokemon_ids' instead of 'pokemon'. Attempting backward-compatible deserialization.")
                if not isinstance(deserialized['pokemon_ids'], list):
                    logger.warning(f"pokemon_ids is not a list: {deserialized['pokemon_ids']}. Initializing as empty list.")
                    deserialized['pokemon'] = []
                else:
                    # **IMPORTANT: If you remove get_pokemon_name_by_id completely, you will need to handle
                    # how names are populated for old 'pokemon_ids' data during migration.**
                    # For a one-time migration script, you would query your master Pokemon list here.
                    # For ongoing runtime, if you expect old data, you *must* provide a mechanism to get names.
                    # For this example, I'll assume that for existing data, you either
                    # 1. Have already migrated, OR
                    # 2. You have a lookup readily available (like a cached dictionary)
                    # I'll keep the placeholder for conceptual completeness for a migration phase.
                    # IF YOU ONLY EVER SAVE NEW DATA WITH NAMES, THIS 'elif' BLOCK CAN BE REMOVED.
                    deserialized_pokemon_from_ids = []
                    # You'd likely need a temporary function here if this is purely for migration.
                    # For regular runtime after migration, this block is removed entirely.
                    # For now, let's just put placeholders if this is only for old data conversion:
                    for pid_str in deserialized['pokemon_ids']:
                        try:
                            pokemon_id_obj = uuid.UUID(pid_str)
                            # In a real migration, you would query your main Pokemon source for the name here.
                            # Example placeholder:
                            # pokemon_name = your_pokemon_service.get_name_by_id(pid_str)
                            # For now, let's use a generic name for migration purposes or just the ID:
                            pokemon_name = f"Pokemon_{pid_str[:8]}" # Or call a dedicated one-time lookup
                            deserialized_pokemon_from_ids.append({"id": pokemon_id_obj, "name": pokemon_name})
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid UUID string for pokemon_id: {pid_str}. Skipping.")
                    deserialized['pokemon'] = deserialized_pokemon_from_ids
                # Remove the old key after migration
                del deserialized['pokemon_ids']
            else: # Ensure 'pokemon' key exists with an empty list if missing or None
                deserialized['pokemon'] = []
            
            if 'items' in deserialized and deserialized['items'] is not None:
                if not isinstance(deserialized['items'], list):
                    logger.warning(f"items is not a list: {deserialized['items']}. Initializing as empty list.")
                    deserialized['items'] = []
                deserialized_items = []
                for item_data in deserialized['items']:
                    if not isinstance(item_data, dict):
                        logger.warning(f"Item data is not a dictionary: {item_data}. Skipping.")
                        continue
                    
                    deserialized_item = item_data.copy()
                    
                    if 'id' in deserialized_item and deserialized_item['id'] is not None:
                        try:
                            deserialized_item['id'] = uuid.UUID(deserialized_item['id'])
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid UUID string for item ID: {deserialized_item['id']}. Setting to None.")
                            deserialized_item['id'] = None
                    
                    if 'quantity' in deserialized_item and deserialized_item['quantity'] is not None:
                        try:
                            deserialized_item['quantity'] = int(deserialized_item['quantity'])
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert item quantity '{deserialized_item['quantity']}' to int. Setting to 0.")
                            deserialized_item['quantity'] = 0
                    
                    deserialized_items.append(deserialized_item)
                deserialized['items'] = deserialized_items
            else: # Ensure 'items' key exists with an empty list if missing or None
                deserialized['items'] = []

            return deserialized

        return cls(
            id=trade_id,
            local_id=data['local_id'],
            user1=deserialize_user_data(data.get('user1', {})), # Pass empty dict if 'user1' is missing
            user2=deserialize_user_data(data.get('user2', {})), # Pass empty dict if 'user2' is missing
            status=data.get('status', '')
        )
    
    def __str__(self):
        """
        Provides a human-readable string representation of the Trade object.
        """
        user1_info = self.user1
        user2_info = self.user2

        # Safely get user_ids, providing default if None
        user1_id_display = user1_info.get('user_id', 'N/A')
        user2_id_display = user2_info.get('user_id', 'N/A')

        # Format user 1's details
        user1_str = (
            f"User 1 (ID: {user1_id_display}):\n"
            f"  Money: {user1_info.get('money', 0)}\n"
            f"  Pokemon: {len(user1_info.get('pokemon', []))}\n"
            f"  Items: {len(user1_info.get('items', []))}\n"
            f"  Confirmed: {'Yes' if user1_info.get('confirmed', False) else 'No'}"
        )

        # Format user 2's details
        user2_str = (
            f"User 2 (ID: {user2_id_display}):\n"
            f"  Money: {user2_info.get('money', 0)}\n"
            f"  Pokemon: {len(user2_info.get('pokemon', []))}\n"
            f"  Items: {len(user2_info.get('items', []))}\n"
            f"  Confirmed: {'Yes' if user2_info.get('confirmed', False) else 'No'}"
        )

        return (
            f"--- Trade {self.local_id} (ID: {self.id}) ---\n"
            f"Status: {self.status.capitalize()}\n\n"
            f"{user1_str}\n\n"
            f"{user2_str}\n"
            f"--------------------------"
        )