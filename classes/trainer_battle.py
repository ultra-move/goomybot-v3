import random
from typing import List
import uuid
from classes.move_master import MoveMaster
from classes.pokemon import Pokemon
from classes.sprites import Sprites
from classes.types import Types
from classes.user import User
from classes.generator import Generator

class TrainerBattle:

    def __init__(self, id=uuid.uuid4()): 
        self.id = id

    def randomize_conditions(self, tier):
        conditions_pool = []

        if tier == 1:
            conditions_pool = ["type"]
        elif tier == 2:
            conditions_pool = ["type", "physical", "special", "status"]
        elif tier == 3:
            conditions_pool = ["type", "damage", "physical", "special", "status", "raise_stat", "lower_stat", "specific_move"]
        elif tier == 4:
            conditions_pool = ["type", "damage", "physical", "special", "status", "raise_stat", "lower_stat", "specific_move", "pp", "high_priority", "low_priority"]
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
            elif con == "pp":
                condition_dict[con] = random.choice([5, 10, 15, 20])
            elif con == "high_priority":
                condition_dict[con] = True
            elif con == "low_priority":
                condition_dict[con] = True
            # Add more conditions as needed

        print(f"Tier {tier} conditions generated (picking {num_to_pick} unique): {condition_dict}")
        return condition_dict
    
