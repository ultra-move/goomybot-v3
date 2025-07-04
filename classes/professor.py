from asyncio.log import logger
from datetime import datetime, timezone, timedelta
import json
import math
import random
from typing import Any, Dict
import uuid

pokemon_types = ["Normal","Fire","Water","Grass","Flying","Fighting","Poison","Electric","Ground","Rock","Psychic","Ice","Bug","Ghost","Steel","Dragon","Dark","Fairy"]
natures = ["Hardy","Docile","Serious","Bashful","Quirky" ,"Lonely","Brave","Adamant","Naughty" ,"Bold","Relaxed","Impish","Lax" ,"Modest","Mild","Quiet","Rash" ,"Calm","Gentle","Sassy","Careful" ,"Timid","Hasty","Jolly","Naive"]
stats = ["hp", "attack", "defense", "special_attack", "special_defense", "speed"]
class Professor():

    def __init__(self, id=None, tier=None, conditions=None, reward=None, local_id=None, completed_by=None, completed_time=None):
        self.id = id
        self.tier = tier 
        self.conditions = conditions
        self.reward = reward
        self.local_id = local_id
        self.completed_by = completed_by
        self.completed_time = completed_time

    def start(self):
        self.id = uuid.uuid4()
        self.tier = random.randrange(1,5)
        self.local_id = random.randrange(1,1000)
        self.completed_by = 0
        self.random_conditions()
        self.random_rewards()

    def random_conditions(self):
        tier_condition = random.randrange(1,5)
        type_condition =  random.choice(pokemon_types)
        level_condition = random.randrange(1,101)
        nature_condition = random.choice(natures)
        iv_condition = random.randrange(35, 71)
        shiny_condition = True
        self.conditions = {"tier_condition": tier_condition, "type_condition": type_condition,"level_condition": level_condition, "nature_condition": nature_condition, "iv_condition": iv_condition, "shiny_condition": shiny_condition }
        
    def random_rewards(self):
        tier = self.tier
        items = {
            'rerollnature': 1000,
            'rerolliv': 2000,
            'rarecandy': 3000,
            'resetseed': 5000,
            'raidpass': 5000,
            'skipframe': 10000,
            'skipraidframe': 50000,
            'regionpass': 100000
        }
        item_name = 'Nothing'
        quantity = 0
        money = 0
        if tier == 4:
            reward_type = 'both'
        else:
            reward_type = random.choice(['item', 'money', 'both'])
        if reward_type == 'item' or reward_type == 'both':
            item_name = random.choice(list(items.keys()))
            if item_name == 'skipraidframe' or item_name == 'regionpass':
                quantity = 1
            elif item_name == 'skipframe':
                quantity = random.randrange(1,3)
            else:
                quantity = random.randrange(5,10)
            
        if reward_type == 'money' or reward_type == 'both':
            money = random.randrange(10000, 25000)
            money = round(money / 100) * 100
        self.tier = tier
        self.reward = {'item': {'name': item_name, 'quantity': quantity*tier}, 'money': money*tier}

    def check_condition(self, pokemon):
        tier = self.tier
        if tier == 4:
            condition_keys = ["tier_condition", "type_condition", "nature_condition", "iv_condition"]
            bonus_condition_keys = ["shiny_condition"]
        if tier == 3:
            condition_keys = ["tier_condition", "type_condition", "nature_condition" ]
            bonus_condition_keys = ["shiny_condition", "iv_condition"]
        if tier == 2:
            condition_keys = ["tier_condition", "type_condition"]
            bonus_condition_keys = ["shiny_condition", "iv_condition", "nature_condition", "level_condition"]
        if tier == 1:
            condition_keys = ["type_condition"]
            bonus_condition_keys = ["shiny_condition", "iv_condition", "nature_condition", "level_condition"]        

        conditions_met = []
        conditions_failed = []
        if "tier_condition" in condition_keys or "tier_condition" in bonus_condition_keys:
            if pokemon.tier == self.conditions['tier_condition']:
                conditions_met.append("tier_condition")
            else:
                conditions_failed.append("tier_condition") 
        if "type_condition" in condition_keys or "type_condition" in bonus_condition_keys:
            
            if self.conditions['type_condition'].lower() in pokemon.types:
                conditions_met.append("type_condition")
            else:
                conditions_failed.append("type_condition") 
        if "nature_condition" in condition_keys or "nature_condition" in bonus_condition_keys:
            if pokemon.nature == self.conditions['nature_condition']:
                conditions_met.append("nature_condition")
            else:
                conditions_failed.append("nature_condition") 
        if "iv_condition" in condition_keys or "iv_condition" in bonus_condition_keys:
            if pokemon.calculate_total_iv_percentage() >= self.conditions['iv_condition']:
                conditions_met.append("iv_condition")
            else:
                conditions_failed.append("iv_condition") 
        if "level_condition" in condition_keys or "level_condition" in bonus_condition_keys:
            if pokemon.level >= self.conditions['level_condition']:
                conditions_met.append("level_condition")
            else:
                conditions_failed.append("level_condition")
        if "shiny_condition" in condition_keys or "shiny_condition" in bonus_condition_keys:
            if pokemon.is_shiny:
                conditions_met.append("shiny_condition")
            else:
                conditions_failed.append("shiny_condition")
        requirements_met = True
        fail_display = "Failed Conditions:\n"
        bonus_met = False
        for required in condition_keys:
            if not required in conditions_met:
                requirements_met = False
                fail_display = fail_display + f"{required.split('_')[0].capitalize()}\n"
        for bonus in bonus_condition_keys:
            if bonus in conditions_met:
                bonus_met = True
        return requirements_met, bonus_met, fail_display
        

    def get_condition_string(self):
        tier = self.tier
        if tier == 4:
            condition_keys = ["tier_condition", "type_condition", "nature_condition", "iv_condition"]
            bonus_condition_keys = ["shiny_condition"]
        if tier == 3:
            condition_keys = ["tier_condition", "type_condition", "nature_condition" ]
            bonus_condition_keys = ["shiny_condition", "iv_condition"]
        if tier == 2:
            condition_keys = ["tier_condition", "type_condition"]
            bonus_condition_keys = ["shiny_condition", "iv_condition", "nature_condition", "level_condition"]
        if tier == 1:
            condition_keys = ["type_condition"]
            bonus_condition_keys = ["shiny_condition", "iv_condition", "nature_condition", "level_condition"]

        result = "__**Conditions**__:\n"

        if "tier_condition" in condition_keys:
             result = result + f"**Tier**: {self.conditions["tier_condition"]}\n"
        if "type_condition" in condition_keys:
            result = result + f"**Type**: {self.conditions["type_condition"]}\n"
        if "nature_condition" in condition_keys:
            result = result + f"**Nature**: {self.conditions["nature_condition"]}\n"
        if "iv_condition" in condition_keys:
            result = result + f"**IV Percentage**: {self.conditions["iv_condition"]}\n"
        if "level_condition" in condition_keys:
            result = result + f"**Level**: {self.conditions["level_condition"]}\n"  
        if "shiny_condition" in condition_keys:
            result = result + f"**Shiny**: {self.conditions["shiny_condition"]}\n" 

        result = result + "\n__**Bonus Conditions**__:\n"

        if "tier_condition" in bonus_condition_keys:
             result = result + f"**Tier**: {self.conditions["tier_condition"]}\n"
        if "type_condition" in bonus_condition_keys:
            result = result + f"**Type**: {self.conditions["type_condition"]}\n"
        if "nature_condition" in bonus_condition_keys:
            result = result + f"**Nature**: {self.conditions["nature_condition"]}\n"
        if "iv_condition" in bonus_condition_keys:
            result = result + f"**IV Percentage**: {self.conditions["iv_condition"]}\n"
        if "level_condition" in bonus_condition_keys:
            result = result + f"**Level**: {self.conditions["level_condition"]}\n"  
        if "shiny_condition" in bonus_condition_keys:
            result = result + f"**Shiny**: {self.conditions["shiny_condition"]}\n"

        reward_string = ""
        if self.reward['item']['name'] != 'Nothing':
            reward_string = reward_string + f"{self.reward['item']['name']} x{self.reward['item']['quantity']}\n"
        if self.reward['money'] != 0:
            reward_string =  reward_string + f"${self.reward['money']:,.0f}"
        
        result= result + f"\nRewards:\n{reward_string}"
        

        return result
     
    def get_reward_string(self, bonus_met, reduced_rewards):
        reward_string = ""
        if self.reward['item']['name'] != 'Nothing':
            if reduced_rewards:
                reward_string = reward_string + f"{self.reward['item']['name']} x{math.ceil(self.reward['item']['quantity']/10)}\n"
            elif bonus_met:
                reward_string = reward_string + f"{self.reward['item']['name']} x{self.reward['item']['quantity']*2}\n"
            else:
                reward_string = reward_string + f"{self.reward['item']['name']} x{self.reward['item']['quantity']}\n"
        if self.reward['money'] != 0:
            if reduced_rewards:
                reward_string = reward_string + f"${math.ceil(self.reward['money']/10):,.0f}\n"
            elif bonus_met:
                reward_string =  reward_string + f"${self.reward['money']*2:,.0f}"
            else:
                reward_string =  reward_string + f"${self.reward['money']:,.0f}"
        if reduced_rewards:
            return f"Reduced Rewards:\n{reward_string}"
        elif bonus_met:
            return f"Bonus Rewards:\n{reward_string}"
        else:
            return f"Rewards:\n{reward_string}"
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Quest instance from a dictionary (e.g., typically from a database row or cache).
        Handles potential UUID, datetime, and float conversions.
        """
        processed_data = data.copy()

        # Convert 'id' from string if necessary (e.g., if coming from Redis HGETALL as string)
        if 'completed_by' in processed_data and isinstance(processed_data['completed_by'], str):
            try:
                processed_data['completed_by'] = int(processed_data['completed_by'])
            except ValueError:
                logger.warning(f"Professor.from_dict: Could not convert completed_by '{processed_data['completed_by']}' to int. Keeping as is.")
                # Decide if you want to keep as str or raise error, for now we keep it
                pass 
        # UUID Handling (as previously defined, it's robust)
        if 'id' in processed_data and processed_data['id']:
            if isinstance(processed_data['id'], str):
                try:
                    processed_data['id'] = uuid.UUID(processed_data['id'])
                except ValueError:
                    logger.warning(f"Professor.from_dict: Invalid UUID string for id: '{processed_data['id']}'. Setting to None.")
                    processed_data['id'] = None
            elif not isinstance(processed_data['id'], uuid.UUID):
                logger.debug(f"Professor.from_dict: id is not a string or UUID: {processed_data['id']}. Setting to None.")
                processed_data['id'] = None
        else:
            processed_data['id'] = None

        # --- JSONB (Dictionary) Handling (ev, iv) ---
        jsonb_keys = ['reward', 'conditions']
        for key in jsonb_keys:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        processed_data[key] = json.loads(processed_data[key])
                    except json.JSONDecodeError:
                        logger.warning(f"Professor.from_dict: Could not parse JSON string for '{key}'. Defaulting to empty dict.")
                        processed_data[key] = {}
                elif not isinstance(processed_data[key], dict):
                    logger.warning(f"Professor.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Defaulting to empty dict.")
                    processed_data[key] = {}
            else:
                processed_data[key] = {} # Default to empty dict if missing or None

        # Datetime Handling (as previously defined, it's robust)
        for key in ['completed_time']:
            if key in processed_data and processed_data[key] is not None: # Check for None explicitly
                if isinstance(processed_data[key], str):
                    try:
                        dt_obj = datetime.fromisoformat(processed_data[key])
                        processed_data[key] = dt_obj if dt_obj.tzinfo is not None else dt_obj.replace(tzinfo=timezone.utc)
                    except ValueError:
                        logger.warning(f"Quest.from_dict: Invalid datetime string for {key}: '{processed_data[key]}'. Setting to current UTC time.")
                        processed_data[key] = datetime.now(timezone.utc)
                elif isinstance(processed_data[key], datetime) and processed_data[key].tzinfo is None:
                    processed_data[key] = processed_data[key].replace(tzinfo=timezone.utc)
            else:
                # If key is missing or None, set to current UTC time as a default for creation
                processed_data[key] = datetime.now(timezone.utc)
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

        for key in ['completed_time']:
            if isinstance(data.get(key), datetime):
                data[key] = data[key].isoformat()

        for key in ['reward', 'conditions']:
            if isinstance(data.get(key), dict):
                data[key] = json.dumps(data[key])
        
        return data