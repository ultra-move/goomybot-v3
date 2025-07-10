import math
import random
import uuid
import datetime
import json
from typing import Optional, Dict, Any, List
import logging

# Configure a basic logger for demonstration purposes
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

NATURE_MODIFIERS: Dict[str, Dict[str, float]] = {
    "Hardy": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},
    "Docile": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},
    "Serious": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},
    "Bashful": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},
    "Quirky": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},

    "Lonely": {"attack": 1.1, "defense": 0.9, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},
    "Brave": {"attack": 1.1, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 0.9},
    "Adamant": {"attack": 1.1, "defense": 1.0, "special_attack": 0.9, "special_defense": 1.0, "speed": 1.0},
    "Naughty": {"attack": 1.1, "defense": 1.0, "special_attack": 1.0, "special_defense": 0.9, "speed": 1.0},

    "Bold": {"attack": 0.9, "defense": 1.1, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.0},
    "Relaxed": {"attack": 1.0, "defense": 1.1, "special_attack": 1.0, "special_defense": 1.0, "speed": 0.9},
    "Impish": {"attack": 1.0, "defense": 1.1, "special_attack": 0.9, "special_defense": 1.0, "speed": 1.0},
    "Lax": {"attack": 1.0, "defense": 1.1, "special_attack": 1.0, "special_defense": 0.9, "speed": 1.0},

    "Modest": {"attack": 0.9, "defense": 1.0, "special_attack": 1.1, "special_defense": 1.0, "speed": 1.0},
    "Mild": {"attack": 1.0, "defense": 0.9, "special_attack": 1.1, "special_defense": 1.0, "speed": 1.0},
    "Quiet": {"attack": 1.0, "defense": 1.0, "special_attack": 1.1, "special_defense": 1.0, "speed": 0.9},
    "Rash": {"attack": 1.0, "defense": 1.0, "special_attack": 1.1, "special_defense": 0.9, "speed": 1.0},

    "Calm": {"attack": 0.9, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.1, "speed": 1.0},
    "Gentle": {"attack": 1.0, "defense": 0.9, "special_attack": 1.0, "special_defense": 1.1, "speed": 1.0},
    "Sassy": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.1, "speed": 0.9},
    "Careful": {"attack": 1.0, "defense": 1.0, "special_attack": 0.9, "special_defense": 1.1, "speed": 1.0},

    "Timid": {"attack": 0.9, "defense": 1.0, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.1},
    "Hasty": {"attack": 1.0, "defense": 0.9, "special_attack": 1.0, "special_defense": 1.0, "speed": 1.1},
    "Jolly": {"attack": 1.0, "defense": 1.0, "special_attack": 0.9, "special_defense": 1.0, "speed": 1.1},
    "Naive": {"attack": 1.0, "defense": 1.0, "special_attack": 1.0, "special_defense": 0.9, "speed": 1.1},
}

