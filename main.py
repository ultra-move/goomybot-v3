import asyncio
import asyncio.log
from datetime import datetime, timezone, timedelta # <-- Add timezone here
import logging # Correct import for logging
# from asyncio.log import logger # This is generally not how you get a logger. Use logging.getLogger()
import random
import time
from typing import Any, Dict, List, Optional, Tuple

# Correct imports for redis-py
# from aioredis import RedisError # This is deprecated
from discord.abc import PrivateChannel
from redis.exceptions import RedisError # Import RedisError from the correct package
import discord

from classes.battle import Battle
from classes.data_loader import DataLoader
from classes.database_manager import DatabaseManager
from classes.embed_generator import EmbedGenerator
from classes.flex_log import FlexLog
from classes.item import Item
from classes.lottery import Lottery
from classes.pokemon_master import PokemonMaster
from classes.redis_manager import RedisManager
from classes.storage_manager import StorageManager
#from classes.data_loader import DataLoader
from classes.user import User
from classes.pokemon import Pokemon
from classes.generator import Generator
import uuid
import os
from dotenv import load_dotenv

load_dotenv() # This loads variables from .env into os.environ

# Configure logging for main.py (optional, but good practice)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get a logger instance for main.py

################################Global################################
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Make sure your .env has REDIS_URL set correctly, e.g.:
# REDIS_URL="redis://:your_password@localhost:6379/0"
# Remember to URL-encode special characters in your password!
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0") # Provide a default for local testing if not in .env
REDIS_PREFIX = os.getenv("REDIS_PREFIX")
FLEX_ID: str | None = os.getenv("FLEX_ID")
BUG_ID: str | None = os.getenv("BUG_ID")
LOTTERY_ID= os.getenv("LOTTERY_ID")
###################################################################

redis_manager = RedisManager(REDIS_URL)
database_manager = DatabaseManager(DATABASE_URL) 
storage_manager = StorageManager(redis_manager=redis_manager, database_manager=database_manager) 
#data_loader = DataLoader()
embed_generator = EmbedGenerator()

intents = discord.Intents.default()
intents.message_content = True

#######################General methods##########################
def get_help():
    help = """
**__General Commands__**
* `.help`: Displays this help message.
* `.help filter`: Displays the filter help message.
* `.register`: Registers you for the game. You'll need to do this before using most other commands!
* `.odds`: Displays the current odds
* `.bug <bug report>`: Submits a bug to the bug channel
* `.git`: provides a link to the git repository

**__User Commands__**
* `.profile`: Shows your user profile.
* `.profileimage <URL>`: Sets your profile image to the provided URL (must be from showdown sprites).
* `.list [page_number]`: Displays a list of your Pokémon. You can specify a page number to view more.
* `.view [local_id]`: If a `local_id` is provided, views details of that specific Pokémon. If no `local_id` is given, it shows details of your current buddy Pokémon.
* `.filter <filter_message>`: Filters your Pokémon list based on your criteria.
* `.buddy [local_id]`: If a `local_id` is provided, sets that Pokémon as your buddy. If no `local_id` is given, it shows your current buddy Pokémon.
* `.evolve [name]`: Evolves buddy pokemon to name, buddy will evolve to a random choice if multiple are available
* `.frame`: Views current frame
* `.lottery`: Enters the lottery, or if already entered, displays information about the lottery

**__Battle Commands__**
* `.spawn`: Initiates a new battle.
* `.run <local_id>`: Runs from a battle with the specified local ID.
* `.join <local_id>`: Joins an existing battle with the specified local ID.

**__Raid Commands__**
* `.raid`: Initiates a new raid (requires a raidpass).
* `.joinraid <local_id>`: Joins an existing raid with the specified local ID.

**__Item Commands__**
* `.shop`: Displays available items in the shop
* `.buy <item_name> <quantity>`: Buys the specified quantity of an item.
* `.items`: Shows a list of your owned items.
* `.resetseed`: Uses a Reset Seed to reset your frame and shiny seed.
* `.shinyframe`: Dispalys the frame that your next shiny is at
* `.fshinyframe`: Displays the pokemon at the shiny frame. Must use a normal shinyframe first.
* `.skipframe`: Uses a Skip Frame (100 frames or to shiny frame).
* `.rerolliv <iv_name>`: Rerolls selected buddy iv.
"""
    return embed_generator.create_help_embed(info=help)

def get_help_filter():
    help = """
**__Filter Commands__**
* `.filter`: Resets filter to default order.
* `.filter <filter_key> <value>`: Sets a filter. For example:
    * `.filter shiny true`: Shows only shiny Pokémon.
    * `.filter type fire`: Shows only Fire-type Pokémon.
    * `.filter type water,flying`: Shows Water or Flying-type Pokémon.
    * `.filter tier 3`: Shows only Tier 3 Pokémon.
    * `.filter level=50`: Shows only Level 50 Pokémon (note: can use `=` or a space).
    * `.filter name Pikachu`: Shows only Pokémon named Pikachu.
    * `.filter nature jolly`: Shows only Jolly-natured Pokémon.
    * `.filter region kanto`: Shows only Pokémon from the Kanto region.
    * `.filter held_item true`: Shows only Pokémon holding an item.
* `.filter order <order_key> <asc/desc>`: Sets the order for displaying Pokémon. For example:
    * `.filter order pokedex asc`: Orders Pokémon by Pokedex number in ascending order.
    * `.filter order tier desc`: Orders Pokémon by Tier in descending order.
    * `.filter order level asc`: Orders Pokémon by Level in ascending order.
* You can combine multiple filters and orders in one command:
    * `.filter shiny true tier 1 order level desc`
"""

    return embed_generator.create_help_embed(info=help)

def get_admin_help():
    admin_help = """
    ---
## **__Admin Commands__**
    * `.addframe <user_id> <amount>`: Adds a specified amount of frames to a user.
    * `.removeframe <user_id> <amount>`: Removes a specified amount of frames from a user.
    * `.flush`: Clears all entires in the cache.
    * `.raidframe`: Shows shiny frame for raid (beta).
    * `.resetodds`: Resets the odds for something (e.g., shiny encounters).
    * `.adminspawn <pokedex_id> <is_shiny>`: Spawns a Pokémon. `is_shiny` can be `true` or `false`.
    * `.addmoney <user_id> <amount>`: Adds a specified amount of money to a user.
    * `.removemoney <user_id> <amount>`: Removes a specified amount of money from a user.
"""
    return embed_generator.create_help_embed(admin_help)

async def register(user_id, name):
    user = User(id=user_id, discord_username=name, name=name)
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_register_embed(name)

async def get_odds(user):
    return embed_generator.create_odds_table(user)
