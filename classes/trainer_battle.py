from datetime import datetime, timezone
import json
import random
from typing import List
import uuid
from classes.move import Move
from classes.move_master import MoveMaster
from classes.types import Types

class TrainerBattle:

    def __init__(self, id=uuid.uuid4(), conditions = None, tier=0, start_time=datetime.now(timezone.utc), bonus_duration = 0, pokemon_id=None, user_id=None, moves_used=[], conditions_met=[], trainer_sprite=""): 
        self.id = id
        self.tier = tier
        if conditions:
            self.conditions = conditions
        else:
            self.conditions = self.randomize_conditions()
        self.start_time = start_time
        self.bonus_duration = self.set_bonus_duration()
        self.pokemon_id = pokemon_id
        self.user_id = user_id
        self.moves_used = []
        self.conditions_met = conditions_met
        self.trainer_sprite = trainer_sprite

    def randomize_conditions(self):
        conditions_pool = []
        tier = self.tier
        if tier == 1:
            conditions_pool = ["type"]
        elif tier == 2:
            conditions_pool = ["type", "physical", "special", "status"]
        elif tier == 3:
            conditions_pool = ["type", "damage", "physical", "special", "status", "raise_stat", "lower_stat", "specific_move", "accuracy"]
        elif tier == 4:
            conditions_pool = ["type", "damage", "physical", "special", "status", "raise_stat", "lower_stat", "specific_move", "accuracy", "pp", "high_priority", "low_priority"]
        else:
            print(f"Warning: Invalid tier '{tier}' provided. Returning empty conditions.")
            return {} # Return an empty dictionary if tier is invalid

        # Determine how many conditions to pick: Exactly 'tier' unique choices.
        # Ensure 'tier' is not greater than the available conditions to avoid errors.
        if tier > len(conditions_pool):
            print(f"Error: Cannot pick {tier} unique conditions for tier {tier} as only {len(conditions_pool)} are available.")
            # You might want to handle this differently, e.g., pick all available, or raise an error.
            # For now, we'll pick all available if tier is too high for the pool.
            num_to_pick = len(conditions_pool)
        else:
            num_to_pick = tier

        # Use random.sample to pick unique conditions
        final_selected_conditions = random.sample(conditions_pool, num_to_pick)

        # Build conditions dict
        condition_dict = {}
        for con in final_selected_conditions:
            if con == "type":
                condition_dict[con] = Types.random_type()
            elif con == "physical":
                condition_dict[con] = True
            elif con == "special":
                condition_dict[con] = True
            elif con == "damage":
                condition_dict[con] = random.choice([0, 60, 70, 80, 90, 100, 120])
            elif con == "status":
                condition_dict[con] = True
            elif con == "raise_stat":
                condition_dict[con] = True
            elif con == "lower_stat":
                condition_dict[con] = True
            elif con == "specific_move":
                condition_dict[con] = MoveMaster.random_move().capitalize()
            elif con == "accuracy":
                condition_dict[con] = random.choice([90, 100, 85])
            elif con == "pp":
                condition_dict[con] = random.choice([5, 10, 15, 20])
            elif con == "high_priority":
                condition_dict[con] = True
            elif con == "low_priority":
                condition_dict[con] = True
            # Add more conditions as needed

        print(f"Tier {tier} conditions generated (picking {num_to_pick} unique): {condition_dict}")
        return condition_dict
    
    def set_bonus_duration(self):
        bonus_duration = 0
        if self.tier == 1:
            bonus_duration = 30
        if self.tier == 2:
            bonus_duration = 60
        if self.tier == 3:
            bonus_duration = 90
        if self.tier == 4:
            bonus_duration = 120
        return bonus_duration

    def check_condition(self, move: Move) -> bool:
        """
        Checks if the given move satisfies any of the battle's conditions
        and updates the list of met conditions.

        Args:
            move (Move): The move to check against the battle's conditions.

        Returns:
            bool: True if all required conditions are now met, False otherwise.
        """
        # Iterate over a copy of keys to avoid issues if conditions.keys() changes during iteration
        for con in list(self.conditions.keys()): 
            # Ensure the condition hasn't already been met
            if con in self.conditions_met:
                continue

            condition_met_for_this_move = False
            
            if con == "type":
                if self.conditions[con].lower() == move.type_name.lower():
                    condition_met_for_this_move = True
            elif con in ["physical", "special", "status"]:
                # Corrected logic: check if the move's damage_class matches the condition key itself
                if move.damage_class == con:
                    condition_met_for_this_move = True
            elif con == "damage":
                if self.conditions[con] == move.power:
                    condition_met_for_this_move = True
            elif con == "raise_stat":
                # Assuming stat_changes is a dictionary like {"stat": "attack", "value": 1}
                if move.stat_changes and move.stat_changes.get("value", 0) > 0:
                    condition_met_for_this_move = True
            elif con == "lower_stat":
                if move.stat_changes and move.stat_changes.get("value", 0) < 0:
                    condition_met_for_this_move = True
            elif con == "specific_move":
                if self.conditions[con] == move.name.capitalize():
                    condition_met_for_this_move = True
            elif con == "accuracy":
                if self.conditions[con] == move.accuracy:
                    condition_met_for_this_move = True
            elif con == "pp":
                if self.conditions[con] == move.pp:
                    condition_met_for_this_move = True
            elif con == "high_priority":
                if move.priority > 0:
                    condition_met_for_this_move = True
            elif con == "low_priority":
                if move.priority < 0:
                    condition_met_for_this_move = True
            
            if condition_met_for_this_move:
                self.conditions_met.append(con)

        # Check if all required conditions are now met
        # Use sets for efficient comparison of unique conditions
        required_conditions = set(self.conditions.keys())
        current_met_conditions = set(self.conditions_met)

        # Return True if all required conditions are a subset of the currently met conditions
        return required_conditions.issubset(current_met_conditions)

    def to_dict(self):
        """
        Converts the TrainerBattle object to a dictionary, suitable for database storage.
        Handles UUID, datetime objects, and serializes complex types (dict, list) to JSON strings.
        """
        data = {
            "id": str(self.id) if self.id else None,
            "tier": self.tier,
            # Serialize conditions dictionary to a JSON string
            "conditions": json.dumps(self.conditions) if self.conditions is not None else "{}",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "bonus_duration": self.bonus_duration,
            "pokemon_id": str(self.pokemon_id) if self.pokemon_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            # Serialize lists to JSON strings
            "moves_used": json.dumps(self.moves_used) if self.moves_used is not None else "[]",
            "conditions_met": json.dumps(self.conditions_met) if self.conditions_met is not None else "[]",
            "trainer_sprite": self.trainer_sprite
        }
        return data

    @classmethod
    def from_dict(cls, data):
        """
        Creates a TrainerBattle object from a dictionary, typically retrieved from a database.
        Handles UUID, datetime string parsing, and deserializes JSON strings back to complex types.
        """
        # Convert UUID strings back to uuid.UUID objects
        _id = uuid.UUID(data["id"]) if data.get("id") else None
        _pokemon_id = uuid.UUID(data["pokemon_id"]) if data.get("pokemon_id") else None
        _user_id = None
        if data.get("user_id") is not None:
            try:
                _user_id = int(data["user_id"])
            except (ValueError, TypeError):
                print(f"Warning: Could not convert user_id '{data['user_id']}' to int. Setting to None.")
                _user_id = None

        # Convert datetime string back to datetime object
        _start_time = None
        if data.get("start_time"):
            try:
                _start_time = datetime.fromisoformat(data["start_time"])
            except ValueError:
                # Fallback for slightly different date formats if necessary, though isoformat is preferred
                print(f"Warning: Could not parse start_time '{data['start_time']}' with fromisoformat. Attempting alternative.")
                try:
                    # Example: if timezone info is sometimes missing, adjust format string
                    _start_time = datetime.strptime(data["start_time"], "%Y-%m-%dT%H:%M:%S.%f")
                except ValueError:
                    print(f"Error: Failed to parse start_time '{data['start_time']}' with alternative format. Setting to None.")
                    _start_time = None
            except TypeError:
                # If start_time is already a datetime object (e.g., from direct assignment)
                _start_time = data["start_time"]


        # Deserialize conditions, moves_used, and conditions_met from JSON strings
        _conditions = {}
        if data.get("conditions"):
            try:
                _conditions = json.loads(data["conditions"])
            except (json.JSONDecodeError, TypeError):
                _conditions = data["conditions"]

        _moves_used = []
        if data.get("moves_used"):
            try:
                _moves_used = json.loads(data["moves_used"])
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not decode moves_used JSON: {data.get('moves_used')}. Setting to empty list.")
                _moves_used = []

        _conditions_met = []
        if data.get("conditions_met"):
            try:
                _conditions_met = json.loads(data["conditions_met"])
            except (json.JSONDecodeError, TypeError):
                _conditions_met = data["conditions_met"]

        # Create a new instance of TrainerBattle
        return cls(
            id=_id,
            tier=data["tier"],
            conditions=_conditions,
            start_time=_start_time,
            bonus_duration=data.get("bonus_duration", 0),
            pokemon_id=_pokemon_id,
            user_id=_user_id,
            moves_used=_moves_used,
            conditions_met=_conditions_met,
            trainer_sprite=data.get("trainer_sprite", ""),
        )