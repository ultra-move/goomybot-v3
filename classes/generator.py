import math
import random
import os
from classes.odds import Odds
from classes.id import Id
class Generator:
    def __init__(self, tier_seed: float, type_seed: float, pokemon_seed: float, shiny_seed: float, item_seed: float):
        self.odds = Odds()
        
        # Store the original integer seeds derived from the float seeds
        # This is crucial for deterministic re-seeding per frame.
        # Multiply by a large number to ensure diverse integer seeds from floats.
        self.original_tier_int_seed = int(tier_seed * 1_000_000_000)
        self.original_type_int_seed = int(type_seed * 1_000_000_000)
        self.original_pokemon_int_seed = int(pokemon_seed * 1_000_000_000)
        self.original_shiny_int_seed = int(shiny_seed * 1_000_000_000)
        self.original_item_int_seed = int(item_seed * 1_000_000_000)

        # Initialize RNGs with their original seeds (though they will be re-seeded per frame)
        self.tier_rng = random.Random(self.original_tier_int_seed)
        self.type_rng = random.Random(self.original_type_int_seed)
        self.pokemon_rng = random.Random(self.original_pokemon_int_seed)
        self.shiny_rng = random.Random(self.original_shiny_int_seed)
        self.item_rng = random.Random(self.original_item_int_seed)
        id = Id()
        self.tier_1_ids = id.tier_1_ids
        self.tier_2_ids = id.tier_2_ids
        self.tier_3_ids = id.tier_3_ids
        self.tier_4_ids = id.tier_4_ids

        self.event_ids = id.event_ids

        self.raid_tier_1_ids = id.raid_tier_1_ids
        self.raid_tier_2_ids = id.raid_tier_2_ids
        self.raid_tier_3_ids = id.raid_tier_3_ids
        self.raid_tier_4_ids = id.raid_tier_4_ids



    def get_outcome_for_frame(self, frame: int, user):
        # === Reseed RNGs deterministically per frame ===
        self.tier_rng.seed(self.original_tier_int_seed + frame)
        self.shiny_rng.seed(self.original_shiny_int_seed + frame)
        self.pokemon_rng.seed(self.original_pokemon_int_seed + frame)
        self.type_rng.seed(self.original_type_int_seed + frame)
        self.item_rng.seed(self.original_item_int_seed + frame)

        # === 1) Determine Tier ===
        tier_roll = self.tier_rng.random()
        tier_sum = self.odds.tier1_rate + self.odds.tier2_rate + self.odds.tier3_rate + self.odds.tier4_rate

        t1 = self.odds.tier1_rate / tier_sum
        t2 = (self.odds.tier1_rate + self.odds.tier2_rate) / tier_sum
        t3 = (self.odds.tier1_rate + self.odds.tier2_rate + self.odds.tier3_rate) / tier_sum

        if tier_roll < t1:
            chosen_tier = 1
            pool_size = self.odds.tier1_pool_size
            tier_pool = self.tier_1_ids
        elif tier_roll < t2:
            chosen_tier = 2
            pool_size = self.odds.tier2_pool_size
            tier_pool = self.tier_2_ids
        elif tier_roll < t3:
            chosen_tier = 3
            pool_size = self.odds.tier3_pool_size
            tier_pool = self.tier_3_ids
        else:
            chosen_tier = 4
            pool_size = self.odds.tier4_pool_size
            tier_pool = self.tier_4_ids

        # === 2) Pick Pokémon using fixed pool size ===
        pokemon_index_roll = self.pokemon_rng.random()
        pokemon_index = math.floor(pokemon_index_roll * pool_size)
        pokemon_index = max(0, min(pokemon_index, pool_size - 1))
        # Map index to actual list with modulus to avoid index errors if list is smaller than pool_size
        pokemon_id = tier_pool[pokemon_index % len(tier_pool)]

        # === 3) Determine Shininess ===
        shiny_rate = self.odds.shiny_rate
        shiny_roll = self.shiny_rng.random()
        is_shiny = (shiny_roll < shiny_rate)

        event = False
        # === 4) Attempt event override if NOT shiny ===
        if not is_shiny and user.event  and chosen_tier != 4:
            if  self.item_rng.random() < self.odds.event_rate:
                event = True
                shiny_rate = self.odds.event_shiny_rate
                is_shiny = (shiny_roll < shiny_rate)
                pokemon_id = self.tier_rng.choice(self.event_ids)

        # === 5) Pack result ===
        result = {
            "frame": frame,
            "tier": chosen_tier,
            "is_shiny": is_shiny,
            "pokemon_index_in_tier": pokemon_index,
            "tier_pool_size": pool_size,
            "pokemon_id": pokemon_id,
            "event": event
        }
        return result

    
    def find_shiny_frame(self, user, start_frame: int = 0, max_frames_to_check: int = 100000):
        """
        Searches for a frame number that would result in a shiny Pokémon.
        This iterates through frames and checks the shiny outcome for each.

        Args:
            user: The user object, containing 'event' status.
            start_frame (int): The frame number to start searching from.
            max_frames_to_check (int): The maximum number of frames to check.

        Returns:
            int or None: The first frame number found that yields a shiny Pokémon,
                        or None if no such frame is found within the specified range.
        """
        #print(f"Searching for a non-event shiny frame between {start_frame} and {start_frame + max_frames_to_check - 1}...")
        for frame in range(start_frame, start_frame + max_frames_to_check):
           result = self.get_outcome_for_frame(frame = frame, user = user)
           if result['event']: 
               continue
           elif result['is_shiny']:
               print(result)
               return frame                
        return None

    def find_event_shiny_frame(self, user, start_frame: int = 0, max_frames_to_check: int = 100000):
        """
        Searches for a frame number that would result in a shiny Pokémon.
        This iterates through frames and checks the shiny outcome for each.

        Args:
            user: The user object, containing 'event' status.
            start_frame (int): The frame number to start searching from.
            max_frames_to_check (int): The maximum number of frames to check.

        Returns:
            int or None: The first frame number found that yields a shiny Pokémon,
                        or None if no such frame is found within the specified range.
        """
        #print(f"Searching for a non-event shiny frame between {start_frame} and {start_frame + max_frames_to_check - 1}...")
        for frame in range(start_frame, start_frame + max_frames_to_check):
           result = self.get_outcome_for_frame(frame = frame, user = user)
           if result['event'] and result['is_shiny']:
               print(result)
               return frame        
        return None
    
    def get_outcome_for_raid_frame(self, frame: int):
        # The key to determinism per frame:
        # Re-seed each RNG for *every frame* using a combination of its original, immutable seed
        # and the current frame number. This ensures that the sequence of "random"
        # numbers generated for a specific type of roll (e.g., tier) at a specific frame
        # is always the same, regardless of previous calls to this method or different Python runs.

        # We combine the original integer seed with the frame number using a simple sum.
        # This is deterministic across all Python runs and for all frame numbers.
        tier_frame_seed = self.original_tier_int_seed + int(frame)
        self.tier_rng.seed(tier_frame_seed)

        shiny_frame_seed = self.original_shiny_int_seed + int(frame)
        self.shiny_rng.seed(shiny_frame_seed)

        pokemon_frame_seed = self.original_pokemon_int_seed + int(frame)
        self.pokemon_rng.seed(pokemon_frame_seed)
        
        # Also re-seed type_rng and item_rng, even if not used in this specific outcome calculation
        type_frame_seed = self.original_type_int_seed + int(frame)
        self.type_rng.seed(type_frame_seed)

        item_frame_seed = self.original_item_int_seed + int(frame)
        self.item_rng.seed(item_frame_seed)


        # 1. Determine Tier
        tier_roll = self.tier_rng.random() # Uses the re-seeded RNG
        tier_sum_of_rates = self.odds.raid_tier1_rate + self.odds.raid_tier2_rate + self.odds.raid_tier3_rate + self.odds.raid_tier4_rate
        
        normalized_tier1_cutoff = self.odds.raid_tier1_rate / tier_sum_of_rates
        normalized_tier2_cutoff = (self.odds.raid_tier1_rate + self.odds.raid_tier2_rate) / tier_sum_of_rates
        normalized_tier3_cutoff = (self.odds.raid_tier1_rate + self.odds.raid_tier2_rate + self.odds.raid_tier3_rate) / tier_sum_of_rates
        
        chosen_tier = None
        tier_pool_size = 0
        chosen_pokemon_index = 0 # Initialize to avoid UnboundLocalError
        pokemon_id = None # Initialize to avoid UnboundLocalError

        if tier_roll < normalized_tier1_cutoff:
            chosen_tier = 1
            tier_pool_size = self.odds.raid_tier1_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_1_ids[chosen_pokemon_index]
        elif tier_roll < normalized_tier2_cutoff:
            chosen_tier = 2
            tier_pool_size = self.odds.raid_tier2_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_2_ids[chosen_pokemon_index]
        elif tier_roll < normalized_tier3_cutoff:
            chosen_tier = 3
            tier_pool_size = self.odds.raid_tier3_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_3_ids[chosen_pokemon_index]
        else:
            chosen_tier = 4
            tier_pool_size = self.odds.raid_tier4_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_4_ids[chosen_pokemon_index]

        # 2. Determine Shininess
        shiny_roll = self.shiny_rng.random() # Uses the re-seeded RNG
        is_shiny = shiny_roll < self.odds.raid_shiny_rate
        
        result = {
            "frame": frame,
            "tier": chosen_tier,
            "is_shiny": is_shiny,
            "pokemon_index_in_tier": chosen_pokemon_index,
            "tier_pool_size": tier_pool_size,
            "pokemon_id": pokemon_id
        }
        print(result)
        return result
    
    def find_shiny_raid_frame(self, start_frame: int = 0, max_frames_to_check: int = 100000):
        """
        Searches for a frame number that would result in a shiny Pokémon.
        This iterates through frames and checks the shiny outcome for each.

        Args:
            start_frame (int): The frame number to start searching from.
            max_frames_to_check (int): The maximum number of frames to check.

        Returns:
            int or None: The first frame number found that yields a shiny Pokémon,
                         or None if no such frame is found within the specified range.
        """
        print(f"Searching for a shiny frame between {start_frame} and {start_frame + max_frames_to_check - 1}...")
        for frame in range(start_frame, start_frame + max_frames_to_check):
            # Re-seed the shiny RNG specifically for this frame check
            shiny_frame_seed = self.original_shiny_int_seed + int(frame)
            self.shiny_rng.seed(shiny_frame_seed)
            
            shiny_roll = self.shiny_rng.random()
            if shiny_roll < self.odds.raid_shiny_rate:
                print(f"Found shiny frame: {frame} (Shiny roll: {shiny_roll:.4f} < Shiny rate: {self.odds.raid_shiny_rate})")
                return frame
        print(f"No shiny frame found within {max_frames_to_check} frames starting from {start_frame}.")
        return None