#######################User methods##########################
async def list_pokemon(user, page, page_size):
   total_pages, pokemon = await storage_manager.list_pokemon(user=user, page=page)
   #build the users view table for easy access later
   user.view_table = {}
   for p,i in zip(pokemon, range(page_size)):
      user.view_table[i+1] = {'id': str(p.id), 'name': p.name}
   logger.debug(user.view_table)
   await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
   return embed_generator.create_user_view_table(user, page+1, total_pages) 

async def view_pokemon(user, local_id):
    pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(local_id)]['id'])
    logger.debug(pokemon)
    return embed_generator.create_pokemon_view(user, pokemon)

async def view_buddy(user):
    pokemon = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
    logger.debug(pokemon)
    return embed_generator.create_pokemon_view(user, pokemon)    

async def set_buddy(user, local_id):
    pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(local_id)]['id'])
    if pokemon:
        user.current_pokemon = pokemon.id
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_pokemon_view(user, pokemon)

def set_buddy_from_evolution(buddy, evolution):
    buddy.name = evolution.name
    buddy.ability = random.choice(evolution.abilities_names)
    buddy.base_stats = evolution.base_stats_json
    buddy.growth_rate = evolution.growth_rate_name
    buddy.pokedex_id = evolution.id
    if buddy.is_shiny:
        buddy.sprite_front = evolution.front_shiny_sprite
        buddy.sprite_back = evolution.back_shiny_sprite
    else:
        buddy.sprite_front = evolution.front_default_sprite
        buddy.sprite_back = evolution.back_default_sprite
    buddy.region = evolution.region
    buddy.calculate_exp(buddy.level)
    buddy.stats = buddy.calculate_stats()
    buddy.tier = evolution.tier
    return buddy                

async def evolve_buddy(user, name: Optional[str] = None):
    """
    Evolves the user's current buddy Pokémon.
    If a 'name' is provided, attempts to evolve to that specific Pokémon.
    If no 'name' is provided, picks a random evolution.
    """
    buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))

    if not buddy:
        return embed_generator.create_evolved_fail_embed(user.name, "Your buddy Pokémon could not be found.")

    # Assuming get_evolutions returns a list of PokemonMaster objects that buddy can evolve into
    evolutions: list[PokemonMaster] = await storage_manager.get_evolutions(buddy.pokedex_id)

    if not evolutions:
        return embed_generator.create_evolved_fail_embed(
                user.name,
                f"No evolutions for selected buddy"
            )

    chosen_evolution: Optional[PokemonMaster] = None

    if name:
        # User specified a desired evolution
        for evolution in evolutions:
            if evolution.name.lower() == name.lower(): # Case-insensitive match
                chosen_evolution = evolution
                break
        if not chosen_evolution:
            # Desired evolution not found in the list of possible evolutions
            return embed_generator.create_evolved_fail_embed(
                user.name,
                f"'{name}' is not a valid evolution for {buddy.name} or it's not available."
            )
    else:
        # No name specified, pick a random evolution
        chosen_evolution = random.choice(evolutions)

    # Proceed with evolution using the chosen_evolution
    if chosen_evolution:
        updated_buddy = set_buddy_from_evolution(buddy, chosen_evolution)
        if updated_buddy:
            await storage_manager.save_object(
                obj=updated_buddy,
                cache_key=f"{REDIS_PREFIX}pokemon_data:{updated_buddy.id}",
                table_name="user_pokemon",
                unique_columns=["id"]
            )
            return embed_generator.create_pokemon_view(user, updated_buddy)
        else:
            return embed_generator.create_evolved_fail_embed(user.name, "Failed to update buddy Pokémon details.")
    else:
        # This case should ideally not be reached if evolutions list is not empty
        # and chosen_evolution is guaranteed to be set either by name or randomly.
        return embed_generator.create_evolved_fail_embed(user.name, "An unexpected error occurred during evolution selection.")


async def filter_pokemon(user, filter_message):
   default_filter = {
            'shiny': False,
            'type': [],
            'name': '',
            'tier': 0,
            'level': 0,
            'nature': '',
            'region': '',
            'held_item': False #False means do not filter here, true means filter where held_item IS NOT NULL
   }
   default_order = {
            'pokedex': {'value': False, 'order': "ASC"},
            'tier': {'value': False, 'order': "ASC"},
            'level': {'value': False, 'order': "ASC"},
   }
   
   parsed_filter, parsed_order, final_status = parse_filter_command(message=filter_message, default_filter=default_filter, default_order=default_order )
   logger.debug(final_status)
   user.filter = parsed_filter
   user.order_by = parsed_order
   #list_pokemon performs the save of the user
   return await list_pokemon(user=user, page=0, page_size=10)

