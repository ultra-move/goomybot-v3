from asyncio.log import logger
import json
import random
import uuid
import datetime
from typing import Optional, Dict, Any

class User:

    def __init__(self,
                 id: int,
                 discord_username: str,
                 name: Optional[str] = None,
                 current_pokemon: Optional[uuid.UUID] = None,
                 region: str = "Kanto", # Default region
                 frame: int = 0,
                 wallet: int = 0,
                 level: int = 1,
                 exp: int = 0,
                 next_exp: int = 0,
                 tier_seed: float = random.random(),
                 type_seed: float = random.random(),
                 pokemon_seed: float = random.random(),
                 shiny_seed: float = random.random(),
                 item_seed: float = random.random(),
                 profile_image: Optional[str] = None,
                 last_activity_date: Optional[datetime.datetime] = None,
                 created_at: Optional[datetime.datetime] = None,
                 last_modified: Optional[datetime.datetime] = None,
                 view_table: dict ={}, 
                 filter: dict={},
                 order_by: dict={},
                 shiny_frame = -1,
                 raid_frame = 0,
                 event = False,
                 full_frame = False,
                 total_spent = 0,
                 battle_frame = 100000
                 ):
        
        self.id: int = id
        self.discord_username: str = discord_username
        self.name: Optional[str] = name
        self.current_pokemon: Optional[uuid.UUID] = current_pokemon
        self.region: str = region
        self.frame: int = frame
        self.raid_frame = raid_frame
        self.wallet: int = wallet
        self.level: int = level
        self.exp: int = exp
        self.next_exp: int = next_exp
        self.tier_seed: float = tier_seed
        self.type_seed: float = type_seed
        self.pokemon_seed: float = pokemon_seed
        self.shiny_seed: float = shiny_seed
        self.item_seed: float = item_seed
        self.profile_image: Optional[str] = profile_image
        self.view_table: dict = view_table
        self.shiny_frame = shiny_frame
        self.filter: dict = filter
        self.order_by: dict = order_by
        # Timestamps - handled with defaults if not provided (e.g., for new users)
        self.last_activity_date: datetime.datetime = last_activity_date or datetime.datetime.now(datetime.timezone.utc)
        self.created_at: datetime.datetime = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.last_modified: datetime.datetime = last_modified or datetime.datetime.now(datetime.timezone.utc)
        self.event = event
        self.full_frame = full_frame
        self.total_spent = total_spent
        self.battle_frame = battle_frame

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a User instance from a dictionary (e.g., typically from a database row or cache).
        Handles potential UUID, datetime, and float conversions.
        """
        processed_data = data.copy()

        # Convert 'id' from string if necessary (e.g., if coming from Redis HGETALL as string)
        if 'id' in processed_data and isinstance(processed_data['id'], str):
            try:
                processed_data['id'] = int(processed_data['id'])
            except ValueError:
                logger.warning(f"User.from_dict: Could not convert user ID '{processed_data['id']}' to int. Keeping as is.")
                # Decide if you want to keep as str or raise error, for now we keep it
                pass 
        if 'frame' in processed_data and isinstance(processed_data['frame'], str):
            processed_data['frame'] = int(processed_data['frame'])

        if 'battle_frame' in processed_data and isinstance(processed_data['battle_frame'], str):
            processed_data['battle_frame'] = int(processed_data['battle_frame'])

        if 'raid_frame' in processed_data and isinstance(processed_data['raid_frame'], str):
            processed_data['raid_frame'] = int(processed_data['raid_frame'])
        # UUID Handling (as previously defined, it's robust)
        if 'current_pokemon' in processed_data and processed_data['current_pokemon']:
            if isinstance(processed_data['current_pokemon'], str):
                try:
                    processed_data['current_pokemon'] = uuid.UUID(processed_data['current_pokemon'])
                except ValueError:
                    logger.warning(f"User.from_dict: Invalid UUID string for current_pokemon: '{processed_data['current_pokemon']}'. Setting to None.")
                    processed_data['current_pokemon'] = None
            elif not isinstance(processed_data['current_pokemon'], uuid.UUID):
                logger.debug(f"User.from_dict: current_pokemon is not a string or UUID: {processed_data['current_pokemon']}. Setting to None.")
                processed_data['current_pokemon'] = None
        else:
            processed_data['current_pokemon'] = None

        # --- NEW: Float Seed Values Handling ---
        float_seed_keys = [
            'tier_seed', 'type_seed', 'pokemon_seed', 'shiny_seed', 'item_seed'
        ]
        for key in float_seed_keys:
            if key in processed_data and processed_data[key] is not None:
                # Attempt to convert to float if it's a string or int
                if isinstance(processed_data[key], (str, int)):
                    try:
                        processed_data[key] = float(processed_data[key])
                    except (ValueError, TypeError):
                        logger.warning(f"User.from_dict: Could not convert '{key}' value '{processed_data[key]}' to float. Setting to 0.0.")
                        processed_data[key] = 0.0 # Default to 0.0 or handle as appropriate
                elif not isinstance(processed_data[key], float):
                    # If it's not a float, string, or int, and not None, log and default
                    logger.warning(f"User.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Setting to 0.0.")
                    processed_data[key] = 0.0
            else:
                # If key is missing or value is None, set a default float value
                processed_data[key] = 0.0 # Ensure it's always a float, even if None

        # Datetime Handling (as previously defined, it's robust)
        for key in ['last_activity_date', 'created_at', 'last_modified']:
            if key in processed_data and processed_data[key] is not None: # Check for None explicitly
                if isinstance(processed_data[key], str):
                    try:
                        dt_obj = datetime.datetime.fromisoformat(processed_data[key])
                        processed_data[key] = dt_obj if dt_obj.tzinfo is not None else dt_obj.replace(tzinfo=datetime.timezone.utc)
                    except ValueError:
                        logger.warning(f"User.from_dict: Invalid datetime string for {key}: '{processed_data[key]}'. Setting to current UTC time.")
                        processed_data[key] = datetime.datetime.now(datetime.timezone.utc)
                elif isinstance(processed_data[key], datetime.datetime) and processed_data[key].tzinfo is None:
                    processed_data[key] = processed_data[key].replace(tzinfo=datetime.timezone.utc)
            else:
                # If key is missing or None, set to current UTC time as a default for creation
                processed_data[key] = datetime.datetime.now(datetime.timezone.utc)
                # --- JSONB (Dictionary) Handling (ev, iv) ---
        jsonb_keys = ['view_table', 'filter', "order_by"]
        for key in jsonb_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = json.loads(processed_data[key])
                    except json.JSONDecodeError:
                        logger.warning(f"Pokemon.from_dict: Could not parse JSON string for '{key}'. Defaulting to empty dict.")
                        processed_data[key] = {}
                elif not isinstance(processed_data[key], dict):
                    logger.warning(f"Pokemon.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Defaulting to empty dict.")
                    processed_data[key] = {}
            else:
                processed_data[key] = {} # Default to empty dict if missing or None
                # --- Boolean Handling (is_shiny) ---
        if 'event' in processed_data and processed_data['event'] is not None:
            if isinstance(processed_data['event'], str):
                processed_data['event'] = processed_data['event'].lower() == 'true'
            elif isinstance(processed_data['event'], int):
                processed_data['event'] = bool(processed_data['event'])
            elif not isinstance(processed_data['event'], bool):
                logger.warning(f"Pokemon.from_dict: 'event' has unexpected type {type(processed_data['event'])}. Defaulting to False.")
                processed_data['event'] = False
        if 'full_frame' in processed_data and processed_data['full_frame'] is not None:
            if isinstance(processed_data['full_frame'], str):
                processed_data['full_frame'] = processed_data['full_frame'].lower() == 'true'
            elif isinstance(processed_data['full_frame'], int):
                processed_data['full_frame'] = bool(processed_data['full_frame'])
            elif not isinstance(processed_data['full_frame'], bool):
                logger.warning(f"Pokemon.from_dict: 'full_frame' has unexpected type {type(processed_data['full_frame'])}. Defaulting to False.")
                processed_data['full_frame'] = False             
        # --- Integer Handling (pokedex_id, tier, level, exp, next_exp) ---
        int_keys = ['wallet', 'shiny_frame', 'total_spent']
        for key in int_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        if processed_data[key]:
                            processed_data[key] = int(processed_data[key])
                    except ValueError:
                        logger.warning(f"User.from_dict: Could not convert '{key}' value '{processed_data[key]}' to int. Setting to default.")
                elif not isinstance(processed_data[key], int):
                    logger.warning(f"User.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Setting to default.")
            if processed_data[key] == None:
                processed_data[key] = 0
        return cls(**processed_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the User instance to a dictionary, suitable for database insertion
        or cache storage. Handles UUID and datetime conversions for storage.
        """
        data = self.__dict__.copy()
        
        # Convert UUID object to string for storage
        if data.get('current_pokemon'):
            data['current_pokemon'] = str(data['current_pokemon'])
        
        # Convert datetime objects to ISO format strings for storage
        for key in ['last_activity_date', 'created_at', 'last_modified']:
            if isinstance(data.get(key), datetime.datetime):
                data[key] = data[key].isoformat()

        for key in ['view_table', 'filter', 'order_by']:
            if isinstance(data.get(key), dict):
                data[key] = json.dumps(data[key])
        
        return data
    
    def reset_seeds(self):
        self.tier_seed: float = random.random()
        self.type_seed: float = random.random()
        self.pokemon_seed: float = random.random()
        self.shiny_seed: float = random.random()
        self.item_seed: float = random.random()

    def __repr__(self):
        return (f"<User id={self.id} username='{self.discord_username}' "
                f"level={self.level} region='{self.region}'>")

    def __str__(self):
        """
        Returns a human-readable string representation of the User object,
        including all key properties.
        """
        display_name = self.name if self.name else self.discord_username
        
        # Format timestamps for readability
        last_activity_str = self.last_activity_date.strftime('%Y-%m-%d %H:%M:%S UTC') if self.last_activity_date else 'N/A'
        created_at_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if self.created_at else 'N/A'
        
        return (
            f"ID: {self.id}\n"
            f"Display Name: {display_name}\n"
            f"Frame: {self.frame}\n"
            f"Raid Frame: {self.raid_frame}\n"
            f"Wallet: ${self.wallet:,.0f}\n"
        )
    
    