class Pokemon:
    """
    Represents a specific Pokémon instance, storing its unique attributes,
    stats, and links to its owner and held item.
    """

    def __init__(self,
                 id: uuid.UUID,
                 user_id: int,
                 pokedex_id: int,
                 name: str,
                 is_shiny: bool = False,
                 tier: int = 1,
                 types: List[str] = [],
                 ability: str = "",
                 level: int = 1,
                 growth_rate = '',
                 exp: int = 0,
                 next_exp: int = 100,  # Default for level 1
                 nature: str = "default", # Default nature
                 sprite_front: str = "",
                 sprite_back: str = "",
                 nickname: Optional[str] = None,
                 original_user_id: Optional[int] = None,
                 region: Optional[str] = None,
                 gender: Optional[str] = None,
                 base_stats: Dict[str, int] = {},
                 stats: Dict[str, int]= {},
                 ev: Dict[str, int] = {},
                 iv: Dict[str, int] = {},
                 safe= False,
                 held_item_id: Optional[uuid.UUID] = None,
                 moves = [],
                 created_at: Optional[datetime.datetime] = None,
                 last_modified: Optional[datetime.datetime] = None):

        # Core identifiers
        self.id: uuid.UUID = id
        self.user_id: int = user_id
        self.pokedex_id: int = pokedex_id
        self.name: str = name
        self.nickname: Optional[str] = nickname
        self.original_user_id: Optional[int] = original_user_id

        # Basic attributes
        self.is_shiny: bool = is_shiny
        self.tier: int = tier
        self.types: List[str] = types if types is not None else []
        self.ability: str = ability
        self.gender: Optional[str] = gender
        self.region: Optional[str] = region
        if nature == 'default':
            self.nature = str(random.choice(list(NATURE_MODIFIERS.keys())))
        else:
            self.nature = nature
        # Progression
        self.level: int = level
        self.growth_rate = growth_rate
        if exp != 0:
            self.exp: int = exp
        else:
            self.exp = self.calculate_exp(level=level)
        self.next_exp: int = self.calculate_exp(level=level + 1) 

        # Stats (EVs and IVs)
        self.base_stats = base_stats
        self.ev: Dict[str, int] = ev
        self.iv: Dict[str, int] = iv
        self.stats: Dict[str, int] = self.calculate_stats()
        # Items
        self.held_item_id: Optional[uuid.UUID] = held_item_id

        # Sprites
        self.sprite_front: str = sprite_front
        self.sprite_back: str = sprite_back

        self.safe = safe
        self.moves = moves
        # Timestamps
        self.created_at: datetime.datetime = created_at or datetime.datetime.now(datetime.timezone.utc)
        self.last_modified: datetime.datetime = last_modified or datetime.datetime.now(datetime.timezone.utc)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Pokemon instance from a dictionary (e.g., from a database row).
        Handles conversions for UUIDs, booleans, lists, and JSONB fields.
        """
        processed_data = data.copy()

        # --- UUID Handling (id, user_id, original_user_id, held_item_id) ---
        uuid_keys = ['id', 'held_item_id']
        for key in uuid_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = uuid.UUID(processed_data[key])
                    except ValueError:
                        logger.warning(f"Pokemon.from_dict: Invalid UUID string for {key}: '{processed_data[key]}'. Setting to None/generating new.")
                        if key == 'id':
                            processed_data[key] = uuid.uuid4() # Generate for ID if invalid
                        elif key == 'user_id':
                            # user_id is NOT NULL, so raise error if invalid/missing
                            raise ValueError(f"Pokemon.from_dict: 'user_id' is required and invalid.")
                        else:
                            processed_data[key] = None
                elif not isinstance(processed_data[key], uuid.UUID):
                    logger.warning(f"Pokemon.from_dict: {key} has unexpected type {type(processed_data[key])}. Setting to None/generating new.")
                    if key == 'id':
                        processed_data[key] = uuid.uuid4()
                    elif key == 'user_id':
                        raise ValueError(f"Pokemon.from_dict: 'user_id' is required and invalid.")
                    else:
                        processed_data[key] = None
            elif key == 'id': # If id is missing, generate a new one
                processed_data[key] = uuid.uuid4()
            elif key == 'user_id': # If user_id is missing, it's a critical error
                raise ValueError(f"Pokemon.from_dict: 'user_id' is a required field.")
            else: # Other optional UUIDs default to None if missing
                processed_data[key] = None

        # --- Boolean Handling (is_shiny) ---
        if 'is_shiny' in processed_data and processed_data['is_shiny'] is not None:
            if isinstance(processed_data['is_shiny'], str):
                processed_data['is_shiny'] = processed_data['is_shiny'].lower() == 'true'
            elif isinstance(processed_data['is_shiny'], int):
                processed_data['is_shiny'] = bool(processed_data['is_shiny'])
            elif not isinstance(processed_data['is_shiny'], bool):
                logger.warning(f"Pokemon.from_dict: 'is_shiny' has unexpected type {type(processed_data['is_shiny'])}. Defaulting to False.")
                processed_data['is_shiny'] = False
        else:
            processed_data['is_shiny'] = False # Default to False if missing or None

        if 'safe' in processed_data and processed_data['safe'] is not None:
            if isinstance(processed_data['safe'], str):
                processed_data['safe'] = processed_data['safe'].lower() == 'true'
            elif isinstance(processed_data['safe'], int):
                processed_data['safe'] = bool(processed_data['safe'])
            elif not isinstance(processed_data['safe'], bool):
                logger.warning(f"Pokemon.from_dict: 'safe' has unexpected type {type(processed_data['safe'])}. Defaulting to False.")
                processed_data['safe'] = False
        else:
            processed_data['safe'] = False # Default to False if missing or None

        # --- Integer Handling (pokedex_id, tier, level, exp, next_exp) ---
        int_keys = ['pokedex_id', 'tier', 'level', 'exp', 'next_exp']
        for key in int_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = int(processed_data[key])
                    except ValueError:
                        logger.warning(f"Pokemon.from_dict: Could not convert '{key}' value '{processed_data[key]}' to int. Setting to default.")
                        processed_data[key] = 0 if key in ['exp'] else 1 if key in ['tier', 'level'] else 100 if key == 'next_exp' else 0 # Default values
                elif not isinstance(processed_data[key], int):
                    logger.warning(f"Pokemon.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Setting to default.")
                    processed_data[key] = 0 if key in ['exp'] else 1 if key in ['tier', 'level'] else 100 if key == 'next_exp' else 0 # Default values
            else:
                # Set default if missing or None
                processed_data[key] = 0 if key in ['exp'] else 1 if key in ['tier', 'level'] else 100 if key == 'next_exp' else 0 # Default values
        
        # Enforce check constraints
        if not (1 <= processed_data.get('tier', 1) <= 4):
            logger.warning(f"Pokemon.from_dict: 'tier' value {processed_data.get('tier')} out of range (1-4). Setting to 1.")
            processed_data['tier'] = 1
        else:
            processed_data['tier'] = int(processed_data['tier'])
        if not (1 <= processed_data.get('level', 1) <= 100):
            logger.warning(f"Pokemon.from_dict: 'level' value {processed_data.get('level')} out of range (1-100). Setting to 1.")
            processed_data['level'] = 1
        else:
            processed_data['level'] = int(processed_data['level'])
        
        # --- List of Strings Handling (types) ---
        if 'types' in processed_data and processed_data['types'] is not None:
            if isinstance(processed_data['types'], str):
                try:
                    # Attempt to parse as JSON array string, fallback to comma-separated
                    parsed_types = json.loads(processed_data['types'])
                    if isinstance(parsed_types, list) and all(isinstance(t, str) for t in parsed_types):
                        processed_data['types'] = parsed_types
                    else:
                        logger.warning(f"Pokemon.from_dict: 'types' string is not a valid JSON list. Splitting by comma.")
                        processed_data['types'] = [t.strip() for t in processed_data['types'].split(',') if t.strip()]
                except json.JSONDecodeError:
                    logger.warning(f"Pokemon.from_dict: 'types' string is not a valid JSON. Splitting by comma.")
                    processed_data['types'] = [t.strip() for t in processed_data['types'].split(',') if t.strip()]
            elif isinstance(processed_data['types'], list):
                processed_data['types'] = [str(t) for t in processed_data['types'] if t is not None] # Ensure all elements are strings
            else:
                logger.warning(f"Pokemon.from_dict: 'types' has unexpected type {type(processed_data['types'])}. Defaulting to empty list.")
                processed_data['types'] = []
        else:
            processed_data['types'] = [] # Default to empty list if missing or None
        # --- List of Strings Handling (types) ---
        if 'moves' in processed_data and processed_data['moves'] is not None:
            if isinstance(processed_data['moves'], str):
                try:
                    # Attempt to parse as JSON array string, fallback to comma-separated
                    parsed_types = json.loads(processed_data['moves'])
                    if isinstance(parsed_types, list) and all(isinstance(t, str) for t in parsed_types):
                        processed_data['moves'] = parsed_types
                    else:
                        logger.warning(f"Pokemon.from_dict: 'moves' string is not a valid JSON list. Splitting by comma.")
                        processed_data['moves'] = [t.strip() for t in processed_data['moves'].split(',') if t.strip()]
                except json.JSONDecodeError:
                    logger.warning(f"Pokemon.from_dict: 'moves' string is not a valid JSON. Splitting by comma.")
                    processed_data['moves'] = [t.strip() for t in processed_data['moves'].split(',') if t.strip()]
            elif isinstance(processed_data['moves'], list):
                processed_data['moves'] = [str(t) for t in processed_data['moves'] if t is not None] # Ensure all elements are strings
            else:
                logger.warning(f"Pokemon.from_dict: 'moves' has unexpected type {type(processed_data['moves'])}. Defaulting to empty list.")
                processed_data['moves'] = []
        else:
            processed_data['types'] = [] # Default to empty list if missing or None
        # --- JSONB (Dictionary) Handling (ev, iv) ---
        jsonb_keys = ['base_stats','stats','ev', 'iv']
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

        # --- Datetime Handling (created_at, last_modified) ---
        for key in ['created_at', 'last_modified']:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        dt_obj = datetime.datetime.fromisoformat(processed_data[key])
                        processed_data[key] = dt_obj if dt_obj.tzinfo is not None else dt_obj.replace(tzinfo=datetime.timezone.utc)
                    except ValueError:
                        logger.warning(f"Pokemon.from_dict: Invalid datetime string for {key}: '{processed_data[key]}'. Setting to current UTC time.")
                        processed_data[key] = datetime.datetime.now(datetime.timezone.utc)
                elif isinstance(processed_data[key], datetime.datetime) and processed_data[key].tzinfo is None:
                    processed_data[key] = processed_data[key].replace(tzinfo=datetime.timezone.utc)
            else:
                processed_data[key] = datetime.datetime.now(datetime.timezone.utc)

        # --- Ensure required fields are present ---
        required_keys = ['pokedex_id', 'name', 'ability', 'sprite_front']
        for key in required_keys:
            if key not in processed_data or processed_data[key] is None or processed_data[key] == "":
                raise ValueError(f"Pokemon.from_dict: Required field '{key}' is missing or empty.")
        
        return cls(**processed_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Pokemon instance to a dictionary, suitable for database insertion
        or cache storage. Handles UUID and datetime conversions for storage.
        Explicitly handles JSONB and TEXT[] types for psycopg2 compatibility.
        """
        data = self.__dict__.copy()
        
        # Convert UUID objects to string for storage
        uuid_keys = ['id', 'held_item_id']
        for key in uuid_keys:
            if data.get(key) is not None:
                data[key] = str(data[key])
        
        # Convert datetime objects to ISO format strings for storage
        for key in ['created_at', 'last_modified']:
            if isinstance(data.get(key), datetime.datetime):
                data[key] = data[key].isoformat()

        # Convert 'ev' and 'iv' dictionaries to JSON strings for JSONB columns
        # psycopg2 can often handle dicts directly if the adapter is set up,
        # but explicitly dumping is safer and more portable if not.
        if isinstance(data.get('base_stats'), dict):
            data['base_stats'] = json.dumps(data['base_stats'])
        if isinstance(data.get('stats'), dict):
            data['stats'] = json.dumps(data['stats'])
        if isinstance(data.get('ev'), dict):
            data['ev'] = json.dumps(data['ev'])
        if isinstance(data.get('iv'), dict):
            data['iv'] = json.dumps(data['iv'])
        
        # Ensure 'types' is a list of strings, which psycopg2 typically handles for TEXT[]
        # No special conversion needed here unless you expect non-list types
        if not isinstance(data.get('types'), list):
            data['types'] = [] # Default to empty list if not a list
        else:
            # Ensure all elements in the list are strings
            data['types'] = [str(item) for item in data['types']]
        if not isinstance(data.get('moves'), list):
            data['moves'] = [] # Default to empty list if not a list
        else:
            # Ensure all elements in the list are strings
            data['moves'] = [str(item) for item in data['moves']]
        return data
    
    def calculate_stats(self) -> Dict[str, int]:
        """
        Calculates a Pokémon's final stats based on base stats, Individual Values (IVs),
        Effort Values (EVs), level, and nature.

        Formulas used:
        HP = floor(0.01 x (2 x Base + IV + floor(0.25 x EV)) x Level) + Level + 10
        Other Stats = (floor(0.01 x (2 x Base + IV + floor(0.25 x EV)) x Level) + 5) x Nature

        Returns:
            Dict[str, int]: A dictionary of the calculated final stats.
        """
        calculated_stats: Dict[str, int] = {}
        nature = self.nature
        ivs = self.iv
        evs = self.ev
        level = self.level
        base_stats = self.base_stats

        # Ensure nature is valid
        if nature not in NATURE_MODIFIERS:
            print(f"Warning: Unknown nature '{nature}'. Using neutral modifiers (1.0 for all stats).")
            nature_modifiers = {stat: 1.0 for stat in ["attack", "defense", "special_attack", "special_defense", "speed"]}
        else:
            nature_modifiers = NATURE_MODIFIERS[nature]

        for stat_name, base_stat in base_stats.items():
            iv = ivs.get(stat_name, 0)
            ev = evs.get(stat_name, 0)

            # Calculate common part of the formula
            # floor(0.25 x EV)
            ev_calc_part = math.floor(0.25 * ev)

            # (2 x Base + IV + floor(0.25 x EV))
            main_calc_part = (2 * base_stat + iv + ev_calc_part)

            # floor(0.01 x (2 x Base + IV + floor(0.25 x EV)) x Level)
            level_calc_part = math.floor(0.01 * main_calc_part * level)

            if stat_name == 'hp':
                # HP formula: floor(...) + Level + 10
                calculated_stats[stat_name] = level_calc_part + level + 10
            else:
                # Other Stats formula: (floor(...) + 5) x Nature
                # Adjust stat_name for special attack/defense lookup in nature_modifiers if needed
                # The nature modifiers keys are "special_attack" and "special_defense"
                # Your base_stats keys might be "special-attack" and "special-defense"
                # It's safer to map them consistently.
                modifier_key = stat_name.replace('-', '_') # Convert "special-attack" to "special_attack"
                nature_multiplier = nature_modifiers.get(modifier_key, 1.0) # Default to 1.0 if stat not in nature_modifiers

                calculated_stats[stat_name] = math.floor((level_calc_part + 5) * nature_multiplier)

        return calculated_stats


    def __repr__(self):
        return (f"<Pokemon id={self.id} name='{self.name}' "
                f"level={self.level} user_id={self.user_id}>")

    def _format_dict_to_lines(self, data_dict, items_per_line=2, key_formatter=str.capitalize):
        """
        Helper method to format a dictionary into lines, with a specified number of items per line.
        """
        formatted_items = []
        for k, v in data_dict.items():
            formatted_items.append(f"{key_formatter(k)}: {v}")

        lines = []
        # Increase leading spaces for a more indented "block" look
        indent_prefix = "* " # 4 spaces for indentation
        for i in range(0, len(formatted_items), items_per_line):
            lines.append(indent_prefix + " | ".join(formatted_items[i : i + items_per_line]))
        return "\n".join(lines)


    def __str__(self):
        """
        Returns a human-readable string representation of the Pokemon object.
        """
        display_name = f"✨{self.name.capitalize()}✨" if self.is_shiny else self.name.capitalize()

        string = (
            f"Pokédex ID: {self.pokedex_id}\n"
            f"Name: {display_name}\n"
            f"Tier: {self.tier}\n"
            f"Types: {', '.join(t.capitalize() for t in self.types)}\n"
            f"Level: {self.level}\n"
            f"Exp Needed: {int(self.next_exp - self.exp)}\n"
            f"Nature: {self.nature}\n"
            f"IVs percentage: {self.calculate_total_iv_percentage()}%\n"
            f"Safe: {self.safe}"
        )
        return string
    
    def stats_str(self):
        """
        Returns a human-readable string representation of the Pokemon object.
        """
        display_name = f"✨{self.name.capitalize()}✨" if self.is_shiny else self.name.capitalize()

        # Format stats to two per line
        # Note: Special-attack and Special-defense should ideally be consistent keys in your dict (e.g., 'sp_atk', 'sp_def')
        # If they are currently 'Special-attack', 'Special-defense', the capitalize will work, but for consistency 'sp_atk' is common.
        formatted_stats = self._format_dict_to_lines(self.stats, items_per_line=1, key_formatter=str.capitalize)

        # Format IVs to two per line
        formatted_ivs = self._format_dict_to_lines(self.iv, items_per_line=1, key_formatter=str.capitalize)

        string = (
            f"Name: {display_name}\n"
            f"Nature: {self.nature}\n"
            f"Stats:\n{formatted_stats}\n"
            f"IVs:\n{formatted_ivs}\n\n"
            f"IVs percentage: {self.calculate_total_iv_percentage()}%\n"
        )
        return string

    def to_readable_dict(self) -> Dict[str, Any]:
        """
        Converts the Pokemon object into a dictionary, suitable for database storage
        or serialization (e.g., to JSON).
        Handles UUID and datetime objects by converting them to string representations.
        """
        return {
            "pokedex_id": self.pokedex_id,
            "name": self.name,
            "nickname": self.nickname,
            "is_shiny": self.is_shiny,
            "tier": self.tier,
            "types": self.types, # List of strings
            "ability": self.ability,
            "level": self.level,
            "region": self.region,
            "nature": self.nature,
            "stats": self.stats, # Dict
            "iv": self.iv, # Dict
        }
    
    def calculate_exp(self, level):
        exp = 0
        if self.growth_rate == "slow-then-very-fast":
            if level < 50:
                exp = (pow(level, 3) * (100 - level)) / 50
            elif 50 <= level < 68:
                exp = (pow(level, 3) * (150 - level)) / 100
            elif 68 <= level < 98:
                exp = (pow(level, 3) * ((1911 - 10 * level) / 3)) / 500
            else:
                exp = (pow(level, 3) * (160 - level)) / 100
        elif self.growth_rate == "slow":
            exp = (5 * pow(level, 3)) / 4
        elif self.growth_rate == "medium-slow":
            exp = (6 / 5 * pow(level, 3)) - (15 * pow(level, 2)) + 100 * level - 140
        elif self.growth_rate == "medium":
            exp = pow(level, 3)
        elif self.growth_rate == "fast":
            exp = (4 * pow(level, 3)) / 5
        elif self.growth_rate == "fast-then-very-slow":
            if level < 15:
                exp = (pow(level, 3) * ((level + 1) / 3) + 24) / 50
            elif 15 <= level < 68:
                exp = (pow(level, 3) * (level + 14)) / 50
            else:
                exp = (pow(level, 3) * ((level / 2) + 32)) / 50

        return int(math.floor(exp))
    
    def level_up(self):
        num_levels = 0
        exp_required_for_current_level = self.next_exp # Store current level's XP requirement
        while self.exp >= exp_required_for_current_level and self.level < 100:
            self.exp -= exp_required_for_current_level # <-- This is the crucial line to add
            num_levels += 1
            self.level += 1
            # Calculate next_exp for the *new* level
            self.next_exp = self.calculate_exp(self.level + 1) 
            # Update exp_required_for_current_level for the *next* iteration of the loop
            exp_required_for_current_level = self.next_exp 

        self.stats = self.calculate_stats() 

        return num_levels

    def calculate_total_iv_percentage(self):
        """
        Calculates the total Individual Values (IVs) as a percentage.

        Args:
            iv_data (dict): A dictionary containing IVs for 'hp', 'attack', 'defense',
                            'special_attack', 'special_defense', and 'speed'.
                            Each IV should be an integer between 0 and 31 (inclusive).

        Returns:
            float: The total IVs as a percentage, rounded to two decimal places.
                Returns 0.0 if iv_data is empty or invalid.
        """
        max_iv_per_stat = 31
        number_of_stats = len(self.iv)

        total_possible_ivs = max_iv_per_stat * number_of_stats
        current_total_ivs = sum(self.iv.values())

        if total_possible_ivs == 0:  # Avoid division by zero if for some reason number_of_stats is 0
            return 0.0

        percentage = (current_total_ivs / total_possible_ivs) * 100
        return round(percentage, 2)