def parse_filter_command(message, default_filter, default_order):
    """
    Parses a user command string to extract filter and order criteria.

    Args:
        message (str): The user's command string (e.g., ".filter shiny true tier 1 order pokedex asc").
        default_filter (dict): The base filter dictionary to merge with.
        default_order (dict): The base order dictionary to merge with.

    Returns:
        Tuple[Dict, Dict, str]: A tuple containing:
            - The parsed filter dictionary.
            - The parsed order dictionary.
            - A status message indicating success or errors.
    """
    parsed_filter = default_filter.copy()
    parsed_order = {k: v.copy() for k, v in default_order.items()}  # Deep copy
    status_messages = []

    # Normalize message for parsing
    tokens = message.lower().strip().split()

    # Remove the initial command prefix if present (e.g., ".filter")
    if tokens and tokens[0] == ".filter":
        tokens = tokens[1:]  # Remove the command word itself

    if not tokens:
        return parsed_filter, parsed_order, "No filters or order specified."

    # Process tokens in a single pass to handle sections correctly
    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "order":
            # Switch to parsing order arguments for the rest of the tokens
            i += 1 # Move past "order" keyword
            while i < len(tokens):
                order_key = tokens[i]
                if i + 1 < len(tokens):
                    order_direction_str = tokens[i+1]
                    if order_key in parsed_order:
                        if order_direction_str in ['asc', 'desc']:
                            parsed_order[order_key]['value'] = True
                            parsed_order[order_key]['order'] = order_direction_str.upper()
                        else:
                            status_messages.append(f"Invalid order direction for '{order_key}': '{order_direction_str}'. Expected 'asc' or 'desc'.")
                    else:
                        status_messages.append(f"Warning: Unrecognized order parameter '{order_key}'. Skipping.")
                    i += 2 # Move past key and value
                else:
                    status_messages.append(f"Warning: Order parameter '{order_key}' provided without a direction (ASC/DESC). Skipping.")
                    i += 1 # Move past key
            break # Exit the main loop after processing order arguments

        # --- Parse Filter Arguments ---
        key = token
        value_str = None

        if '=' in key:
            # Handle key=value format
            parts = key.split('=', 1)
            key = parts[0]
            value_str = parts[1]
            i += 1 # Only advance by one token (the current token)
        elif i + 1 < len(tokens):
            # Handle key value format
            value_str = tokens[i+1]
            i += 2 # Advance by two tokens (key and value)
        else:
            status_messages.append(f"Warning: Filter parameter '{key}' provided without a value. Skipping.")
            i += 1 # Advance by one token (the current token)
            continue # Continue to the next token

        if key in parsed_filter:
            if key == 'type':
                # Special handling for 'type' to allow multiple types
                if 'type' not in parsed_filter or parsed_filter['type'] is None:
                    parsed_filter['type'] = [] # Initialize as a list if not already
                
                # Split by commas if present, and add each type
                for t in value_str.split(','):
                    t_clean = t.strip()
                    if t_clean: # Ensure it's not an empty string
                        parsed_filter['type'].append(t_clean)

            elif key in ['shiny', 'held_item']:
                if value_str in ['true', 'false']:
                    parsed_filter[key] = (value_str == 'true')
                else:
                    status_messages.append(f"Invalid value for '{key}': '{value_str}'. Expected 'true' or 'false'.")
            elif key in ['tier', 'level']:
                try:
                    num_val = int(value_str)
                    if num_val >= 0:
                        parsed_filter[key] = num_val
                    else:
                        status_messages.append(f"Invalid value for '{key}': '{value_str}'. Expected a non-negative integer.")
                except ValueError:
                    status_messages.append(f"Invalid value for '{key}': '{value_str}'. Expected an integer.")
            elif key in ['name', 'nature', 'region']:
                parsed_filter[key] = value_str
            else:
                status_messages.append(f"Warning: Unrecognized filter key '{key}'. Skipping.")
        else:
            status_messages.append(f"Warning: Unrecognized filter parameter '{key}'. Skipping.")

    final_status = "Successfully parsed command." if not status_messages else "\n".join(status_messages)

    return parsed_filter, parsed_order, final_status

async def set_profile_image(user, url):
    host_string = r'https://play.pokemonshowdown.com/sprites/'
    if url.startswith(host_string):
        user.profile_image = url
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_user_profile_image_success_embed(user)
    else:
        return embed_generator.create_user_profile_image_failed_embed(user, host_string)

#######################Admin methods##########################
async def add_frame(user_id, frames):
    user = await storage_manager.get_user(user_id=user_id)
    user.frame += frames
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed(f"Added {frames} frames for {user.name}")

async def remove_frame(user_id, frames):
    user = await storage_manager.get_user(user_id=user_id)
    user.frame -= frames
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed(f"Added {frames} frames for {user.name}")

async def flush_all():
    await redis_manager.flush_all()
    return embed_generator.create_admin_embed("flushed cache")

async def odds_reset():
    users = await storage_manager.get_all_users()
    for user in users:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_shiny_frame(start_frame=user.frame+1, max_frames_to_check=10000)
        user.shiny_frame = shiny_frame
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed("resetodds")

async def add_money(user_id, amount):
    user = await storage_manager.get_user(user_id=user_id)
    user.wallet += int(amount)
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed("addmoney")

async def remove_money(user_id, amount):
    user = await storage_manager.get_user(user_id=user_id)
    if int(amount) >= user.wallet:
        user.wallet = 0
    else:
        user.wallet -= int(amount)
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed("removemoney")

#######################Item methods#######################
async def get_shop(user):
    items = {
        'shinyframe': 1000,
        'resetseed': 5000,
        'rerolliv': 5000,
        'raidpass': 5000,
        'skipframe': 10000
    }
    return embed_generator.create_shop_view_table(user, items)

async def buy_item(user, item_name, quantity):
    items = {
        'shinyframe': 1000,
        'resetseed': 5000,
        'rerolliv': 5000,
        'raidpass': 5000,
        'skipframe': 10000
    }
    user_items = await storage_manager.get_user_items(user)
    final_item = {}
    price = items[item_name] * quantity
    if price <= user.wallet:
        found = False
        for item in user_items:
            if item.name == item_name:
                found = True
                final_item = item
                item.quantity += quantity
        if not found:
            final_item = Item(id=uuid.uuid4(), user_id=user.id, name=item_name, quantity=quantity)
        user.wallet -= price
        await storage_manager.save_object(obj=final_item, cache_key=f"{REDIS_PREFIX}item_id:{final_item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]) 
        return embed_generator.create_item_bought_embed(user, item_name, quantity) 
    else:
        return embed_generator.create_item_bought_failed_embed(user, item_name, quantity)
    
async def shiny_frame(user):
    if user.shiny_frame != -1:
       #print('Shiny frame not -1')
       return embed_generator.create_shiny_frame(user=user, shiny_frame=user.shiny_frame) 
    
    item = await storage_manager.get_user_item_by_name(user, 'shinyframe')
    if item.quantity >= 1:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_shiny_frame(start_frame=user.frame+1, max_frames_to_check=10000)
        if shiny_frame:
            outcome = gen.get_outcome_for_frame(shiny_frame)
            user.shiny_frame = shiny_frame
            item.quantity = item.quantity - 1
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
            await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])            
            return embed_generator.create_shiny_frame(user=user, shiny_frame=shiny_frame)
        else:
            return embed_generator.create_shiny_frame(user=user, shiny_frame="No shiny found")
    else:
        return embed_generator.create_item_failure_embed(user, 'shinyframe')

async def full_shiny_frame(user):
    if user.shiny_frame != -1:
       print('Shiny frame not -1')
       gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
       outcome = gen.get_outcome_for_frame(user.shiny_frame)
       pokemon = await storage_manager.get_pokemon_master_by_id(outcome['pokemon_id'])
       return embed_generator.create_full_shiny_frame(user=user, shiny_frame=user.shiny_frame, pokemon_url=pokemon.front_shiny_sprite)
    else:
        return embed_generator.create_item_failure_embed(user, 'fshinyframe, please use shinyframe first')

async def reset_seeds(user):
    item = await storage_manager.get_user_item_by_name(user, 'resetseed')
    if item.quantity >= 1:
        user.reset_seeds()
        user.shiny_frame = -1
        user.frame = 1
        user.raid_frame = 1
        item.quantity = item.quantity - 1
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_reset_seeds_embed(user)
    else:
        return embed_generator.create_item_failure_embed(user, 'resetseed')

