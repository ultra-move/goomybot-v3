from asyncio.log import logger
from datetime import datetime, timezone, timedelta
import json
import random
from typing import Any, Dict, Optional
import uuid

from classes.id import Id


class Quest:

    def __init__(self, id: uuid, user_id, name='default', status='active', start_time=None, end_time=None, reward={}, condition={}):
        self.id = id
        self.user_id = user_id
        self.reward = reward
        self.condition = condition
        self.start_time = start_time if start_time is not None else datetime.now(timezone.utc)
        self.end_time = end_time if end_time is not None else datetime.now(timezone.utc) + timedelta(days=1)
        self.name = name
        self.status = status

    def random_reward(self):
        items = {
            'rerollnature': 2000,
            'rerolliv': 2000,
            'rarecandy': 3000,
            'resetseed': 5000,
            'raidpass': 5000,
            'skipframe': 10000,
            'skipraidframe': 50000
        }
        tier = self.condition['tier']
        item_name = 'Nothing'
        quantity = 0
        money = 0
        if tier == 4:
            reward_type = 'both'
        else:
            reward_type = random.choice(['item', 'money', 'both'])
        if reward_type == 'item' or reward_type == 'both':
            item_name = random.choice(list(items.keys()))
            
            if item_name == 'skipraidframe':
                quantity = 1
            elif item_name == 'skipframe':
                quantity = random.randrange(1,3)
            else:
                quantity = random.randrange(5,10)
            
        if reward_type == 'money' or reward_type == 'both':
            money = random.randrange(5000, 15000)
            money = round(money / 100) * 100
        #{item: {name: "", quantity: ""}, money: 0}
        self.reward = {'item': {'name': item_name, 'quantity': quantity*tier}, 'money': money*tier}

    def random_condition(self):
        pokedex_id = random.randrange(1, 1026)
        quantity = 1
        id = Id()
        tier = id.lookup_tier(pokedex_id=pokedex_id)
        self.condition = {'pokedex_id': pokedex_id, 'tier': tier, "quantity": quantity}

    def region_condition(self, user):
        id = Id()
        tier = random.randrange(1, 5)
        pokedex_id = random.choice(id.get_tier_region_pool(tier, user.region))
        quantity = 1   
        self.condition = {'pokedex_id': pokedex_id, 'tier': tier, "quantity": quantity}
        
    def __str__(self):
        reward_string = ""
        if self.reward['item']['name'] != 'Nothing':
            reward_string = reward_string + f"{self.reward['item']['name']} x{self.reward['item']['quantity']}\n"
        if self.reward['money'] != 0:
            reward_string =  reward_string + f"${self.reward['money']:,.0f}"
        return (
            f"Rewards:\n{reward_string}"
        )
    
    def get_time_remaining(self):
        now = datetime.now(timezone.utc)
        time_left = self.end_time - now
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        seconds = time_left.seconds % 60
        return f"{hours} hours, {minutes} minutes, {seconds} seconds."
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Quest instance from a dictionary (e.g., typically from a database row or cache).
        Handles potential UUID, datetime, and float conversions.
        """
        processed_data = data.copy()

        # Convert 'id' from string if necessary (e.g., if coming from Redis HGETALL as string)
        if 'user_id' in processed_data and isinstance(processed_data['user_id'], str):
            try:
                processed_data['user_id'] = int(processed_data['user_id'])
            except ValueError:
                logger.warning(f"Quest.from_dict: Could not convert user ID '{processed_data['id']}' to int. Keeping as is.")
                # Decide if you want to keep as str or raise error, for now we keep it
                pass 
        # UUID Handling (as previously defined, it's robust)
        if 'id' in processed_data and processed_data['id']:
            if isinstance(processed_data['id'], str):
                try:
                    processed_data['id'] = uuid.UUID(processed_data['id'])
                except ValueError:
                    logger.warning(f"Quest.from_dict: Invalid UUID string for id: '{processed_data['id']}'. Setting to None.")
                    processed_data['id'] = None
            elif not isinstance(processed_data['id'], uuid.UUID):
                logger.debug(f"Quest.from_dict: id is not a string or UUID: {processed_data['id']}. Setting to None.")
                processed_data['id'] = None
        else:
            processed_data['id'] = None

        # Datetime Handling (as previously defined, it's robust)
        for key in ['start_time', 'end_time']:
            if key in processed_data and processed_data[key] is not None: # Check for None explicitly
                if isinstance(processed_data[key], str):
                    try:
                        dt_obj = datetime.fromisoformat(processed_data[key])
                        processed_data[key] = dt_obj if dt_obj.tzinfo is not None else dt_obj.replace(tzinfo=datetime.timezone.utc)
                    except ValueError:
                        logger.warning(f"Quest.from_dict: Invalid datetime string for {key}: '{processed_data[key]}'. Setting to current UTC time.")
                        processed_data[key] = datetime.now(datetime.timezone.utc)
                elif isinstance(processed_data[key], datetime) and processed_data[key].tzinfo is None:
                    processed_data[key] = processed_data[key].replace(tzinfo=datetime.timezone.utc)
            else:
                # If key is missing or None, set to current UTC time as a default for creation
                processed_data[key] = datetime.now(datetime.timezone.utc)
        # --- JSONB (Dictionary) Handling (ev, iv) ---
        jsonb_keys = ['reward', 'condition']
        for key in jsonb_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = json.loads(processed_data[key])
                    except json.JSONDecodeError:
                        logger.warning(f"Quest.from_dict: Could not parse JSON string for '{key}'. Defaulting to empty dict.")
                        processed_data[key] = {}
                elif not isinstance(processed_data[key], dict):
                    logger.warning(f"Quest.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Defaulting to empty dict.")
                    processed_data[key] = {}
            else:
                processed_data[key] = {} # Default to empty dict if missing or None
        return cls(**processed_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the User instance to a dictionary, suitable for database insertion
        or cache storage. Handles UUID and datetime conversions for storage.
        """
        data = self.__dict__.copy()
        
        # Convert UUID object to string for storage
        if data.get('id'):
            data['id'] = str(data['id'])
        
        # Convert datetime objects to ISO format strings for storage
        for key in ['start_time', 'end_time']:
            if isinstance(data.get(key), datetime):
                data[key] = data[key].isoformat()

        for key in ['reward', 'condition']:
            if isinstance(data.get(key), dict):
                data[key] = json.dumps(data[key])
        
        return data