async def skip_frames(user):
    item = await storage_manager.get_user_item_by_name(user, 'skipframe')
    if item.quantity >= 1:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_shiny_frame(start_frame=user.frame+1, max_frames_to_check=10000)
        if shiny_frame and user.frame + 100 >= shiny_frame:
            user.frame = shiny_frame
            skipped_to_shiny = True
        else:
            skipped_to_shiny = False
            user.frame += 100
        item.quantity = item.quantity - 1
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        if skipped_to_shiny:
            return embed_generator.create_skip_to_shiny_embed(user)
        else:
            return embed_generator.create_skip_frames_embed(user)
    else:
        return embed_generator.create_item_failure_embed(user, 'skipframe')    

async def reroll_iv(user, iv):
    if iv not in ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']:
        return embed_generator.create_item_failure_embed(user, 'rerolliv') 
    item = await storage_manager.get_user_item_by_name(user, 'rerolliv')
    if item.quantity >= 1:
        buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        try:
            buddy.iv[iv] = random.randrange(0,32)
            item.quantity = item.quantity - 1
            await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
            await storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"])
        except:
            return embed_generator.create_item_failure_embed(user, 'rerolliv')  
        return embed_generator.create_rerolliv_view(user, buddy)
    else:
        return embed_generator.create_item_failure_embed(user, 'rerolliv')  

async def raid_shiny_frame(user):
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_raid_frame = gen.find_shiny_raid_frame(start_frame=user.raid_frame+1, max_frames_to_check=10000)
        if shiny_raid_frame:
            outcome = gen.get_outcome_for_raid_frame(shiny_raid_frame)
            print(outcome)        
            return embed_generator.create_shiny_frame(user=user, shiny_frame=shiny_raid_frame)
        else:
            return embed_generator.create_shiny_frame(user=user, shiny_frame="No shiny found")  

async def get_items(user):
    user_items = await storage_manager.get_user_items(user)
    return embed_generator.create_items_view_table(user, user_items)

#######################Battle methods#######################
async def admin_start_battle(pokedex_id, is_shiny, user, channel_id):
    print(is_shiny)
    active_battle = await storage_manager.get_battle_by_user(user.id)
    if active_battle:
        logger.info('User in battle already')
        return None, embed_generator.create_already_in_battle_embed(user_name=user.name)
    
    logger.info(f"Battle Started for: {user.id}")
    user.frame = user.frame + 1 
    #logger.info(outcome)
    if user.current_pokemon:
        buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        if buddy:
            level = buddy.level
    else:
        level = 1
    pokemon_data = await storage_manager.get_pokemon_master_by_id(pokedex_id)
    if is_shiny:
        front_sprite = pokemon_data.front_shiny_sprite
    else:
        front_sprite = pokemon_data.front_default_sprite
    iv = {
        'hp': random.randrange(0,32),
        'attack': random.randrange(0,32),
        'defense': random.randrange(0,32),
        'special_attack': random.randrange(0,32),
        'special_defense': random.randrange(0,32),
        'speed': random.randrange(0,32)
    }
    ev = {
        'hp': 0,
        'attack': 0,
        'defense': 0,
        'special_attack': 0,
        'special_defense': 0,
        'speed': 0
    }
    new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=is_shiny, tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = level, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json)
    #set embed_color
    color = embed_generator.get_color(new_pokemon)
    
    #save user
    asyncio.create_task(storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]))
    #calculate duration
    duration = 10 * int(new_pokemon.tier) + random.randrange(0,16) 
    start_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=duration)
    end_time = start_time + delta
    logger.debug(f"battle end_time: {end_time}")
    #calculate rewards, for now just money
    rewards = {'money': 200*new_pokemon.tier, 'exp': int((int(pokemon_data.base_experience) * level+new_pokemon.tier)/4)}
    battle = Battle(id=uuid.uuid4(), user_ids=[user.id], local_id=random.randrange(100,1000), channel_id=channel_id, start_time=start_time, duration=duration, end_time=end_time, rewards=rewards, status='active', battle_pokemon_id=new_pokemon.id)
    #write new pokemon to battle_pokemon table
    asyncio.create_task(storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}battle_pokemon_id:{new_pokemon.id}", table_name="battle_pokemon", unique_columns=["id"]))
    #write battle to table
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name="battles", unique_columns=["id"])
    return new_pokemon, embed_generator.create_battle_embed(user_name=user.name, pokemon_name=new_pokemon.name, join_code=battle.local_id,duration=battle.duration, color=color, url=front_sprite)

async def start_battle(user, channel_id):
    active_battle = await storage_manager.get_battle_by_user(user.id)
    if active_battle:
        logger.info('User in battle already')
        return None, embed_generator.create_already_in_battle_embed(user_name=user.name)
    
    logger.info(f"Battle Started for: {user.id}")
    gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed) 
    outcome = gen.get_outcome_for_frame(user.frame)
    user.frame = user.frame + 1 
    #logger.info(outcome)
    if user.current_pokemon:
        buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        if buddy:
            level = buddy.level
    else:
        level = 1
    pokemon_data = await storage_manager.get_pokemon_master_by_id(outcome['pokemon_id'])
    if outcome['is_shiny']:
        user.shiny_frame = -1
        front_sprite = pokemon_data.front_shiny_sprite
    else:
        front_sprite = pokemon_data.front_default_sprite
    iv = {
        'hp': random.randrange(0,32),
        'attack': random.randrange(0,32),
        'defense': random.randrange(0,32),
        'special_attack': random.randrange(0,32),
        'special_defense': random.randrange(0,32),
        'speed': random.randrange(0,32)
    }
    ev = {
        'hp': 0,
        'attack': 0,
        'defense': 0,
        'special_attack': 0,
        'special_defense': 0,
        'speed': 0
    }
    new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=outcome['is_shiny'], tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = level, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json)
    #set embed_color
    color = embed_generator.get_color(new_pokemon)
    
    #save user
    asyncio.create_task(storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]))
    #calculate duration
    duration = 10 * int(new_pokemon.tier) + random.randrange(0,16) 
    start_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=duration)
    end_time = start_time + delta
    logger.debug(f"battle end_time: {end_time}")
    #calculate rewards, for now just money
    rewards = {'money': 200*new_pokemon.tier, 'exp': int((int(pokemon_data.base_experience) * level+new_pokemon.tier)/4)}
    battle = Battle(id=uuid.uuid4(), user_ids=[user.id], local_id=random.randrange(100,1000), channel_id=channel_id, start_time=start_time, duration=duration, end_time=end_time, rewards=rewards, status='active', battle_pokemon_id=new_pokemon.id)
    #write new pokemon to battle_pokemon table
    asyncio.create_task(storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}battle_pokemon_id:{new_pokemon.id}", table_name="battle_pokemon", unique_columns=["id"]))
    #write battle to table
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name="battles", unique_columns=["id"])
    return new_pokemon, embed_generator.create_battle_embed(user_name=user.name, pokemon_name=new_pokemon.name, join_code=battle.local_id,duration=battle.duration, color=color, url=front_sprite)

async def process_expired_battle(battle: List[Battle]):
    """
    Asynchronously processes a single expired battle.
    This is where your 'catch pokemon', 'add to inventory', 'give rewards' logic goes.
    """
    logger.info(f"Processing expired battle: {battle.id} for user(s) {battle.user_ids}")

    try:
        # --- Your battle completion logic here ---
        # 1. Add pokemon to user_pokemon table (using battle.battle_pokemon_id and battle.wild_pokemon_details)
        # 2. Grant rewards to user (using battle.rewards)
        # 3. Notify user on Discord

        logger.debug(battle)
        pokemon = await storage_manager.get_battle_pokemon_by_id(str(battle.battle_pokemon_id))
        logger.debug(pokemon)
        for user_id in battle.user_ids:
            pokemon.id = str(uuid.uuid4())
            pokemon.user_id = user_id
            user = await storage_manager.get_user(user_id=user_id)
            if user.current_pokemon:
                buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
                if buddy:
                    buddy.exp = int(int(buddy.exp) + int(battle.rewards['exp']))
                    buddy.level_up()
                    asyncio.create_task(storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"]))
            user.wallet = int(user.wallet) + int(battle.rewards['money'])
            asyncio.create_task(storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]))

            await storage_manager.save_object(obj=pokemon, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon.id}", table_name='user_pokemon', unique_columns=['id'])
        

        # Update the battle status in the database or just delete the record
        battle.status = 'inactive'
        await storage_manager.delete_battle_by_id(battle.id)
        await storage_manager.delete_battle_pokemon_by_id(str(battle.battle_pokemon_id))
        embed = embed_generator.create_battle_finish_embed(pokemon_name=pokemon.name, url=pokemon.sprite_front, color=embed_generator.get_color(pokemon), rewards=battle.rewards)
        return battle.channel_id, embed
        #asyncio.create_task(storage_manager.save_object(obj = battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name='battles', unique_columns=['id']))

    except Exception as e:
        logger.error(f"Error processing battle {battle.id}: {e}")
        # Log the error, perhaps update battle status to 'error' or retry later

async def battle_monitor_task(interval_seconds: int):
    """
    Background task to periodically check for and process expired battles.

    Args:
        interval_seconds (int): How often to poll the database in seconds.
    """
    logger.info(f"Battle monitor task started. Polling every {interval_seconds} seconds.")
    while True:
        try:
            # 1. Fetch expired battles from the database
            expired_battles_data = await storage_manager.get_expired_battles()

            if expired_battles_data:
                logger.debug(f"Found {len(expired_battles_data)} expired battles to process.")
                
                # 2. Process each expired battle concurrently
                # Corrected: asyncio.gather returns a list of results (tuples in this case)
                processed_results: List[Tuple[int, Any]] = await asyncio.gather(
                    *[process_expired_battle(battle_data) for battle_data in expired_battles_data]
                )
                
                # 3. Iterate through the list of (channel_id, embed) tuples and send messages
                for channel_id, embed in processed_results:
                    if channel_id and embed: # Ensure valid channel_id and embed
                        try:
                            # client.get_channel() might return None if the channel isn't cached
                            channel = await client.fetch_channel(channel_id)
                            if channel:
                                await channel.send(embed=embed)
                            else:
                                logger.warning(f"Could not find channel {channel_id} to send battle completion message.")
                        except Exception as send_e:
                            logger.error(f"Error sending Discord message to channel {channel_id}: {send_e}")
            else:
                logger.debug("No expired battles found.")

        except asyncio.CancelledError:
            logger.info("Battle monitor task cancelled. Shutting down.")
            break # Exit the loop cleanly on cancellation
        except Exception as e:
            logger.error(f"Unhandled error in battle_monitor_task: {e}")
            # Implement more robust error handling, perhaps back-off and retry

        # 4. Wait for the next interval
        await asyncio.sleep(interval_seconds)

async def join_battle(user, local_id, channel_id):
    #get battle
    battle = await storage_manager.get_battle_by_local_channel(local_id=local_id, channel_id=channel_id)
    #add user to user_ids
    if battle and user.id in battle.user_ids:
        return embed_generator.create_already_in_battle_embed(user_name=user.name)
    battle.user_ids.append(user.id)
    #reset duration
    duration = battle.duration
    start_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=duration)
    end_time = start_time + delta
    battle.start_time = start_time
    battle.end_time = end_time
    battle.status = 'joined'
    #save battle
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name="battles", unique_columns=["id"])
    return embed_generator.create_join_battle_embed(user_name=user.name, new_duration=duration)
    
async def run_battle(user, local_id, channel_id):
    #get battle that user is in
    battle = await storage_manager.get_battle_by_local_channel(local_id=local_id, channel_id=channel_id)
    if battle.status == 'joined':
        return embed_generator.create_run_from_battle_fail_embed(user.name)
    #remove user_id from user_ids
    if user.id in battle.user_ids:
        asyncio.create_task(storage_manager.delete_battle_by_id(battle.id))
        #reset user frame
        user.frame -= 1
        asyncio.create_task(storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])) 
        return embed_generator.create_run_from_battle_embed(user_name=user.name)
############################################################


#######################Raid methods#######################
async def start_raid(user, channel_id):
    item = await storage_manager.get_user_item_by_name(user, 'raidpass')
    if item and item.quantity >= 1:
        item.quantity = item.quantity - 1 
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
        active_raid = await storage_manager.get_raid_by_user(user.id)
        if active_raid:
            logger.info('User in raid already')
            return None, embed_generator.create_already_in_raid_embed(user_name=user.name)
        
        logger.info(f"active_raid Started for: {user.id}")
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed) 
        outcome = gen.get_outcome_for_raid_frame(user.raid_frame)
        user.raid_frame = user.raid_frame + 1 
        #logger.info(outcome)
        if user.current_pokemon:
            buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
            if buddy:
                level = buddy.level
        else:
            level = 1
        pokemon_data = await storage_manager.get_raid_pokemon_master_by_id(outcome['pokemon_id'])
        if outcome['is_shiny']:
            user.shiny_frame = -1
            front_sprite = pokemon_data.front_shiny_sprite
        else:
            front_sprite = pokemon_data.front_default_sprite
        iv = {
            'hp': random.randrange(0,32),
            'attack': random.randrange(0,32),
            'defense': random.randrange(0,32),
            'special_attack': random.randrange(0,32),
            'special_defense': random.randrange(0,32),
            'speed': random.randrange(0,32)
        }
        ev = {
            'hp': 0,
            'attack': 0,
            'defense': 0,
            'special_attack': 0,
            'special_defense': 0,
            'speed': 0
        }
        new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=outcome['is_shiny'], tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = level, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json)
        #set embed_color
        color = embed_generator.get_color(new_pokemon)
        
        #save user
        asyncio.create_task(storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]))
        #calculate duration
        duration = 100 * int(new_pokemon.tier) + random.randrange(0,61) 
        start_time = datetime.now(timezone.utc)
        delta = timedelta(seconds=duration)
        end_time = start_time + delta
        logger.debug(f"battle end_time: {end_time}")
        #calculate rewards, for now just money
        rewards = {'money': 1000*new_pokemon.tier, 'exp': int((int(pokemon_data.base_experience) * level+new_pokemon.tier)/4)*5}
        raid = Battle(id=uuid.uuid4(), user_ids=[user.id], local_id=random.randrange(100,1000), channel_id=channel_id, start_time=start_time, duration=duration, end_time=end_time, rewards=rewards, status='active', battle_pokemon_id=new_pokemon.id)
        #write new pokemon to raid_pokemon table
        asyncio.create_task(storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}raid_pokemon_id:{new_pokemon.id}", table_name="raid_pokemon", unique_columns=["id"]))
        #write battle to table
        await storage_manager.save_object(obj=raid, cache_key=f"{REDIS_PREFIX}raid_id:{raid.id}", table_name="raids", unique_columns=["id"])
        return new_pokemon, embed_generator.create_raid_embed(user_name=user.name, pokemon_name=new_pokemon.name, join_code=raid.local_id,duration=raid.duration, color=color, url=front_sprite)
    else:
        return embed_generator.create_item_failure_embed(user, 'raidpass')
     
async def process_expired_raid(battle: List[Battle]):
    """
    Asynchronously processes a single expired battle.
    This is where your 'catch pokemon', 'add to inventory', 'give rewards' logic goes.
    """
    logger.info(f"Processing expired raid: {battle.id} for user(s) {battle.user_ids}")

    try:
        # --- Your battle completion logic here ---
        # 1. Add pokemon to user_pokemon table (using battle.battle_pokemon_id and battle.wild_pokemon_details)
        # 2. Grant rewards to user (using battle.rewards)
        # 3. Notify user on Discord

        logger.debug(battle)
        pokemon = await storage_manager.get_raid_pokemon_by_id(str(battle.battle_pokemon_id))
        logger.debug(pokemon)
        for user_id in battle.user_ids:
            pokemon.id = str(uuid.uuid4())
            pokemon.user_id = user_id
            user = await storage_manager.get_user(user_id=user_id)
            if user.current_pokemon:
                buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
                if buddy:
                    buddy.exp = int(int(buddy.exp) + int(battle.rewards['exp']))
                    buddy.level_up()
                    asyncio.create_task(storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"]))
            user.wallet = int(user.wallet) + int(battle.rewards['money'])
            asyncio.create_task(storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]))

            await storage_manager.save_object(obj=pokemon, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon.id}", table_name='user_pokemon', unique_columns=['id'])
        

        # Update the battle status in the database or just delete the record
        battle.status = 'inactive'
        await storage_manager.delete_raid_by_id(battle.id)
        await storage_manager.delete_raid_pokemon_by_id(str(battle.battle_pokemon_id))
        embed = embed_generator.create_raid_finish_embed(pokemon_name=pokemon.name, url=pokemon.sprite_front, color=embed_generator.get_color(pokemon), rewards=battle.rewards)
        return battle.channel_id, embed
        #asyncio.create_task(storage_manager.save_object(obj = battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name='battles', unique_columns=['id']))

    except Exception as e:
        logger.error(f"Error processing battle {battle.id}: {e}")
        # Log the error, perhaps update battle status to 'error' or retry later

async def raid_monitor_task(interval_seconds: int):
    """
    Background task to periodically check for and process expired raids.

    Args:
        interval_seconds (int): How often to poll the database in seconds.
    """
    logger.info(f"Raid monitor task started. Polling every {interval_seconds} seconds.")
    while True:
        try:
            # 1. Fetch expired battles from the database
            expired_raids_data = await storage_manager.get_expired_raids()
            if expired_raids_data:
                logger.debug(f"Found {len(expired_raids_data)} expired battles to process.")
                
                # 2. Process each expired battle concurrently
                # Corrected: asyncio.gather returns a list of results (tuples in this case)
                processed_results: List[Tuple[int, Any]] = await asyncio.gather(
                    *[process_expired_raid(battle_data) for battle_data in expired_raids_data]
                )
                
                # 3. Iterate through the list of (channel_id, embed) tuples and send messages
                for channel_id, embed in processed_results:
                    if channel_id and embed: # Ensure valid channel_id and embed
                        try:
                            # client.get_channel() might return None if the channel isn't cached
                            channel = await client.fetch_channel(channel_id)
                            if channel:
                                await channel.send(embed=embed)
                            else:
                                logger.warning(f"Could not find channel {channel_id} to send battle completion message.")
                        except Exception as send_e:
                            logger.error(f"Error sending Discord message to channel {channel_id}: {send_e}")
            else:
                logger.debug("No expired battles found.")

        except asyncio.CancelledError:
            logger.info("Raid monitor task cancelled. Shutting down.")
            break # Exit the loop cleanly on cancellation
        except Exception as e:
            logger.error(f"Unhandled error in Raid_monitor_task: {e}")
            # Implement more robust error handling, perhaps back-off and retry

        # 4. Wait for the next interval
        await asyncio.sleep(interval_seconds)

async def join_raid(user, local_id, channel_id):
    #get battle
    battle = await storage_manager.get_raid_by_local_channel(local_id=local_id, channel_id=channel_id)
    #add user to user_ids
    if battle and user.id in battle.user_ids:
        return embed_generator.create_already_in_raid_embed(user_name=user.name)
    battle.user_ids.append(user.id)
    #reset duration
    duration = battle.duration
    start_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=duration)
    end_time = start_time + delta
    battle.start_time = start_time
    battle.end_time = end_time
    battle.status = 'joined'
    #save battle
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}raid_id:{battle.id}", table_name="raids", unique_columns=["id"])
    return embed_generator.create_join_raid_embed(user_name=user.name, new_duration=duration)

#######################Lottery methods#######################

async def enter_lottery(user):
    lottery_entry_fee = 10000
    lottery = await storage_manager.get_active_lottery()
    if user.id in lottery.user_ids:
        return embed_generator.create_lottery_embed(user=user, content=f"Current Jackpot: ${lottery.amount:,.0f}\n")
    if user.wallet >= lottery_entry_fee:
        user.wallet -= lottery_entry_fee
        lottery.user_ids.append(user.id)
        lottery.amount += lottery_entry_fee
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]) 
        await storage_manager.save_object(obj=lottery, cache_key=f"{REDIS_PREFIX}lottery_id:{lottery.id}", table_name="lottery", unique_columns=["id"]) 
        return embed_generator.create_lottery_embed(user=user, content=f"Successfully entered lottery!\nCurrent Jackpot: ${lottery.amount:,.0f}\n")
    else:
        return embed_generator.create_lottery_embed(user=user, content=f"Could not enter lottery due to insufficient funds\n\Cost:{lottery_entry_fee}\nCurrent Jackpot: ${lottery.amount:,.0f}\n")

async def process_expired_lottery(lottery: Lottery):
    if lottery.user_ids:
        winner = random.choice(lottery.user_ids)
    else:
        return embed_generator.create_lottery_embed(None, f"No winner selected, rolling over...\nAmount: ${lottery.amount:,.0f}")
    if winner:
        user = await storage_manager.get_user(winner)
        user.wallet += lottery.amount
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_lottery_embed(user, f"{user.name} has won the lottery!\nAmount: ${lottery.amount:,.0f}")
    else:
        duration = 24
        start_time = datetime.now(timezone.utc)
        delta = timedelta(hours=duration)
        end_time = start_time + delta
        lottery.start_time = start_time
        lottery.end_time = end_time
        await storage_manager.save_object(obj=lottery, cache_key=f"{REDIS_PREFIX}lottery_id:{lottery.id}", table_name="lottery", unique_columns=["id"]) 
        return embed_generator.create_lottery_embed(None, f"No winner selected, rolling over...\nAmount: ${lottery.amount:,.0f}")

async def lottery_monitor_task(interval_seconds: int):
    """
    Background task to periodically check for and process expired lotteries.

    Args:
        interval_seconds (int): How often to poll the database in seconds.
    """
    logger.info(f"Lottery monitor task started. Polling every {interval_seconds} seconds.")
    while True:

        # 1. Fetch expired battles from the database
        expired_lottery_data = await storage_manager.get_expired_lottery()
        if expired_lottery_data:
            print(f"Found {expired_lottery_data.id} expired lottery to process.")
            await storage_manager.delete_lottery_by_id(expired_lottery_data.id)
            embed = await process_expired_lottery(expired_lottery_data)
            channel: discord.VoiceChannel | discord.StageChannel | discord.ForumChannel | discord.TextChannel | discord.CategoryChannel | discord.Thread | PrivateChannel | None = await client.fetch_channel(LOTTERY_ID)
            await channel.send(embed=embed)
        else:
            active_lottery = await storage_manager.get_active_lottery()
            if not active_lottery:
                duration = 24
                start_time = datetime.now(timezone.utc)
                delta = timedelta(hours=duration)
                end_time = start_time + delta
                new_lottery = Lottery(id=uuid.uuid4(), user_ids=[], start_time=start_time,end_time=end_time, amount=30000)
                await storage_manager.save_object(obj=new_lottery, cache_key=f"{REDIS_PREFIX}lottery_id:{new_lottery.id}", table_name="lottery", unique_columns=["id"]) 

        # 4. Wait for the next interval
        await asyncio.sleep(interval_seconds)

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    battle_monitor = asyncio.create_task(battle_monitor_task(interval_seconds=10)) # Poll every 10 seconds
    raid_monitor = asyncio.create_task(raid_monitor_task(interval_seconds=60)) # Poll every 60 seconds
    lottery_monitor = asyncio.create_task(lottery_monitor_task(interval_seconds=3600)) # Poll every hour
@client.event
async def on_message(message):
    start_time = time.time()

    channel_id = message.channel.id
    if message.author == client.user:
        return
    message.content = message.content.lower()
    user = await storage_manager.get_user(message.author.id)

#######################General commands#######################
    if message.content.startswith('.help filter'):
        embed = get_help_filter()
        await message.channel.send(embed=embed)
    elif message.content.startswith('.help admin') and user.id == 701062435678846998:
        embed = get_admin_help()
        await message.channel.send(embed=embed)
    elif message.content.startswith('.help'):
        embed = get_help()
        await message.channel.send(embed=embed)
    
    if user and message.content.startswith('.register'):
        embed = embed_generator.create_already_registered_embed()
        await message.channel.send(embed=embed)
    elif message.content.startswith('.register'):
        embed = await register(message.author.id, message.author.name)
        await message.channel.send(embed=embed)
    elif message.content.startswith('.') and not user:
        embed = embed_generator.create_not_registered_embed()
        await message.channel.send(embed=embed)
        return    

    if message.content.startswith('.odds'):
        embed = await get_odds(user=user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.bug'):
        embed = embed_generator.create_bug_reported_embed(user)
        await message.channel.send(embed=embed)
        channel = await client.fetch_channel(BUG_ID)
        bug_embed = embed_generator.create_bug_log_embed(user, message.content.replace(".bug", ""))
        await channel.send(embed=bug_embed)

    if message.content.startswith('.git'):
        await message.channel.send('https://github.com/ultra-move/goomybot-v3')

#######################Admin commands########################
    if message.content.startswith('.addframe') and user.id == 701062435678846998:
        split = message.content.split()
        user_id = split[1]
        amount = split[2]
        embed = await add_frame(user_id, int(amount))
        await message.channel.send(embed=embed)

    if message.content.startswith('.removeframe') and user.id == 701062435678846998:
        split = message.content.split()
        user_id = split[1]
        amount = split[2]
        embed = await remove_frame(user_id, int(amount))
        await message.channel.send(embed=embed)

    if message.content.startswith('.flush') and user.id == 701062435678846998:
        embed = await flush_all()
        await message.channel.send(embed=embed)

    if message.content.startswith('.raidframe') and user.id == 701062435678846998:
        embed = await raid_shiny_frame(user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.resetodds') and user.id == 701062435678846998:
        embed = await odds_reset()
        await message.channel.send(embed=embed)

    if message.content.startswith('.adminspawn') and user.id == 701062435678846998:
        pokedex_id = int(message.content.split()[1])
        is_shiny = {"true": True, "false": False}.get(message.content.split()[2].lower(), False)
        pookemon, embed = await admin_start_battle(pokedex_id=pokedex_id, is_shiny=is_shiny, user=user, channel_id=channel_id)
        await message.channel.send(embed=embed)

    if message.content.startswith('.addmoney') and user.id == 701062435678846998:
        split = message.content.split()
        user_id = split[1]
        amount = split[2]
        embed = await add_money(user_id=user_id, amount=amount)
        await message.channel.send(embed=embed)

    if message.content.startswith('.removemoney') and user.id == 701062435678846998:
        split = message.content.split()
        user_id = split[1]
        amount = split[2]
        embed = await remove_money(user_id=user_id, amount=amount)
        await message.channel.send(embed=embed)

#######################Battle commands#######################
    if message.content.startswith('.spawn'):
        pokemon, embed = await start_battle(user=user, channel_id=channel_id)
        await message.channel.send(embed=embed)
        if pokemon and pokemon.is_shiny:
            flex_log = await storage_manager.get_flex_log(user.id, channel_id, pokemon.name)
            if not flex_log:
                log = FlexLog(id= uuid.uuid4(), user_id=user.id, channel_id=channel_id, name=pokemon.name, status='active', timestamp=datetime.now(timezone.utc), expiration_date= datetime.now(timezone.utc) + timedelta(hours=4))
                await storage_manager.save_object(obj=log, cache_key=f"{REDIS_PREFIX}flexlog_id:{log.id}", table_name='flex_log', unique_columns=['id'])
                channel = await client.fetch_channel(FLEX_ID)
                embed = embed_generator.create_flex_embed(user, pokemon)
                await channel.send(embed=embed)

    if message.content.startswith('.run'):
        local_id = message.content[-3:]
        embed = await run_battle(user=user, local_id=local_id, channel_id=channel_id)
        await message.channel.send(embed=embed)

    if message.content.startswith('.join') and not message.content.startswith('.joinraid'):
        local_id = message.content[-3:]
        embed = await join_battle(user=user, local_id=local_id, channel_id=channel_id)
        await message.channel.send(embed=embed)

#######################Raid commands#######################
    if message.content.startswith('.raid') and not message.content.startswith('.raidframe'):
        try:
            pokemon, embed = await start_raid(user=user, channel_id=channel_id)
            await message.channel.send(embed=embed)
            if pokemon and pokemon.is_shiny:
                channel = await client.fetch_channel(FLEX_ID)
                embed = embed_generator.create_flex_embed(user, pokemon)
                await channel.send(embed=embed)
        except:
            embed = embed_generator.create_raid_failure_embed(user)
            await message.channel.send(embed=embed)
            return

    if message.content.startswith('.joinraid'):
        local_id = message.content[-3:]
        embed = await join_raid(user=user, local_id=local_id, channel_id=channel_id)
        await message.channel.send(embed=embed)
#######################User commands#######################
    if message.content.startswith('.profileimage'):
        url = message.content.split()
        if len(url) > 1:
            embed = await set_profile_image(user=user, url=url[1])
        else:
            embed = embed_generator.create_user_profile_image_failed_embed(user)
        await message.channel.send(embed=embed)
    elif message.content.startswith('.profile'):
        embed = embed_generator.create_user_profile_embed(user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.list'):
        page = message.content.split()
        try:
            if len(page) > 1:
                if int(page[1]) > 0: # Ensure user doesn't ask for page 0 or negative
                    requested_page = int(page[1]) - 1
                    embed: discord.Embed = await list_pokemon(user=user, page=requested_page, page_size=10)
                else:
                    embed = await list_pokemon(user=user, page=0, page_size=10)
            else:
                embed = await list_pokemon(user=user, page=0, page_size=10)
        except:
            embed = await list_pokemon(user=user, page=0, page_size=10)

        await message.channel.send(embed=embed)
    if message.content.startswith('.view'):
        local_id = message.content.split()
        if len(local_id) > 1:
            embed = await view_pokemon(user=user, local_id=str(local_id[1]))
        else:
            embed = await view_buddy(user=user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.filter'):
        embed = await filter_pokemon(user=user, filter_message=message.content)
        await message.channel.send(embed=embed)

    if message.content.startswith('.buddy'):
        local_id = message.content.split()
        if len(local_id) > 1:
            embed = await set_buddy(user=user, local_id=str(local_id[1]))
        else:
            embed = await view_buddy(user=user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.evolve'):
        name = message.content.split()
        if len(name) > 1 and name[1]:
            embed = await evolve_buddy(user=user, name=name[1])
        else:
            embed = await evolve_buddy(user=user, name=None)
        await message.channel.send(embed=embed)

    if message.content.startswith('.frame'):
        embed = embed_generator.create_frame_embed(user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.lottery'):
        embed = await enter_lottery(user)
        await message.channel.send(embed=embed)        
#######################item commands#######################
    if message.content.startswith('.shop'):
        embed = await get_shop(user)
        await message.channel.send(embed=embed)    
    
    if message.content.startswith('.buy'):
        name_quantity = message.content.split()
        try:
            if len(name_quantity) == 3:
                if name_quantity[1] == 'shinyframe':
                    embed = await buy_item(user, 'shinyframe', int(name_quantity[2]))
                if name_quantity[1] == 'resetseed':
                    embed = await buy_item(user, 'resetseed', int(name_quantity[2]))
                if name_quantity[1] == 'skipframe':
                    embed = await buy_item(user, 'skipframe', int(name_quantity[2]))
                if name_quantity[1] == 'rerolliv':
                    embed = await buy_item(user, 'rerolliv', int(name_quantity[2]))
                if name_quantity[1] == 'raidpass':
                    embed = await buy_item(user, 'raidpass', int(name_quantity[2]))
            else:
                embed = embed_generator.create_invalid_syntax_embed(user)
        except:
                embed = embed_generator.create_invalid_syntax_embed(user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.items'):
        embed = await get_items(user)
        await message.channel.send(embed=embed)

    if message.content.startswith('.resetseed'):
        embed = await reset_seeds(user)
        await message.channel.send(embed=embed)
        
    if message.content.startswith('.rerolliv'):
        iv = message.content.split()
        if len(iv) > 1:
            embed = await reroll_iv(user=user, iv=str(iv[1]))
        else:
            embed = embed_generator.create_item_failure_embed(user=user, item_name='rerolliv')
        await message.channel.send(embed=embed)
    
    if '.fshinyframe' in message.content:
        embed = await full_shiny_frame(user)
        await message.channel.send(embed=embed)

    if '.shinyframe' in message.content:
        embed = await shiny_frame(user)
        await message.channel.send(embed=embed)

    if '.skipframe' in message.content:
        embed = await skip_frames(user)
        await message.channel.send(embed=embed)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Message Response Time: {elapsed_time} seconds")

client.run(os.getenv('DISCORD_BOT_TOKEN'))

