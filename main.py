import asyncio
import asyncio.log
from datetime import datetime, timezone, timedelta
import json
import logging
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from discord.abc import PrivateChannel
from redis.exceptions import RedisError
import discord

from classes import trainer_battle
from classes.battle import Battle
from classes.data_loader import DataLoader
from classes.database_manager import DatabaseManager
from classes.embed_generator import EmbedGenerator
from classes.flex_log import FlexLog
from classes.item import Item
from classes.lottery import Lottery
from classes.professor import Professor
from classes.quest import Quest
from classes.pokemon_master import PokemonMaster
from classes.redis_manager import RedisManager
from classes.sprites import Sprites
from classes.storage_manager import StorageManager
#from classes.data_loader import DataLoader
from classes.trade import Trade
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
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0") # Provide a default for local testing if not in .env
REDIS_PREFIX = os.getenv("REDIS_PREFIX")
FLEX_ID: str | None = os.getenv("FLEX_ID")
BUG_ID: str | None = os.getenv("BUG_ID")
LOTTERY_ID= os.getenv("LOTTERY_ID")
PROFESSOR_ID= os.getenv("PROFESSOR_ID")
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
**__Help Commands__**
* `.help`: Displays this help message.
* `.help user`: Displays the user commands help message.
* `.help pokemon`: Displays the pokemon commands help message.
* `.help moves`: Displays the moves commands help message.
* `.help filter`: Displays the filter commands help message.
* `.help battle`: Displays the battle commands help message.
* `.help raid`: Displays the raid commands help message.
* `.help items`: Displays the items commands help message.
* `.help event`: Displays the event commands help message.
* `.help trade`: Displays the trade commands help message.
**__General Commands__**
* `.register`: Registers you for the game. You'll need to do this before using most other commands!
* `.odds`: Displays the current odds
* `.lottery`: Enters the lottery, or if already entered, displays information about the lottery
* `.leaderboard`: Shows the leaderboard
* `.quest`: Shows the daily quest, or completes it if condition met
* `.bug <bug report>`: Submits a bug to the bug channel
* `.git`: provides a link to the git repository
"""
    return embed_generator.create_help_embed(info=help)

def get_help_event():
    help = """
**__Event Commands__**
* `.event`: displays information about the current event
* `.event toggle`: joins/leaves the current event
* `.eventframe`: Shows the shinyframe of the event pokemon
"""
    return embed_generator.create_help_embed(info=help)

def get_help_moves():
    help = """
**__Move Commands__**
* `.moves`: Displays moves that your pokemon currently knows
* `.seemove <move_name>`: Shows info about the given move 
* `.learnset <page_number>`: Shows all moves that your pokemon can learn 
* `.learn <slot> <move_name>`: Teaches your pokemon the selected move
"""
    return embed_generator.create_help_embed(info=help)

def get_help_user():
    help = """
**__User Commands__**
* `.profile`: Shows your user profile.
* `.profileimage <URL>`: Sets your profile image to the provided URL (must be from showdown sprites).
* `.list [page_number]`: Displays a list of your Pokémon. You can specify a page number to view more.
* `.view [local_id] or [recent]`: If a `local_id` is provided, views details of that specific Pokémon. If no `local_id` is given, it shows details of your current buddy Pokémon.
* `.stats [local_id] or [recent]`: Like view but for stats
* `.filter <filter_message>`: Filters your Pokémon list based on your criteria.
* `.frame`: Views current frame & raid frame
* `.fullframe`: Toggles whether shinyframe commands show the pokemon or not
* `.displayname <name>`: Changes your display name
"""
    return embed_generator.create_help_embed(info=help)

def get_help_pokemon():
    help = """
**__Pokemon Commands__**
* `.buddy [local_id] or [recent]`: If a `local_id` is provided, sets that Pokémon as your buddy. If no `local_id` is given, it shows your current buddy Pokémon.
* `.evolve [name]`: Evolves buddy pokemon to name, buddy will evolve to a random choice if multiple are available and no name is provided
* `.safe [local_id] <recent>`: Marks a pokemon as safe or not safe. Local id comes from .list command. Defaults to buddy
* `.release [local_id]`: Releases specified pokemon (from .list)
* `.release duplicates`: Releases duplicate pokemon, keeps buddy, safe, shiny and tier 4 pokemon. Keeps the pokemon with the highest total iv
* `.pokedex <page_number>`: Shows all un-owned pokemon
* `.raidpokedex <page_number>`: Shows all un-owned raid pokemon
* `.see <name>`: Displays sprites of a given pokemon, works with raid pokemon
"""
    return embed_generator.create_help_embed(info=help)

def get_help_battle():
    help = """
**__Battle Commands__**
* `.spawn`: Initiates a new battle.
* `.run`: Runs from a battle that the user is in.
* `.join <local_id>`: Joins an existing battle with the specified local ID.
"""
    return embed_generator.create_help_embed(info=help)

def get_help_raid():
    help = """
**__Raid Commands__**
* `.raid`: Initiates a new raid (requires a raidpass).
* `.joinraid <local_id>`: Joins an existing raid with the specified local ID.
* `.raidframe`: Shows your shiny raid frame, this is free!
"""
    return embed_generator.create_help_embed(info=help)

def get_help_trade():
    help = """
**__Trade Commands__**
* `.trade`: Displays current trade
* `.trade @user`: Initiates a trade with @user
* `.trade join <local_id>`: Starts trade that another user initiated
* `.trade confirm`: Confirms a trade (both users must confirm)
* `.trade cancel`: Cancels a trade
* `.trade add pokemon <local_id>`: Adds a pokemon to the trade from your .list (or .filter)
* `.trade add item <item_name> <quantity>`: Adds the specified item to the trade
* `.trade add money <local_id>`: Adds specified amount of money to trade

"""
    return embed_generator.create_help_embed(info=help)    

def get_help_challenge():
    help = """
**__Challenge Commands__**
* `.challenge <local_id>`: Attempts to solve the professor challenge (using pokemon from .list)
* `.challenge info`: Shows when full rewards can be earned again

Bonus applies a 2x to all rewards
Lockout time is 10 minutes from last completed challenge
The below applies from your oldest completed challenge:
    10 minutes - 1 hour: basic rewards
    1 - 2 hours: 2x basic rewards
    2 - 3 hours: 4x basic rewards
    3 - 4 hours: 6x basic rewards
    4 hours: 10x basic rewards
"""
    return embed_generator.create_help_embed(info=help)
def get_help_items():
    help = """
**__Item Commands__**
* `.shop`: Displays available items in the shop
* `.buy <item_name> <quantity>`: Buys the specified quantity of an item. If no quantity is provided it defaults to 1
* `.items`: Shows a list of your owned items.
* `.resetseed`: Uses a Reset Seed to reset your frame and shiny seed.
* `.shinyframe`: Dispalys the frame that your next shiny is at
* `.skipframe <quantity>`: Uses a Skip Frame (quantity * 100 frames or to shiny frame).
* `.skipraidframe <quantity>`: Uses a Skip Raid Frame (quantity * 15 frames or to shiny frame).
* `.rerolliv <iv_name>`: Rerolls selected buddy iv.
* `.rarecandy <quantity>`: Levels up your buddy
* `.regionpass <region> or none`: Sets region to selected region, or freely remove region
"""
    return embed_generator.create_help_embed(info=help)

def get_help_filter():
    help = """
**__Filter Commands__**
* `.filter`: Resets filter to default order.
* `.filter <filter_key> <value>`: Sets a filter. For example:
    * `.filter shiny`: Shows only shiny Pokémon.
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
    * `.filter order recent`: Orders Pokémon by most recently caught
* You can combine multiple filters and orders in one command:
    * `.filter shiny tier 1 order level desc`
"""

    return embed_generator.create_help_embed(info=help)

def get_admin_help():
    admin_help = """
    ---
**__Admin Commands__**
    * `.addframe <user_id> <amount>`: Adds a specified amount of frames to a user.
    * `.removeframe <user_id> <amount>`: Removes a specified amount of frames from a user.
    * `.flush`: Clears all entires in the cache.
    * `.resetodds`: Required after adjusting odds to adjust shiny frames
    * `.adminspawn <pokedex_id> <is_shiny>`: Spawns a Pokémon. `is_shiny` can be `true` or `false`.
    * `.adminraid <pokedex_id> <is_shiny>`: Spawns a Pokémon. `is_shiny` can be `true` or `false`.
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
        if p.is_shiny:
            name = f"✨{p.name.capitalize()}✨"
        else:
            name = p.name.capitalize()
        user.view_table[i+1] = {'id': str(p.id), 'name': name}
    logger.debug(user.view_table)
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    if total_pages == 0:
        total_pages += 1
    return embed_generator.create_user_view_table(user, page+1, total_pages) 

async def list_missing_pokemon(user, page, page_size):
    records, total_pages, total_count_result = await storage_manager.get_missing_pokedex(user=user, page=page, pagesize=page_size)
    #build the users view table for easy access later
    pokemon_table = {}
    for p,i in zip(records, range(page_size)):
      pokemon_table[i+1] = {'id': str(p['id']), 'name': p['name']}
    if total_pages == 0:
       total_pages += 1
    return embed_generator.create_missing_view_table(user, pokemon_table, page+1, total_pages, total_count_result, 1025) 

async def list_missing_raid_pokemon(user, page, page_size):
    records, total_pages, total_count_result = await storage_manager.get_missing_raid_pokedex(user=user, page=page, pagesize=page_size)
    #build the users view table for easy access later
    pokemon_table = {}
    for p,i in zip(records, range(page_size)):
      pokemon_table[i+1] = {'id': str(p['id']), 'name': p['name']}
    if total_pages == 0:
       total_pages += 1
    return embed_generator.create_missing_view_table(user, pokemon_table, page+1, total_pages, total_count_result, 259) 

async def view_pokemon(user, local_id):
    pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(local_id)]['id'])
    logger.debug(pokemon)
    return embed_generator.create_pokemon_view(user, pokemon)

async def view_pokemon_stats(user, local_id):
    pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(local_id)]['id'])
    logger.debug(pokemon)
    return embed_generator.create_pokemon_stats_view(user, pokemon)

async def view_recent_pokemon(user):
    pokemon = await storage_manager.get_user_pokemon_by_recent(user)
    logger.debug(pokemon)
    return embed_generator.create_pokemon_view(user, pokemon)

async def view_recent_pokemon_stats(user):
    pokemon = await storage_manager.get_user_pokemon_by_recent(user)
    logger.debug(pokemon)
    return embed_generator.create_pokemon_stats_view(user, pokemon)

async def view_buddy(user):
    pokemon = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
    logger.debug(pokemon)
    return embed_generator.create_pokemon_view(user, pokemon)    

async def view_buddy_stats(user):
    pokemon = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
    logger.debug(pokemon)
    return embed_generator.create_pokemon_stats_view(user, pokemon) 

async def set_buddy_recent(user):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot release while in a trade")
    active_battle = await storage_manager.get_battle_by_user(user.id)
    active_raid = await storage_manager.get_raid_by_user(user.id)
    if active_battle or active_raid:
        return embed_generator.create_change_buddy_failed_embed(user)
    pokemon = await storage_manager.get_user_pokemon_by_recent(user)
    if pokemon:
        user.current_pokemon = pokemon.id
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_pokemon_view(user, pokemon)

async def set_buddy(user, local_id):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot change buddy while in a trade")
    active_battle = await storage_manager.get_battle_by_user(user.id)
    active_raid = await storage_manager.get_raid_by_user(user.id)
    if active_battle or active_raid:
        return embed_generator.create_change_buddy_failed_embed(user)
    pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(local_id)]['id'])
    if pokemon:
        user.current_pokemon = pokemon.id
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_pokemon_view(user, pokemon)

def set_buddy_from_evolution(buddy, evolution):
    buddy.name = evolution.name
    buddy.ability = random.choice(evolution.abilities_names)
    buddy.types = evolution.types_names
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
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot evolve while in a trade!")
    buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))

    if not buddy:
        return embed_generator.create_evolved_fail_embed(user.name, "Your buddy Pokémon could not be found.")
    if buddy.safe:
        return embed_generator.create_evolved_fail_embed(user.name, "Can not evolve safe pokemon, please use .safe to toggle")
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
        'held_item': False  # False means do not filter; True means filter where held_item IS NOT NULL
    }
    default_order = {
        'pokedex': {'value': False, 'order': "ASC"},
        'tier': {'value': False, 'order': "ASC"},
        'level': {'value': False, 'order': "ASC"},
        'recent': {'value': False, 'order': "DESC"},   # virtual
        'created_at': {'value': False, 'order': "DESC"}  # real column
    }

    parsed_filter, parsed_order, final_status = parse_filter_command(
        message=filter_message,
        default_filter=default_filter,
        default_order=default_order
    )
    logger.debug(final_status)

    user.filter = parsed_filter
    user.order_by = parsed_order

    return await list_pokemon(user=user, page=0, page_size=10)

def parse_filter_command(message, default_filter, default_order):
    """
    Parses a user command string to extract filter and order criteria.

    Supports 'recent' as a friendly alias for ordering by created_at DESC.
    """
    parsed_filter = default_filter.copy()
    parsed_order = {k: v.copy() for k, v in default_order.items()}
    status_messages = []

    tokens = message.lower().strip().split()
    if tokens and tokens[0] == ".filter":
        tokens = tokens[1:]

    if not tokens:
        return parsed_filter, parsed_order, "No filters or order specified."

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token == "order":
            i += 1  # skip 'order'
            while i < len(tokens):
                order_key = tokens[i]

                # Special handling: 'recent' means 'created_at DESC'
                if order_key == 'recent':
                    parsed_order['recent']['value'] = True
                    parsed_order['recent']['order'] = "DESC"
                    parsed_order['created_at']['value'] = True
                    parsed_order['created_at']['order'] = "DESC"
                    i += 1
                    # Skip a possible direction token for 'recent' if present
                    if i < len(tokens) and tokens[i] in ['asc', 'desc']:
                        i += 1
                    continue

                if order_key in parsed_order:
                    if i + 1 < len(tokens):
                        direction = tokens[i + 1]
                        if direction in ['asc', 'desc']:
                            parsed_order[order_key]['value'] = True
                            parsed_order[order_key]['order'] = direction.upper()
                        else:
                            status_messages.append(f"Invalid order direction for '{order_key}': '{direction}'.")
                        i += 2
                    else:
                        status_messages.append(f"Order key '{order_key}' missing direction.")
                        i += 1
                else:
                    status_messages.append(f"Unrecognized order key '{order_key}'.")
                    i += 1
            break  # done parsing

        # --- Filters ---
        key = token
        value_str = None

        if '=' in key:
            parts = key.split('=', 1)
            key, value_str = parts[0], parts[1]
            i += 1
        # CORRECT PLACEMENT FOR THE SHINY SHORTCUT
        elif key == 'shiny':
            parsed_filter[key] = True  # Set shiny to True if just 'shiny' is present
            i += 1
            continue  # Move to the next token immediately
        elif i + 1 < len(tokens):
            value_str = tokens[i + 1]
            i += 2
        else:
            status_messages.append(f"Filter key '{key}' missing value.")
            i += 1
            continue

        if key in parsed_filter:
            if key == 'type':
                for t in value_str.split(','):
                    t_clean = t.strip()
                    if t_clean:
                        parsed_filter['type'].append(t_clean)
            elif key in ['shiny', 'held_item']: # This handles 'shiny=true' or 'shiny=false'
                if value_str in ['true', 'false']:
                    parsed_filter[key] = (value_str == 'true')
                else:
                    status_messages.append(f"Invalid value for '{key}': '{value_str}'.")
            elif key in ['tier', 'level']:
                try:
                    num = int(value_str)
                    if num >= 0:
                        parsed_filter[key] = num
                    else:
                        status_messages.append(f"Invalid value for '{key}': must be non-negative.")
                except ValueError:
                    status_messages.append(f"Invalid integer for '{key}': '{value_str}'.")
            elif key in ['name', 'nature', 'region']:
                parsed_filter[key] = value_str
            else:
                status_messages.append(f"Unknown filter key '{key}'.")
        else:
            status_messages.append(f"Unknown filter key '{key}'.")

    final_status = "Parsed successfully." if not status_messages else "\n".join(status_messages)
    return parsed_filter, parsed_order, final_status

async def see_pokemon(name):
    result = await storage_manager.get_pokemon_master_by_name(name)
    if result:
        return embed_generator.create_master_pokemon_view(result)
    else:
        result = await storage_manager.get_raid_pokemon_master_by_name(name)
        if result:
             return embed_generator.create_master_pokemon_view(result)
        else:
            return embed_generator.create_master_pokemon_view_failure()

async def see_single_move(name):
    result = await storage_manager.get_move_by_name(name)
    if result:
        return embed_generator.create_move_view(result)

async def release_duplicates(user):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot release while in a trade!")
    release_count = await storage_manager.delete_duplicates(user.id, user.current_pokemon)
    reward_amount = release_count * 200
    user.wallet += reward_amount
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_release_embed(user, f"Released {release_count} pokemon!\nEarned ${reward_amount:,.0f}")

async def release_single(user, selection):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot release while in a trade!")
    try:
        to_delete = user.view_table[str(selection)]['id']
        pokemon = await storage_manager.get_user_pokemon_by_id(to_delete)
        if pokemon.safe or str(user.current_pokemon) == str(to_delete):
            return embed_generator.create_release_embed(user, content="Can not release safe or buddy pokemon!")
        else:
            user.view_table[str(selection)]['id'] = None
            await storage_manager.delete_user_pokemon_by_id(to_delete)
            reward_amount = 200
            user.wallet += reward_amount
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
            return embed_generator.create_release_embed(user, f"Released {pokemon.name.capitalize()}!\nEarned ${reward_amount:,.0f}")
    except Exception as e:
        logger.error(f"Error processing release: {e}")
        return embed_generator.create_release_embed(user, content="Could not release pokemon, please check syntax")


async def pokedex(user):
    # get all user pokedex_id <= 1025
    True
async def raid_pokedex(user):
    True

async def mark_safe(user, index):
    try:
        pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(index)]['id'])
        if pokemon.safe:
            pokemon.safe = False
        else:
            pokemon.safe = True
        await storage_manager.save_object(obj=pokemon, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon.id}", table_name="user_pokemon", unique_columns=["id"])
        return embed_generator.create_safe_pokemon_view(user, pokemon)
    except:
        return embed_generator.create_safe_pokemon_failure_view(user, pokemon)

async def mark_safe_recent(user):
    try:
        pokemon = await storage_manager.get_user_pokemon_by_recent(user)
        if pokemon.safe:
            pokemon.safe = False
        else:
            pokemon.safe = True
        await storage_manager.save_object(obj=pokemon, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon.id}", table_name="user_pokemon", unique_columns=["id"])
        return embed_generator.create_safe_pokemon_view(user, pokemon)
    except:
        return embed_generator.create_safe_pokemon_failure_view(user, pokemon)    

async def mark_safe_buddy(user):
    try:
        pokemon = await storage_manager.get_user_pokemon_by_id(user.current_pokemon)
        if pokemon.safe:
            pokemon.safe = False
        else:
            pokemon.safe = True
        await storage_manager.save_object(obj=pokemon, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon.id}", table_name="user_pokemon", unique_columns=["id"])
        return embed_generator.create_safe_pokemon_view(user, pokemon)
    except:
        return embed_generator.create_safe_pokemon_failure_view(user, pokemon)    

async def set_profile_image(user, url):
    host_string = r'https://play.pokemonshowdown.com/sprites/'
    if url.startswith(host_string):
        user.profile_image = url
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_user_profile_image_success_embed(user)
    else:
        return embed_generator.create_user_profile_image_failed_embed(user, host_string)

async def toggle_full_frame(user):
    if user.full_frame:
        user.full_frame = False
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_full_frame_embed(user)
    else:
        user.full_frame = True
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_full_frame_embed(user)

async def display_name(user, display_name):
    user.name = display_name
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_user_profile_embed(user)


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

async def add_raid_frame(user_id, frames):
    user = await storage_manager.get_user(user_id=user_id)
    user.raid_frame += frames
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed(f"Added {frames} raid frames for {user.name}")

async def remove_raid_frame(user_id, frames):
    user = await storage_manager.get_user(user_id=user_id)
    user.raid_frame -= frames
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    return embed_generator.create_admin_embed(f"Added {frames} raid frames for {user.name}")


async def flush_all():
    await redis_manager.flush_all()
    return embed_generator.create_admin_embed("flushed cache")

async def odds_reset():
    users = await storage_manager.get_all_users()
    for user in users:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_shiny_frame(user = user, start_frame=user.frame+1, max_frames_to_check=10000)
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

async def admin_reset_quest(user_id):
    active_quest = await storage_manager.get_active_quest(user_id)
    await storage_manager.delete_quest_by_id(active_quest.id)
    return embed_generator.create_admin_embed(f"Reset Quest for {user_id}")

async def find_in_seeds(user:User, pokemon_id):
    result = await Generator.find_shiny_seeds(pokemon_id=int(pokemon_id), user=user, max_frames_to_check=5000)
    user.tier_seed = result["tier_seed"]
    user.type_seed = result["type_seed"]
    user.pokemon_seed = result["pokemon_seed"]
    user.shiny_seed = result["shiny_seed"]
    user.item_seed = result["item_seed"]
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]) 
    return embed_generator.create_admin_embed(f"Seeds for {pokemon_id}\n{json.dumps(result)}")

#######################Item methods#######################
async def get_shop(user):
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
    return embed_generator.create_shop_view_table(user, items)

async def buy_item(user, item_name, quantity):
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
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot purchase items while in a trade")
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
            final_item = Item(id=uuid.uuid4(), user_id=user.id, name=item_name, quantity=quantity, uses=0)
        user.wallet -= price
        user.total_spent += price
        await storage_manager.save_object(obj=final_item, cache_key=f"{REDIS_PREFIX}item_id:{final_item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]) 
        return embed_generator.create_item_bought_embed(user, item_name, quantity) 
    else:
        return embed_generator.create_item_bought_failed_embed(user, item_name, quantity)
    
async def shiny_frame(user):
    gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
    shiny_frame = gen.find_shiny_frame(user= user, start_frame=user.frame+1, max_frames_to_check=10000)
    if shiny_frame:
        outcome = gen.get_outcome_for_frame(shiny_frame, user)
        user.shiny_frame = shiny_frame
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])      
        return embed_generator.create_shiny_frame(user=user, shiny_frame=shiny_frame)
    else:
        return embed_generator.create_shiny_frame(user=user, shiny_frame="No shiny found")

async def get_pokemon_for_shiny_frame(user, frame):
    gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
    outcome = gen.get_outcome_for_frame(frame, user)
    pokemon = await storage_manager.get_pokemon_master_by_id(outcome['pokemon_id'])
    return pokemon

async def full_shiny_frame(user):
    gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
    shiny_frame = gen.find_shiny_frame(user=user,start_frame=user.frame+1, max_frames_to_check=10000)
    if shiny_frame:
        user.shiny_frame = shiny_frame
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])        
        if user.full_frame:
            pokemon = await get_pokemon_for_shiny_frame(user, user.shiny_frame)
            return embed_generator.create_full_shiny_frame(user, user.shiny_frame, pokemon.name, pokemon.front_shiny_sprite)
        else:
            return embed_generator.create_shiny_frame(user=user, shiny_frame=shiny_frame)
    else:
        return embed_generator.create_shiny_frame(user=user, shiny_frame="No shiny found")
    
async def full_raid_shiny_frame(user):
    gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
    shiny_frame = gen.find_shiny_raid_frame(user.raid_frame, 10000)
    outcome = gen.get_outcome_for_raid_frame(shiny_frame)
    pokemon = await storage_manager.get_raid_pokemon_master_by_id(outcome['pokemon_id'])
    return embed_generator.create_full_raid_shiny_frame(user=user, shiny_frame=shiny_frame, pokemon_name=pokemon.name, pokemon_url=pokemon.front_shiny_sprite)

async def reset_seeds(user):
    item = await storage_manager.get_user_item_by_name(user, 'resetseed')
    if item.quantity >= 1:
        user.reset_seeds()
        user.shiny_frame = -1
        user.frame = 1
        user.raid_frame = 1
        item.quantity = item.quantity - 1
        item.uses = item.uses + 1
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_reset_seeds_embed(user)
    else:
        return embed_generator.create_item_failure_embed(user, 'resetseed')

async def skip_frames(user, quantity):
    num_skip_frames = 100
    item = await storage_manager.get_user_item_by_name(user, 'skipframe')
    if item.quantity >= quantity:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_shiny_frame(user=user, start_frame=user.frame+1, max_frames_to_check=10000)
        frames_skipped = 0
        quantity_used = 0
        for i in range(quantity):
            if shiny_frame and user.frame + num_skip_frames >= shiny_frame:
                user.frame = shiny_frame
                skipped_to_shiny = True
                quantity_used += 1
                break 
            else:
                skipped_to_shiny = False
                user.frame += num_skip_frames
                frames_skipped += num_skip_frames
                quantity_used += 1
        item.quantity = item.quantity - quantity_used
        item.uses = item.uses + quantity_used
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        if skipped_to_shiny:
            return embed_generator.create_skip_to_shiny_embed(user)
        else:
            return embed_generator.create_skip_frames_embed(user, num_frames=frames_skipped)
    else:
        return embed_generator.create_item_failure_embed(user, 'skipframe') 
       
async def skip_raid_frames(user, quantity):
    num_skip_frames = 15
    item = await storage_manager.get_user_item_by_name(user, 'skipraidframe')
    if item.quantity >= quantity:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_shiny_raid_frame(start_frame=user.raid_frame+1, max_frames_to_check=10000)
        frames_skipped = 0
        quantity_used = 0
        for i in range(quantity):
            if shiny_frame and user.raid_frame + num_skip_frames >= shiny_frame:
                user.raid_frame = shiny_frame
                skipped_to_shiny = True
                quantity_used += 1
                break 
            else:
                skipped_to_shiny = False
                user.raid_frame += num_skip_frames
                frames_skipped += num_skip_frames
                quantity_used += 1
        item.quantity = item.quantity - quantity_used
        item.uses = item.uses + quantity_used
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        if skipped_to_shiny:
            return embed_generator.create_skip_to_shiny_raid_embed(user)
        else:
            return embed_generator.create_skip_raid_frames_embed(user, num_frames=frames_skipped)
    else:
        return embed_generator.create_item_failure_embed(user, 'skipraidframe') 
    
async def reroll_iv(user, iv):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot use rerolliv while in a trade")
    if iv not in ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']:
        return embed_generator.create_item_failure_embed(user, 'rerolliv') 
    item = await storage_manager.get_user_item_by_name(user, 'rerolliv')
    if item.quantity >= 1:
        buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        try:
            buddy.iv[iv] = random.randrange(0,32)
            item.quantity = item.quantity - 1
            item.uses = item.uses + 1
            await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
            await storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"])
        except:
            return embed_generator.create_item_failure_embed(user, 'rerolliv')  
        return embed_generator.create_rerolliv_view(user, buddy, iv)
    else:
        return embed_generator.create_item_failure_embed(user, 'rerolliv')  

async def reroll_nature(user):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot use rerollnature while in a trade")
    item = await storage_manager.get_user_item_by_name(user, 'rerollnature')
    if item.quantity >= 1:
        buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        try:
            buddy.nature  = random.choice(["Hardy","Docile","Serious","Bashful","Quirky" ,"Lonely","Brave","Adamant","Naughty" ,"Bold","Relaxed","Impish","Lax" ,"Modest","Mild","Quiet","Rash" ,"Calm","Gentle","Sassy","Careful" ,"Timid","Hasty","Jolly","Naive"])
            item.quantity = item.quantity - 1
            item.uses = item.uses + 1
            await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
            await storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"])
        except:
            return embed_generator.create_item_failure_embed(user, 'rerollnature')  
        return embed_generator.create_rerollnature_view(user, buddy)
    else:
        return embed_generator.create_item_failure_embed(user, 'rerollnature')  

async def rare_candy(user, quantity):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_block_embed(user, "Cannot use rare candy while in a trade")
    item = await storage_manager.get_user_item_by_name(user, 'rarecandy')
    print(item)
    if item.quantity >= quantity:
        buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        try:
            for i in range(quantity):
                if buddy.level < 100:
                    buddy.exp += buddy.next_exp
                    buddy.level_up()
                    item.quantity = item.quantity - 1
                    item.uses = item.uses + 1
                else:
                    return embed_generator.create_rare_candy_fail_view(user, buddy)
            await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
            await storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"])
        except:
            return embed_generator.create_item_failure_embed(user, 'rarecandy')  
        return embed_generator.create_rare_candy_view(user, buddy, quantity)
    else:
        return embed_generator.create_item_failure_embed(user, 'rarecandy')  

async def raid_shiny_frame(user):
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_raid_frame = gen.find_shiny_raid_frame(start_frame=user.raid_frame+1, max_frames_to_check=10000)
        if shiny_raid_frame:
            outcome = gen.get_outcome_for_raid_frame(shiny_raid_frame)
            print(outcome)        
            return embed_generator.create_raid_shiny_frame(user=user, shiny_frame=shiny_raid_frame)
        else:
            return embed_generator.create_raid_shiny_frame(user=user, shiny_frame="No shiny found")  

async def region_pass(user, region):
    regions = ["kanto", "johto","hoenn","sinnoh", "unova", "kalos", "alola", "galar", "paldea"]
    
    if not region or region.lower() == 'none':
        user.region = ''
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_region_view(user, "no region")
    if not (region.lower() in regions):
        return embed_generator.create_region_failure_view(user, "no valid region found!")

    active_battle = await storage_manager.get_battle_by_user(user.id)
    if active_battle:
        return embed_generator.create_region_failure_view(user, "you are currently in a battle!")
    item = await storage_manager.get_user_item_by_name(user, 'regionpass')
    if item.quantity >= 1:
        try:
            item.quantity -= 1
            user.region = region
            await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        except:
            return embed_generator.create_item_failure_embed(user, 'regionpass')  
        return embed_generator.create_region_view(user, region)
    else:
        return embed_generator.create_item_failure_embed(user, 'regionpass')     
     
   
async def get_items(user):
    user_items = await storage_manager.get_user_items(user)
    return embed_generator.create_items_view_table(user, user_items)

#######################Event methods#######################
async def toggle_event(user):
    if user.event:
        user.event = False
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_left_event_embed(user)
    else:
        user.event = True
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_joined_event_embed(user)

async def get_event_details(user):
    return embed_generator.create_event_embed(user)

async def full_event_shiny_frame(user):
    if user.event:
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed)
        shiny_frame = gen.find_event_shiny_frame(user=user,start_frame=user.frame+1, max_frames_to_check=10000)
        if shiny_frame:
            user.shiny_frame = shiny_frame
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])        
            if user.full_frame:
                pokemon = await get_pokemon_for_shiny_frame(user, user.shiny_frame)
                return embed_generator.create_full_shiny_frame(user, user.shiny_frame, pokemon.name, pokemon.front_shiny_sprite)
            else:
                return embed_generator.create_shiny_frame(user=user, shiny_frame=shiny_frame)
        else:
            return embed_generator.create_shiny_frame(user=user, shiny_frame="No shiny found")
    else:
        return embed_generator.create_not_in_event_embed(user)

#######################Battle methods#######################
async def admin_start_battle(pokedex_id, is_shiny, user, channel_id):
    print(is_shiny)
    active_battle = await storage_manager.get_battle_by_user(user.id)
    if active_battle:
        logger.info('User in battle already')
        return None, embed_generator.create_already_in_battle_embed(user=user)
    
    logger.info(f"Battle Started for: {user.id}")
    user.frame = user.frame + 1 
    level = 1
    pokemon_data = await storage_manager.get_pokemon_master_by_id(pokedex_id)
    safe = False
    if is_shiny:
        safe = True
        front_sprite = pokemon_data.front_shiny_sprite
    else:
        front_sprite = pokemon_data.front_default_sprite
    if pokemon_data.tier == 4:
        safe = True
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
    new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=is_shiny, tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = level, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json, safe=safe)
    #set embed_color
    color = embed_generator.get_color(new_pokemon)
    
    #save user
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
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
    await storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}battle_pokemon_id:{new_pokemon.id}", table_name="battle_pokemon", unique_columns=["id"])
    #write battle to table
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name="battles", unique_columns=["id"])
    return new_pokemon, embed_generator.create_battle_embed(user_name=user.name, pokemon_name=new_pokemon.name, join_code=battle.local_id,duration=battle.duration, color=color, url=front_sprite)

async def start_battle(user, channel_id):
    active_battle = await storage_manager.get_battle_by_user(user.id)
    if active_battle:
        logger.info('User in battle already')
        return None, embed_generator.create_already_in_battle_embed(user=user)
    
    logger.info(f"Battle Started for: {user.id}")
    gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed) 
    outcome = gen.get_outcome_for_frame(user.frame, user)
    user.frame = user.frame + 1 
    safe = False
    #logger.info(outcome)
    level = 1
    pokemon_data = await storage_manager.get_pokemon_master_by_id(outcome['pokemon_id'])
    if outcome['is_shiny']:
        safe = True
        user.shiny_frame = -1
        front_sprite = pokemon_data.front_shiny_sprite
    else:
        front_sprite = pokemon_data.front_default_sprite

    if pokemon_data.tier == 4:
        safe = True

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
    new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=outcome['is_shiny'], tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = level, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json, safe = safe)
    #set embed_color
    color = embed_generator.get_color(new_pokemon)
    
    #save user
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    #calculate duration
    duration = 10 * int(new_pokemon.tier) + random.randrange(0,16) 
    start_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=duration)
    end_time = start_time + delta
    logger.debug(f"battle end_time: {end_time}")
    #calculate rewards, for now just money
    rewards = {'money': 200*new_pokemon.tier, 'exp': int(pokemon_data.base_experience)}
    battle = Battle(id=uuid.uuid4(), user_ids=[user.id], local_id=random.randrange(100,1000), channel_id=channel_id, start_time=start_time, duration=duration, end_time=end_time, rewards=rewards, status='active', battle_pokemon_id=new_pokemon.id)
    #write new pokemon to battle_pokemon table
    await storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}battle_pokemon_id:{new_pokemon.id}", table_name="battle_pokemon", unique_columns=["id"])
    #write battle to table
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}battle_id:{battle.id}", table_name="battles", unique_columns=["id"])
    return new_pokemon, embed_generator.create_battle_embed(user_name=user.name, pokemon_name=new_pokemon.name, join_code=battle.local_id,duration=battle.duration, color=color, url=front_sprite)

async def process_expired_battle(battle: List[Battle]):
    """
    Asynchronously processes a single expired battle.
    """
    logger.info(f"Processing expired battle: {battle.id} for user(s) {battle.user_ids}")

    try:
        pokemon = await storage_manager.get_battle_pokemon_by_id(str(battle.battle_pokemon_id))
        for user_id in battle.user_ids:
            pokemon.id = str(uuid.uuid4())
            pokemon.user_id = user_id
            pokemon.random_on_catch()
            user = await storage_manager.get_user(user_id=user_id)
            reward = int(battle.rewards['money'])
            if user.current_pokemon:
                buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
                if buddy:
                    if buddy.level < 100:
                        buddy.exp = int(int(buddy.exp) + int((battle.rewards['exp'] * buddy.level)/4))
                    elif buddy.level == 100:
                        reward = math.floor(reward * 1.5)
                    num_levels = buddy.level_up()
                    if num_levels > 0:
                        reward = reward + (num_levels * 500)
                        channel = await client.fetch_channel(battle.channel_id)
                        embed = embed_generator.create_level_up_embed(user = user, levels=num_levels, buddy= buddy, reward=(num_levels * 500))
                        await channel.send(embed=embed)
                    await storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"])
            user.wallet = int(user.wallet) + int(reward)
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
            
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
            logger.error(msg=f"Unhandled error in battle_monitor_task: {e}", exc_info=True)
            # Implement more robust error handling, perhaps back-off and retry

        # 4. Wait for the next interval
        await asyncio.sleep(interval_seconds)

async def join_battle(user, local_id, channel_id):
    active_battle = await storage_manager.get_battle_by_user(user.id)
    if active_battle:
        logger.info('User in battle already')
        return embed_generator.create_already_in_battle_embed(user=user)
    #get battle
    battle = await storage_manager.get_battle_by_local_channel(local_id=local_id, channel_id=channel_id)
    #add user to user_ids
    if battle and user.id in battle.user_ids:
        return embed_generator.create_already_in_battle_embed(user=user)
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
    return embed_generator.create_join_battle_embed(user=user, new_duration=duration)
    
async def run_battle(user):
    #get battle that user is in
    battle = await storage_manager.get_battle_by_user(user.id)
    if battle.status == 'joined':
        return embed_generator.create_run_from_battle_fail_embed(user)
    #delete active battle
    if user.id in battle.user_ids:
        await storage_manager.delete_battle_by_id(battle.id)
        #reset user frame
        user.frame -= 1
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        return embed_generator.create_run_from_battle_embed(user=user)
############################################################

async def start_trainer_battle(user: User):
    #pick trainer
    trainer_sprite = Sprites.get_random_sprite()
    #pick pokemon
    trainer_user = User(id = 36135, discord_username="test", region=user.region, frame=random.randrange(1, 5000), event=False)
    gen = Generator(trainer_user.tier_seed, trainer_user.type_seed, trainer_user.pokemon_seed, trainer_user.shiny_seed, trainer_user.item_seed)
    outcome = gen.get_outcome_for_frame(trainer_user.frame, trainer_user)
    safe = False
    #logger.info(outcome)
    level = 1
    pokemon_data = await storage_manager.get_pokemon_master_by_id(outcome['pokemon_id'])
    front_sprite = f"https://raw.githubusercontent.com/ultra-move/goomybot-v3/refs/heads/prod/sprites/whois/{outcome['pokemon_id']}.png"

    if pokemon_data.tier == 4:
        safe = True

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
    new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=outcome['is_shiny'], tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = level, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json, safe = safe)
    print(new_pokemon)

    #save pokemon to table
    #pick conditions
    tb = trainer_battle.TrainerBattle()
    conditions = tb.randomize_conditions(new_pokemon.tier)

    #pick bonus timer
    if new_pokemon.tier == 1:
        bonus_duration = 20
    if new_pokemon.tier == 2:
        bonus_duration = 45
    if new_pokemon.tier == 3:
        bonus_duration = 90
    if new_pokemon.tier == 4:
        bonus_duration = 120

    return embed_generator.create_trainer_battle_embed(user_name=user.name, pokemon=new_pokemon, trainer_name="Test", trainer_sprite=trainer_sprite, conditions=conditions, bonus_duration=bonus_duration)


#######################Raid methods#######################
async def admin_start_raid(pokedex_id, is_shiny, user, channel_id):
    item = await storage_manager.get_user_item_by_name(user, 'raidpass')
    active_raid = await storage_manager.get_raid_by_user(user.id)
    if active_raid:
        logger.info('User in raid already')
        return None, embed_generator.create_already_in_raid_embed(user_name=user.name)
    safe = False
    pokemon_data = await storage_manager.get_raid_pokemon_master_by_id(pokedex_id)
    if is_shiny:
        safe = True
        front_sprite = pokemon_data.front_shiny_sprite
    else:
        front_sprite = pokemon_data.front_default_sprite

    if pokemon_data.tier == 4:
        safe = False
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
    new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=is_shiny, tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = 1, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json, safe=safe)
    #set embed_color
    color = embed_generator.get_color(new_pokemon)
    
    #save user
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
    #calculate duration
    duration = 100 * int(new_pokemon.tier) + random.randrange(0,61) 
    start_time = datetime.now(timezone.utc)
    delta = timedelta(seconds=duration)
    end_time = start_time + delta
    logger.debug(f"battle end_time: {end_time}")
    #calculate rewards, for now just money
    rewards = {'money': 1000*new_pokemon.tier, 'exp': int(pokemon_data.base_experience)}
    raid = Battle(id=uuid.uuid4(), user_ids=[user.id], local_id=random.randrange(100,1000), channel_id=channel_id, start_time=start_time, duration=duration, end_time=end_time, rewards=rewards, status='active', battle_pokemon_id=new_pokemon.id)
    #write new pokemon to raid_pokemon table
    await storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}raid_pokemon_id:{new_pokemon.id}", table_name="raid_pokemon", unique_columns=["id"])
    #write battle to table
    await storage_manager.save_object(obj=raid, cache_key=f"{REDIS_PREFIX}raid_id:{raid.id}", table_name="raids", unique_columns=["id"])
    return new_pokemon, embed_generator.create_raid_embed(user_name=user.name, pokemon_name=new_pokemon.name, join_code=raid.local_id,duration=raid.duration, color=color, url=front_sprite)


async def start_raid(user, channel_id):
    item = await storage_manager.get_user_item_by_name(user, 'raidpass')
    active_raid = await storage_manager.get_raid_by_user(user.id)
    if active_raid:
        logger.info('User in raid already')
        return None, embed_generator.create_already_in_raid_embed(user_name=user.name)
    if item and item.quantity >= 1:
        item.quantity = item.quantity - 1 
        await storage_manager.save_object(obj=item, cache_key=f"{REDIS_PREFIX}item_id:{item.id}", table_name='user_items', unique_columns=['id'])

        logger.info(f"active_raid Started for: {user.id}")
        gen = Generator(tier_seed=user.tier_seed, type_seed=user.type_seed, pokemon_seed=user.pokemon_seed, shiny_seed=user.shiny_seed, item_seed=user.item_seed) 
        outcome = gen.get_outcome_for_raid_frame(user.raid_frame)
        user.raid_frame = user.raid_frame + 1 
        #logger.info(outcome)
        safe = False
        pokemon_data = await storage_manager.get_raid_pokemon_master_by_id(outcome['pokemon_id'])
        if outcome['is_shiny']:
            safe = True
            front_sprite = pokemon_data.front_shiny_sprite
        else:
            front_sprite = pokemon_data.front_default_sprite

        if pokemon_data.tier == 4:
            safe = False
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
        new_pokemon = Pokemon(id=uuid.uuid4(), user_id=user.id, original_user_id=user.id, pokedex_id=pokemon_data.id, name=pokemon_data.name, is_shiny=outcome['is_shiny'], tier = pokemon_data.tier, types=pokemon_data.types_names, ability=random.choice(pokemon_data.abilities_names), level = 1, growth_rate = pokemon_data.growth_rate_name, exp=0, next_exp=0, sprite_front=front_sprite, sprite_back=pokemon_data.back_default_sprite, region=pokemon_data.region, iv=iv, ev=ev, base_stats=pokemon_data.base_stats_json, safe=safe)
        #set embed_color
        color = embed_generator.get_color(new_pokemon)
        
        #save user
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
        #calculate duration
        duration = 100 * int(new_pokemon.tier) + random.randrange(0,61) 
        start_time = datetime.now(timezone.utc)
        delta = timedelta(seconds=duration)
        end_time = start_time + delta
        logger.debug(f"battle end_time: {end_time}")
        #calculate rewards, for now just money
        rewards = {'money': 1000*new_pokemon.tier, 'exp': int(pokemon_data.base_experience)}
        raid = Battle(id=uuid.uuid4(), user_ids=[user.id], local_id=random.randrange(100,1000), channel_id=channel_id, start_time=start_time, duration=duration, end_time=end_time, rewards=rewards, status='active', battle_pokemon_id=new_pokemon.id)
        #write new pokemon to raid_pokemon table
        await storage_manager.save_object(obj=new_pokemon, cache_key=f"{REDIS_PREFIX}raid_pokemon_id:{new_pokemon.id}", table_name="raid_pokemon", unique_columns=["id"])
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
            reward = int(battle.rewards['money'])
            if user.current_pokemon:
                buddy = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
                if buddy:
                    if buddy.level < 100:
                        buddy.exp = int(int(buddy.exp) + int((5 * battle.rewards['exp'] * buddy.level)/4))
                    elif buddy.level == 100:
                        reward = math.floor(reward * 1.5)
                    num_levels = buddy.level_up()
                    if num_levels > 0:
                        reward = reward + (num_levels * 500)
                        channel = await client.fetch_channel(battle.channel_id)
                        embed = embed_generator.create_level_up_embed(user = user, levels=num_levels, buddy= buddy, reward=(num_levels * 500))
                        await channel.send(embed=embed)
                    await storage_manager.save_object(obj=buddy, cache_key=f"{REDIS_PREFIX}pokemon_data:{buddy.id}", table_name="user_pokemon", unique_columns=["id"])
            user.wallet = int(user.wallet) + int(reward)
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])

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
    active_battle = await storage_manager.get_raid_by_user(user.id)
    if active_battle:
        logger.info('User in raid already')
        return None, embed_generator.create_already_in_raid_embed(user_name=user.name)
    #get battle
    battle = await storage_manager.get_raid_by_local_channel(local_id=local_id, channel_id=channel_id)
    #add user to user_ids
    if battle and user.id in battle.user_ids:
        return embed_generator.create_already_in_raid_embed(user_name=user.name)
    battle.user_ids.append(user.id)
    time_until_end = battle.end_time - datetime.now(timezone.utc)
    battle.status = 'joined'
    #save battle
    await storage_manager.save_object(obj=battle, cache_key=f"{REDIS_PREFIX}raid_id:{battle.id}", table_name="raids", unique_columns=["id"])
    return embed_generator.create_join_raid_embed(user=user, new_duration=time_until_end.seconds)

#######################Lottery methods#######################

async def enter_lottery(user):
    lottery_entry_fee = 10000
    lottery = await storage_manager.get_active_lottery()
    if lottery and user.id in lottery.user_ids:
        print('user in lottery')
        return embed_generator.create_lottery_embed(user=user, content=f"Current Jackpot: ${lottery.amount:,.0f}\nEnd time: {lottery.end_time.strftime('%Y-%m-%d %H:%M')} (UTC)\n")
    elif user.wallet >= lottery_entry_fee:
        print('entering user in lottery')
        user.wallet -= lottery_entry_fee
        lottery.user_ids.append(user.id)
        lottery.amount += lottery_entry_fee
        await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"]) 
        await storage_manager.save_object(obj=lottery, cache_key=f"{REDIS_PREFIX}lottery_id:{lottery.id}", table_name="lottery", unique_columns=["id"]) 
        return embed_generator.create_lottery_embed(user=user, content=f"Successfully entered lottery!\nCurrent Jackpot: ${lottery.amount:,.0f}\nEnd time: {lottery.end_time.strftime('%Y-%m-%d %H:%M')} (UTC)\n")
    else:
        return embed_generator.create_lottery_embed(user=user, content=f"Could not enter lottery due to insufficient funds\nCost:${lottery_entry_fee:,.0f}\nCurrent Jackpot: ${lottery.amount:,.0f}\nEnd time: {lottery.end_time.strftime('%Y-%m-%d %H:%M')} (UTC)\n")

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
        
        active_lottery = await storage_manager.get_active_lottery()
        if not active_lottery:
            print('no active lottery, creating one')
            duration = 24
            start_time = datetime.now(timezone.utc)
            delta = timedelta(hours=duration)
            end_time = start_time + delta
            new_lottery = Lottery(id=uuid.uuid4(), user_ids=[], start_time=start_time,end_time=end_time, amount=60000)
            await storage_manager.save_object(obj=new_lottery, cache_key=f"{REDIS_PREFIX}lottery_id:{new_lottery.id}", table_name="lottery", unique_columns=["id"]) 

        # 4. Wait for the next interval
        await asyncio.sleep(interval_seconds)


#####################trade functions##############################

async def start_trade(user, mention):
    print(f"Trade starting with: {mention}")
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade:
        return embed_generator.create_trade_already_active_embed(user)
    user_mentioned = await storage_manager.get_user(user_id=mention.id)
    if user_mentioned:
        active_trade = await storage_manager.get_trade_by_user_id(user_id=user_mentioned.id)
        if active_trade:
            return embed_generator.create_trade_already_mentioned_active_embed(user, user_mentioned=user_mentioned)
        user1={'user_id': user.id, 'pokemon': [], 'items': [{'id': '', 'name': '', 'quantity': 0}], 'money': 0, 'confirmed': False}        
        user2= {'user_id': user_mentioned.id, 'pokemon': [], 'items': [{'id': '', 'name': '', 'quantity': 0}], 'money': 0, 'confirmed': False}
        local_id = random.randrange(100,999)
        trade = Trade(id=uuid.uuid4(), local_id=local_id, user1=user1, user2=user2, status='started')
        await storage_manager.save_object(obj= trade, cache_key=f"{REDIS_PREFIX}trade_id_{trade.id}", table_name='trades', unique_columns=['id'])
        #trade = await storage_manager.get_trade_by_user_id(user_id=message.author.id)
        #print(trade)
        return embed_generator.create_trade_started_embed(user=user, user_mentioned=user_mentioned, local_id=local_id)
    else:
        return embed_generator.create_trade_invalid_user_embed(user=user)

async def join_trade(user, local_id):
    active_trade = await storage_manager.get_trade_by_user_id_local_id(user_id=user.id, local_id=local_id)
    if active_trade:
        #print(active_trade)
        active_trade.status = 'active'
        await storage_manager.save_object(obj= active_trade, cache_key=f"{REDIS_PREFIX}trade_id_{active_trade.id}", table_name='trades', unique_columns=['id'])
        return embed_generator.create_join_trade_success_embed(user=user)
    else:
        return embed_generator.create_join_trade_failure_embed(user)
    
async def add_pokemon_to_trade(user, local_id):
    active_trade = await storage_manager.get_trade_by_user_id_active(user_id=user.id)
    if active_trade:
        pokemon_id = user.view_table[local_id]['id']
        pokemon = await storage_manager.get_user_pokemon_by_id(pokemon_id)

        # Determine if the Pokémon is shiny for naming
        name = user.view_table[local_id]['name'].capitalize()

        # Check if the Pokémon is the user's current buddy
        if str(pokemon_id) == str(user.current_pokemon):
            return embed_generator.create_trade_add_failure_embed(user, reason="Cannot trade your buddy Pokémon!")

        # Determine which user's trade slot to check/add to
        user_trade_data = active_trade.user1 if active_trade.user1['user_id'] == user.id else active_trade.user2

        # Check if the Pokémon is already in the trade
        for traded_pokemon in user_trade_data['pokemon']:
            if str(traded_pokemon['id']) == str(pokemon_id):
                return embed_generator.create_trade_add_failure_embed(user, reason="This Pokémon is already in the trade!")

        # If not already in trade and not buddy, add the Pokémon
        user_trade_data['pokemon'].append({"id": pokemon_id, 'name': name})
        await storage_manager.save_object(obj=active_trade, cache_key=f"{REDIS_PREFIX}trade_id_{active_trade.id}", table_name='trades', unique_columns=['id'])

        return embed_generator.create_trade_add_pokemon_embed(user, pokemon)
    else:
        return embed_generator.create_trade_add_failure_embed(user, reason="No active trade!")


async def add_money_to_trade(user, amount):
    active_trade = await storage_manager.get_trade_by_user_id_active(user_id=user.id)
    #print(active_trade)
    if active_trade:
        if user.wallet >= amount and amount > 0:
            user.wallet = user.wallet - amount
            if active_trade.user1['user_id'] == user.id:
                active_trade.user1['money'] += amount
            else:
                active_trade.user2['money'] += amount
        
            await storage_manager.save_object(obj= active_trade, cache_key=f"{REDIS_PREFIX}trade_id_{active_trade.id}", table_name='trades', unique_columns=['id'])
            await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])
            return embed_generator.create_trade_add_money_embed(user, amount)
        else:
            return embed_generator.create_trade_add_money_failure_embed(user, amount)

async def add_item_to_trade(user, item_name, item_quantity):
    active_trade = await storage_manager.get_trade_by_user_id_active(user_id=user.id)
    if active_trade:
        item: Item = await storage_manager.get_user_item_by_name(user=user, item_name=item_name)
        if item:
            user_trade_data = active_trade.user1 if active_trade.user1['user_id'] == user.id else active_trade.user2
            trade_index = None
            for index, i in enumerate(user_trade_data['items']):
                if i['name'] == item_name:
                    trade_index = index
                    break
            if item.quantity >= item_quantity and item_quantity > 0:
                # Determine which user's trade slot to check/add to
                if trade_index:
                    user_trade_data['items'][trade_index] = {"name": item_name, "quantity": item_quantity}
                else:   
                    user_trade_data['items'].append({"name": item_name, 'quantity': item_quantity})
                await storage_manager.save_object(obj=active_trade, cache_key=f"{REDIS_PREFIX}trade_id_{active_trade.id}", table_name='trades', unique_columns=['id'])
                return embed_generator.create_trade_add_item_embed(user, item_name, item_quantity)
            else:
                return embed_generator.create_trade_add_failure_embed(user, reason=f"You do not own that many {item_name}! Please check quantity")
        else:
            return embed_generator.create_trade_add_failure_embed(user, reason=f"You do not own any {item_name}!")
    else:
        return embed_generator.create_trade_add_failure_embed(user, reason="No active trade!")


async def display_trade(user):
    active_trade = await storage_manager.get_trade_by_user_id_active(user_id=user.id)
    if active_trade:
        # Determine user names
        if user.id == active_trade.user1["user_id"]:
            user1_name = user.name
            user2 = await storage_manager.get_user(active_trade.user2["user_id"])
            user2_name = user2.name
        else:
            user2_name = user.name
            user1 = await storage_manager.get_user(active_trade.user1["user_id"])
            user1_name = user1.name

        # Prepare pokemon strings
        user1_pokemon_string = "\n".join([pokemon['name'] for pokemon in active_trade.user1['pokemon']])
        user2_pokemon_string = "\n".join([pokemon['name'] for pokemon in active_trade.user2['pokemon']])

        user1_item_string = "\n".join([
            f"{item['name']} x{item['quantity']}"
            for item in active_trade.user1['items']
            if item.get('name') and item.get('quantity', 0) > 0 # This condition is key!
        ])

        user2_item_string = "\n".join([
            f"{item['name']} x{item['quantity']}"
            for item in active_trade.user2['items']
            if item.get('name') and item.get('quantity', 0) > 0
        ])
        # Format confirmation status
        user1_confirmed = "Yes" if active_trade.user1['confirmed'] else "No"
        user2_confirmed = "Yes" if active_trade.user2['confirmed'] else "No"

        # Prepare money strings
        user1_money_string = f"\nMoney: ${active_trade.user1['money']:,.0f}" if active_trade.user1['money'] != 0 else ""
        user2_money_string = f"\nMoney: ${active_trade.user2['money']:,.0f}" if active_trade.user2['money'] != 0 else ""

        # Construct the display string
        display_string = f"""
**Trade ID:** {active_trade.local_id}

**{user1_name}**
Confirmed: {user1_confirmed}
Offered:
{user1_pokemon_string if user1_pokemon_string else ""}{user1_item_string if user1_item_string else ""}{user1_money_string}

---

**{user2_name}**
Confirmed: {user2_confirmed}
Offered:
{user2_pokemon_string if user2_pokemon_string else ""}{user2_item_string if user2_item_string else ""}{user2_money_string}
"""
        return embed_generator.create_trade_display_embed(user, display_string, user1_name, user2_name)
    else:
        return embed_generator.create_trade_add_failure_embed(user, reason="No active trade!")
       

async def confirm_trade(user):
    active_trade = await storage_manager.get_trade_by_user_id_active(user_id=user.id)
    if active_trade:
        if user.id == active_trade.user1["user_id"]:
            active_trade.user1['confirmed'] = True
        if user.id == active_trade.user2["user_id"]:
            active_trade.user2['confirmed'] = True
        
        if active_trade.user1['confirmed'] == active_trade.user2['confirmed']:
            await finish_trade(active_trade)
            await storage_manager.delete_trade_id(active_trade.id)
            return embed_generator.create_trade_completed_embed(active_trade=active_trade)
        else:
            await storage_manager.save_object(obj= active_trade, cache_key=f"{REDIS_PREFIX}trade_id_{active_trade.id}", table_name='trades', unique_columns=['id'])
            return await display_trade(user)
    else:
        return embed_generator.create_trade_add_failure_embed(user, reason="No active trade!")     

async def finish_trade(active_trade):
    user1 = await storage_manager.get_user(user_id=active_trade.user1['user_id'])
    user2 = await storage_manager.get_user(user_id=active_trade.user2['user_id'])
    for pokemon in active_trade.user1['pokemon']:
        pokemon_data = await storage_manager.get_user_pokemon_by_id(pokemon_id=pokemon['id'])
        pokemon_data.user_id = active_trade.user2['user_id']
        pokemon_data.created_at = datetime.now(timezone.utc)
        pokemon_data.original_user_id = active_trade.user1['user_id']
        await storage_manager.save_object(obj=pokemon_data, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon_data.id}", table_name='user_pokemon', unique_columns=['id'])
    for pokemon in active_trade.user2['pokemon']:
        pokemon_data = await storage_manager.get_user_pokemon_by_id(pokemon_id=pokemon['id'])
        pokemon_data.user_id = active_trade.user1['user_id']
        pokemon_data.created_at = datetime.now(timezone.utc)
        pokemon_data.original_user_id = active_trade.user2['user_id']
        await storage_manager.save_object(obj=pokemon_data, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon_data.id}", table_name='user_pokemon', unique_columns=['id'])
    
    for item in active_trade.user1['items']:
        print(active_trade)
        user1_item_data = await storage_manager.get_user_item_by_name(user=user1, item_name=item['name'])
        user2_item_data = await storage_manager.get_user_item_by_name(user=user2, item_name=item['name'])
        if user2_item_data:
            user2_item_data.quantity += item['quantity']
        else:
            user2_item_data = Item(id=uuid.uuid4(), user_id=user2.id, name=item['name'], quantity=item['quantity'], uses=0)
        user1_item_data.quantity = user1_item_data.quantity - item['quantity']
        await storage_manager.save_object(obj=user1_item_data, cache_key=f"{REDIS_PREFIX}item_id:{user1_item_data.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user2_item_data, cache_key=f"{REDIS_PREFIX}item_id:{user2_item_data.id}", table_name='user_items', unique_columns=['id'])
    for item in active_trade.user2['items']:
        user1_item_data = await storage_manager.get_user_item_by_name(user=user1, item_name=item['name'])
        user2_item_data = await storage_manager.get_user_item_by_name(user=user2, item_name=item['name'])
        if user1_item_data:
            user1_item_data.quantity += item['quantity']
        else:
            user1_item_data = Item(id=uuid.uuid4(), user_id=user1.id, name=item['name'], quantity=item['quantity'], uses=0)
        user2_item_data.quantity = user2_item_data.quantity - item['quantity']
        await storage_manager.save_object(obj=user1_item_data, cache_key=f"{REDIS_PREFIX}item_id:{user1_item_data.id}", table_name='user_items', unique_columns=['id'])
        await storage_manager.save_object(obj=user2_item_data, cache_key=f"{REDIS_PREFIX}item_id:{user2_item_data.id}", table_name='user_items', unique_columns=['id'])

    if active_trade.user1['money'] > 0:
        
        user2.wallet += active_trade.user1['money']
        await storage_manager.save_object(obj=user2, cache_key=f"{REDIS_PREFIX}user_id:{user2.id}", table_name="users", unique_columns=["id"])
    if active_trade.user2['money'] > 0:

        user1.wallet += active_trade.user2['money']
        await storage_manager.save_object(obj=user1, cache_key=f"{REDIS_PREFIX}user_id:{user1.id}", table_name="users", unique_columns=["id"])

async def cancel_trade(user):
    active_trade = await storage_manager.get_trade_by_user_id(user_id=user.id)
    if active_trade.user1['money'] > 0:
        user1 = await storage_manager.get_user(user_id=active_trade.user1['user_id'])
        user1.wallet += active_trade.user1['money']
        await storage_manager.save_object(obj=user1, cache_key=f"{REDIS_PREFIX}user_id:{user1.id}", table_name="users", unique_columns=["id"])
    if active_trade.user2['money'] > 0:
        user2 = await storage_manager.get_user(user_id=active_trade.user2['user_id'])
        user2.wallet += active_trade.user2['money']
        await storage_manager.save_object(obj=user2, cache_key=f"{REDIS_PREFIX}user_id:{user2.id}", table_name="users", unique_columns=["id"])

    await storage_manager.delete_trade_id(active_trade.id)
    return embed_generator.create_trade_canceled_embed(user)


########################Global stats#########################
async def get_leaderboard():
    leaderboard_results = await storage_manager.get_leaderboard_stats()
    return embed_generator.create_leaderboard_embed(leaderboard_results)

########################Quests#########################
async def quest(user):
    active_quest = await storage_manager.get_active_quest(user.id)
    if active_quest:
        if active_quest.status == 'active':
            complete = await storage_manager.get_quest_complete(user.id, active_quest)
            pokemon = await storage_manager.get_pokemon_master_by_id(active_quest.condition['pokedex_id'])
            print(complete)
            if complete:
                await quest_reward(user, active_quest)
                active_quest.status = 'complete'
                await storage_manager.save_object(obj=active_quest, cache_key=f"{REDIS_PREFIX}quest_id:{active_quest.id}", table_name='quests', unique_columns=['id'])
                #quest complete embed!
                return embed_generator.create_quest_complete(user, pokemon, active_quest)
            else:
                return embed_generator.create_quest_embed(user, pokemon, active_quest)
        else:
            #quest already completed!
            pokemon = await storage_manager.get_pokemon_master_by_id(active_quest.condition['pokedex_id'])
            return embed_generator.create_quest_already_complete(user, pokemon, active_quest)
    else:
        pokemon, quest = await quest_start(user)
        await storage_manager.save_object(obj=quest, cache_key=f"{REDIS_PREFIX}quest_id:{quest.id}", table_name='quests', unique_columns=['id'])
        return embed_generator.create_quest_embed(user, pokemon, quest)


async def quest_start(user):
    quest = Quest(id=uuid.uuid4(), user_id = user.id)
    if user.region != '':
        quest.region_condition(user)
    else:
        quest.random_condition()
    quest.random_reward()
    pokemon = await storage_manager.get_pokemon_master_by_id(quest.condition['pokedex_id'])
    quest.name = f'{pokemon.name.capitalize()}'
    return pokemon, quest

async def quest_reward(user, quest):
    item_name = quest.reward['item']['name']
    user_items = await storage_manager.get_user_items(user)
    final_item = {}
    found = False
    for item in user_items:
        if item.name == item_name:
            found = True
            final_item = item
            item.quantity += quest.reward['item']['quantity']
    if not found:
        final_item = Item(id=uuid.uuid4(), user_id=user.id, name=item_name, quantity=quest.reward['item']['quantity'], uses=0)
    
    if quest.reward['money'] != 0:
        user.wallet += quest.reward['money']
    await storage_manager.save_object(obj=final_item, cache_key=f"{REDIS_PREFIX}item_id:{final_item.id}", table_name='user_items', unique_columns=['id'])
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])     

#Professor functions
async def professor_monitor_task(interval_seconds: int):
    """
    Background task to periodically check and send a new professor challenge

    Args:
        interval_seconds (int): How often to poll the database in seconds.
    """
    logger.info(f"Professor task started. Polling every {interval_seconds} seconds.")
    while True:
        #await storage_manager.delete_old_challenges()
        await start_challenge()

        # 4. Wait for the next interval
        await asyncio.sleep(interval_seconds) 

async def start_challenge():
    active_challenge = await storage_manager.get_active_professor(1)
    if active_challenge and active_challenge.start_time <= datetime.now(timezone.utc) - timedelta(minutes=30):
        await reset_challenge(None)
        await create_challenge()
    if not active_challenge:
        await create_challenge()

async def create_challenge():
    new_challenge = Professor(id=None, tier=None, conditions=None, reward=None, local_id=None, completed_by=None, start_time=None)
    new_challenge.start()
    embed = embed_generator.create_professor_view(new_challenge)
    await storage_manager.save_object(obj=new_challenge, cache_key=f"{REDIS_PREFIX}professor_id:{new_challenge.id}", table_name="professor_challenges", unique_columns=["id"])  
    channel: discord.VoiceChannel | discord.StageChannel | discord.ForumChannel | discord.TextChannel | discord.CategoryChannel | discord.Thread | PrivateChannel | None = await client.fetch_channel(PROFESSOR_ID)
    await channel.send(embed=embed)

async def challenge_reward(user, challenge, bonus, reduced_rewards, reduced_mult):
    item_name = challenge.reward['item']['name']
    user_items = await storage_manager.get_user_items(user)
    final_item = {}
    found = False
    for item in user_items:
        if item.name == item_name:
            found = True
            final_item = item
            final_quantity = challenge.reward['item']['quantity']
            if reduced_rewards:
                final_quantity = math.ceil(final_quantity / reduced_mult)
            if bonus:
               final_quantity = final_quantity * 2
            item.quantity += final_quantity
    if not found:
        final_quantity = challenge.reward['item']['quantity']
        if reduced_rewards:
            final_quantity = math.ceil(final_quantity / reduced_mult)
        if bonus:
            final_quantity = final_quantity * 2
        if bonus:
            final_item = Item(id=uuid.uuid4(), user_id=user.id, name=item_name, quantity=final_quantity, uses=0)
        else:
            final_item = Item(id=uuid.uuid4(), user_id=user.id, name=item_name, quantity=final_quantity, uses=0)
    
    
    if challenge.reward['money'] != 0:
        final_money = challenge.reward['money']
        if reduced_rewards:
            final_money = math.ceil(final_money / reduced_mult)
        if bonus:
            final_money= final_money * 2
        user.wallet += final_money

    await storage_manager.save_object(obj=final_item, cache_key=f"{REDIS_PREFIX}item_id:{final_item.id}", table_name='user_items', unique_columns=['id'])
    await storage_manager.save_object(obj=user, cache_key=f"{REDIS_PREFIX}user_id:{user.id}", table_name="users", unique_columns=["id"])     


async def challenge_professor(user, local_id):
    pokemon = await storage_manager.get_user_pokemon_by_id(user.view_table[str(local_id)]['id'])
    active_challenge = await storage_manager.get_active_professor(1)
    hours_4 = datetime.now(timezone.utc) - timedelta(hours=4)
    oldest_challenge = await storage_manager.get_recent_challenge_full_reward(user_id=user.id)
    recent_challenge = await storage_manager.get_recent_challenge(user_id=user.id, timestamp=hours_4)
    lockout_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    if recent_challenge and recent_challenge.completed_time >= lockout_time:
        return embed_generator.create_challenge_time_view(user, recent_challenge)
    
    reduced_rewards = False
    reduced_mult = 10
    if oldest_challenge and oldest_challenge.completed_time >= hours_4:
        reduced_rewards = True
        hours_1 = datetime.now(timezone.utc) - timedelta(hours=1)
        hours_2 = datetime.now(timezone.utc) - timedelta(hours=2)
        hours_3 = datetime.now(timezone.utc) - timedelta(hours=3)
        if oldest_challenge.completed_time <=  hours_1 and oldest_challenge.completed_time >= hours_2:
            reduced_mult = 8
        elif oldest_challenge.completed_time <= hours_2 and oldest_challenge.completed_time  >= hours_3:
            reduced_mult = 6  
        elif oldest_challenge.completed_time <= hours_3 and oldest_challenge.completed_time  >= hours_4:
            reduced_mult = 4  
    if active_challenge:
        requirements_met, bonus_met, fail_display = active_challenge.check_condition(pokemon)
        print(requirements_met)
        print(bonus_met)
        print(fail_display)
        if requirements_met:
            await challenge_reward(user=user, challenge=active_challenge, bonus=bonus_met, reduced_rewards=reduced_rewards, reduced_mult=reduced_mult)
            active_challenge.completed_by = user.id
            active_challenge.completed_time = datetime.now(timezone.utc)
            if not reduced_rewards:
                active_challenge.full_reward = True
            await storage_manager.save_object(obj=active_challenge, cache_key=f"{REDIS_PREFIX}professor_id:{active_challenge.id}", table_name="professor_challenges", unique_columns=["id"])  
            return embed_generator.create_challenge_complete_view(user, pokemon, active_challenge, bonus_met, reduced_rewards, reduced_mult)
        else:
            return embed_generator.create_challenge_failure_view(user, pokemon, active_challenge, fail_display)

async def challenge_info(user):
    hours_4 = datetime.now(timezone.utc) - timedelta(hours=4)
    completed_challenge = await storage_manager.get_recent_challenge_full_reward(user_id=user.id)
    if completed_challenge and completed_challenge.completed_time >= hours_4:
        full_rewards_time = completed_challenge.completed_time

        # Calculate 4 hours *from* the completed time
        four_hours_from_completion = full_rewards_time + timedelta(hours=4)

        # Get the current time in UTC
        current_time_utc = datetime.now(timezone.utc)

        # Calculate the time remaining until the 4-hour mark
        time_left = four_hours_from_completion - current_time_utc

        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        seconds = time_left.seconds % 60
        return embed_generator.create_challenge_time_left_view(user, f"{hours} hours, {minutes} minutes, {seconds} seconds.")
    else:
        return embed_generator.create_challenge_full_rewards_view(user)


async def reset_challenge(user):
    active_challenge = await storage_manager.get_active_professor(1)
    await storage_manager.delete_challenge_by_id(active_challenge.id)
    return embed_generator.create_admin_embed("Reset challenge")

############################move functions############################
async def load_moves():
    for i in range(917):
        #print(f"Move ID: {i+1}")
        move, learned_by = DataLoader.load_moves(i+1)
        await storage_manager.save_object(obj=move, cache_key=None, table_name="moves", unique_columns=["id"])
        await storage_manager.save_objects(objects=learned_by, cache_key_prefix=None, table_name="move_learned_by", unique_columns=["id"])

async def get_learnset(user, page):
    pokemon = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
    total_records, result = await storage_manager.get_learnset(pokemon_id= pokemon.pokedex_id, page=page, page_size=10)
    move_string = ""
    for record in result:
        #print(record)
        move_string = move_string + record['name'].capitalize() +"\n"
    return embed_generator.create_learnset_table(user, pokemon, move_string, page+1, total_records)

async def learn_move(user, slot, move_name):
    if slot < 5 and slot > 0:
        pokemon = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
        total_records, result = await storage_manager.get_learnset(pokemon_id= pokemon.pokedex_id, page=0, page_size=10000)
        
        check_list = []
        for r in result:
            check_list.append(r['name'])
        if move_name.lower() in check_list:
            pokemon.moves[slot-1] = move_name.lower()
        await storage_manager.save_object(obj=pokemon, cache_key=f"{REDIS_PREFIX}pokemon_data:{pokemon.id}", table_name='user_pokemon', unique_columns=['id'])
        move_string = ""
        for i, m in enumerate(pokemon.moves):
            move_string = move_string + f"{i+1}: {m.capitalize()}\n"
        return embed_generator.create_move_table(user, pokemon, move_string)
     
async def see_moves(user):
    pokemon = await storage_manager.get_user_pokemon_by_id(str(user.current_pokemon))
    move_string = ""
    if len(pokemon.moves) > 0:
        for i, m in enumerate(pokemon.moves):
            move_string = move_string + f"{i+1}: {m.capitalize()}\n"
    return embed_generator.create_move_table(user, pokemon, move_string) 

######################################################################
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

    # Check if a flag exists on the client indicating tasks have been started
    # or if the flag is False. Initialize it if it doesn't exist.
    if not hasattr(client, '_monitor_tasks_started') or not client._monitor_tasks_started:
        print("Starting background monitor tasks...")
        
        # Store the task objects as attributes on the client for potential cancellation/management later
        client.battle_monitor_task_instance = asyncio.create_task(battle_monitor_task(interval_seconds=10))
        client.raid_monitor_task_instance = asyncio.create_task(raid_monitor_task(interval_seconds=10))
        client.lottery_monitor_task_instance = asyncio.create_task(lottery_monitor_task(interval_seconds=600))
        client.professor_monitor_task_instance = asyncio.create_task(professor_monitor_task(interval_seconds=180))
        # Set the flag to True so tasks aren't started again
        client._monitor_tasks_started = True
    else:
        print("Background monitor tasks already running, skipping re-initialization.")

user_command_locks = {}

@client.event
async def on_message(message):
    start_time = time.time()

    channel_id = message.channel.id
    if message.author == client.user:
        return
    # 1. Get or create the lock for this user
    user_id = message.author.id
    if user_id not in user_command_locks:
        user_command_locks[user_id] = asyncio.Lock()

    # 2. Check if the lock is already held (another command by this user is running)
    if user_command_locks[user_id].locked():
        logger.info(f'User {user_id} is locked for command: {message.content}')
        return

    # 3. Acquire the lock and execute command
    message.content = message.content.lower()
    user = await storage_manager.get_user(message.author.id)

    async with user_command_locks[user_id]:
#######################General commands#######################
        if message.content.startswith('.help filter'):
            embed = get_help_filter()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help moves'):
            embed = get_help_moves()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help user'):
            embed = get_help_user()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help pokemon'):
            embed = get_help_pokemon()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help battle'):
            embed = get_help_battle()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help raid'):
            embed = get_help_raid()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help items'):
            embed = get_help_items()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help event'):
            embed = get_help_event()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help trade'):
            embed = get_help_trade()
            await message.channel.send(embed=embed)
        elif message.content.startswith('.help challenge'):
            embed = get_help_challenge()
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

        if message.content.startswith('.addraidframe') and user.id == 701062435678846998:
            split = message.content.split()
            user_id = split[1]
            amount = split[2]
            embed = await add_raid_frame(user_id, int(amount))
            await message.channel.send(embed=embed)

        if message.content.startswith('.removeraidframe') and user.id == 701062435678846998:
            split = message.content.split()
            user_id = split[1]
            amount = split[2]
            embed = await remove_raid_frame(user_id, int(amount))
            await message.channel.send(embed=embed)

        if message.content.startswith('.flush') and user.id == 701062435678846998:
            embed = await flush_all()
            await message.channel.send(embed=embed)



        if message.content.startswith('.resetodds') and user.id == 701062435678846998:
            embed = await odds_reset()
            await message.channel.send(embed=embed)

        if message.content.startswith('.adminspawn') and user.id == 701062435678846998:
            pokedex_id = int(message.content.split()[1])
            is_shiny = {"true": True, "false": False}.get(message.content.split()[2].lower(), False)
            pookemon, embed = await admin_start_battle(pokedex_id=pokedex_id, is_shiny=is_shiny, user=user, channel_id=channel_id)
            await message.channel.send(embed=embed)

        if message.content.startswith('.adminraid') and user.id == 701062435678846998:
            pokedex_id = int(message.content.split()[1])
            is_shiny = {"true": True, "false": False}.get(message.content.split()[2].lower(), False)
            pookemon, embed = await admin_start_raid(pokedex_id=pokedex_id, is_shiny=is_shiny, user=user, channel_id=channel_id)
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

        if message.content.startswith('.resetquest') and user.id == 701062435678846998:
            split = message.content.split()
            user_id = split[1]
            embed = await admin_reset_quest(user_id=user_id)
            await message.channel.send(embed=embed)

        if '.resetchallenge' in message.content and user.id == 701062435678846998:
            embed = await reset_challenge(user)
            await message.channel.send(embed=embed)

        if '.startchallenge' in message.content and user.id == 701062435678846998:
            await start_challenge()

        if message.content.startswith('.getseed') and user.id == 701062435678846998:
            split = message.content.split()
            pokemon_id = split[1]
            embed = await find_in_seeds(user=user, pokemon_id=pokemon_id)
            await message.channel.send(embed=embed)

    #######################Battle commands#######################
        if message.content.startswith('.spawn'):
            pokemon, embed = await start_battle(user=user, channel_id=channel_id)
            await message.channel.send(embed=embed)
            if pokemon and pokemon.is_shiny:
                flex_log = await storage_manager.get_flex_log(user.id, channel_id, pokemon.name)
                if not flex_log:
                    log = FlexLog(id= uuid.uuid4(), user_id=user.id, channel_id=channel_id, name=pokemon.name, status='active', timestamp=datetime.now(timezone.utc), expiration_date= datetime.now(timezone.utc) + timedelta(hours=24))
                    await storage_manager.save_object(obj=log, cache_key=f"{REDIS_PREFIX}flexlog_id:{log.id}", table_name='flex_log', unique_columns=['id'])
                    channel = await client.fetch_channel(FLEX_ID)
                    embed = embed_generator.create_flex_embed(user, pokemon)
                    await channel.send(embed=embed)

        if message.content.startswith('.run'):
            embed = await run_battle(user=user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.join') and not message.content.startswith('.joinraid'):
            local_id = message.content[-3:]
            embed = await join_battle(user=user, local_id=local_id, channel_id=channel_id)
            await message.channel.send(embed=embed)

    #######################Raid commands#######################
        if message.content.startswith('.raid') and not message.content.startswith('.raidframe') and not message.content.startswith('.raidpokedex'):
            try:
                pokemon, embed = await start_raid(user=user, channel_id=channel_id)
                await message.channel.send(embed=embed)
                if pokemon and pokemon.is_shiny:
                    flex_log = await storage_manager.get_flex_log(user.id, channel_id, pokemon.name)
                    if not flex_log:
                        log = FlexLog(id= uuid.uuid4(), user_id=user.id, channel_id=channel_id, name=pokemon.name, status='active', timestamp=datetime.now(timezone.utc), expiration_date= datetime.now(timezone.utc) + timedelta(hours=24))
                        await storage_manager.save_object(obj=log, cache_key=f"{REDIS_PREFIX}flexlog_id:{log.id}", table_name='flex_log', unique_columns=['id'])
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

        if message.content.startswith('.displayname'):
            name = message.content.split()[1]
            embed = await display_name(user,name)
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
        
        if message.content.startswith('.learnset'):
            page = message.content.split()
            try:
                if len(page) > 1:
                    if int(page[1]) > 0: # Ensure user doesn't ask for page 0 or negative
                        requested_page = int(page[1]) - 1
                        embed: discord.Embed = await get_learnset(user=user, page=requested_page)
                    else:
                        embed = await get_learnset(user=user, page=0)
                else:
                    embed = await get_learnset(user=user, page=0)
            except:
                embed = await get_learnset(user=user, page=0)

            await message.channel.send(embed=embed)
        elif message.content.startswith('.learn'):
            split = message.content.split()
            try:
                slot = int(split[1])
            except:
                slot = 5
            move_name = split[2]
            embed = await learn_move(user, slot, move_name)
            await message.channel.send(embed=embed)

        if message.content.startswith('.moves'):
            embed = await see_moves(user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.pokedex'):
            page = message.content.split()
            try:
                if len(page) > 1:
                    if int(page[1]) > 0: # Ensure user doesn't ask for page 0 or negative
                        requested_page = int(page[1]) - 1
                        embed: discord.Embed = await list_missing_pokemon(user=user, page=requested_page, page_size=10)
                    else:
                        embed = await list_missing_pokemon(user=user, page=0, page_size=10)
                else:
                    embed = await list_missing_pokemon(user=user, page=0, page_size=10)
            except:
                embed = await list_missing_pokemon(user=user, page=0, page_size=10)

            await message.channel.send(embed=embed)

        if message.content.startswith('.raidpokedex'):
            page = message.content.split()
            try:
                if len(page) > 1:
                    if int(page[1]) > 0: # Ensure user doesn't ask for page 0 or negative
                        requested_page = int(page[1]) - 1
                        embed: discord.Embed = await list_missing_raid_pokemon(user=user, page=requested_page, page_size=10)
                    else:
                        embed = await list_missing_raid_pokemon(user=user, page=0, page_size=10)
                else:
                    embed = await list_missing_raid_pokemon(user=user, page=0, page_size=10)
            except:
                embed = await list_missing_raid_pokemon(user=user, page=0, page_size=10)

            await message.channel.send(embed=embed)

        if message.content.startswith('.view recent'):
            embed = await view_recent_pokemon(user)
            await message.channel.send(embed=embed)
        elif message.content.startswith('.view'):
            local_id = message.content.split()
            if len(local_id) > 1:
                embed = await view_pokemon(user=user, local_id=str(local_id[1]))
            else:
                embed = await view_buddy(user=user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.stats recent'):
            embed = await view_recent_pokemon_stats(user)
            await message.channel.send(embed=embed)
        elif message.content.startswith('.stats buddy'):
            embed = await view_buddy_stats(user)
            await message.channel.send(embed=embed)
        elif message.content.startswith('.stats'):
            local_id = message.content.split()
            if len(local_id) > 1:
                embed = await view_pokemon_stats(user=user, local_id=str(local_id[1]))
            else:
                embed = await view_buddy_stats(user=user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.filter'):
            embed = await filter_pokemon(user=user, filter_message=message.content)
            await message.channel.send(embed=embed)

        if message.content.startswith('.buddy recent'):
            embed = await set_buddy_recent(user)
            await message.channel.send(embed=embed)
        elif message.content.startswith('.buddy'):
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

        if message.content.startswith('.release duplicates'):
            embed = await release_duplicates(user)
            await message.channel.send(embed=embed)
        elif message.content.startswith('.release'):
            try:
                num = int(message.content.split()[1])
                embed = await release_single(user, num)
            except:
                embed = embed_generator.create_release_embed(user=user, content="Could not release! Please select a pokemon from .list")
            await message.channel.send(embed=embed)

        if message.content.startswith('.safe recent'):
            embed = await mark_safe_recent(user)
            await message.channel.send(embed=embed)

        elif message.content.startswith('.safe'):
            num = message.content.split()
            if len(num) > 1 and num[1]:
                embed = await mark_safe(user, int(num[1]))
            else:
                embed = await mark_safe_buddy(user)
            await message.channel.send(embed=embed)

        
        if message.content.startswith('.seemove'):
            name = message.content.split()
            if len(name) > 1 and name[1]:
                embed = await see_single_move(name[1])
        elif message.content.startswith('.see'):
            name = message.content.split()
            if len(name) > 1 and name[1]:
                embed = await see_pokemon(name[1])
            else:
                embed = embed_generator.create_master_pokemon_view_failure()
        await message.channel.send(embed=embed) 

    #######################event commands#######################
        if message.content.startswith('.event toggle'):
            embed = await toggle_event(user)
            await message.channel.send(embed=embed) 
        elif message.content.startswith('.eventframe'):
            embed = await full_event_shiny_frame(user)
            await message.channel.send(embed=embed) 
        elif message.content.startswith('.event'):
            embed = await get_event_details(user)
            await message.channel.send(embed=embed)         

    #######################item commands#######################
        if message.content.startswith('.shop'):
            embed = await get_shop(user)
            await message.channel.send(embed=embed)    
        
        if message.content.startswith('.buy'):
            name_quantity = message.content.split()
            try:
                name = name_quantity[1]
                if (len(name_quantity) >= 3) and name_quantity[2]:
                    quantity = name_quantity[2]
                else:
                    quantity = 1
            except:
                embed = embed = embed_generator.create_invalid_syntax_embed(user) 
            try:
                    if name == 'shinyframe':
                        embed = await buy_item(user, 'shinyframe', int(quantity))
                    elif name == 'resetseed':
                        embed = await buy_item(user, 'resetseed', int(quantity))
                    elif name == 'skipframe':
                        embed = await buy_item(user, 'skipframe', int(quantity))
                    elif name == 'rerollnature':
                        embed = await buy_item(user, 'rerollnature', int(quantity))
                    elif name == 'rerolliv':
                        embed = await buy_item(user, 'rerolliv', int(quantity))
                    elif name == 'raidpass':
                        embed = await buy_item(user, 'raidpass', int(quantity))
                    elif name == 'skipraidframe':
                        embed = await buy_item(user, 'skipraidframe', int(quantity))
                    elif name == 'rarecandy':
                        embed = await buy_item(user, 'rarecandy', int(quantity))
                    elif name == 'regionpass':
                        embed = await buy_item(user, 'regionpass', int(quantity))
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

        if message.content.startswith('.rerollnature'):
            embed = await reroll_nature(user=user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.rarecandy'):
            try:
                quantity = int(message.content.split()[1])
            except:
                quantity = 1

            embed = await rare_candy(user, quantity)
            await message.channel.send(embed=embed)

        if message.content.startswith('.fullframe'):
            embed = await toggle_full_frame(user)
            await message.channel.send(embed=embed)

        if '.shinyframe' in message.content:
            if user.full_frame:
                embed = await full_shiny_frame(user)
            else:
                embed = await shiny_frame(user)
            await message.channel.send(embed=embed)
        
        if '.raidframe' in message.content:
            if user.full_frame:
                embed = await full_raid_shiny_frame(user)
            else:
                embed = await raid_shiny_frame(user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.skipframe'):
            try:
                quantity = int(message.content.split()[1])
            except:
                quantity = 1
            embed = await skip_frames(user, quantity)
            await message.channel.send(embed=embed)
        
        if message.content.startswith('.skipraidframe'):
            try:
                quantity = int(message.content.split()[1])
            except:
                quantity = 1
            embed = await skip_raid_frames(user, quantity)
            await message.channel.send(embed=embed)

        if message.content.startswith('.regionpass'):
            try:
                region = message.content.split()[1]
            except:
                region = None
            embed = await region_pass(user, region)
            await message.channel.send(embed=embed)        

    #######################trade commands######################
        #.trade @user
        mentions = message.mentions
        #print(mentions[0].id)
        if message.content.startswith('.trade') and mentions and mentions[0].id != None and mentions[0].id != user.id:
            embed = await start_trade(user, mentions[0])
            await message.channel.send(embed=embed)
        elif message.content == '.trade':
            embed = await display_trade(user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.trade join'):
            local_id = message.content[-3:]
            embed = await join_trade(user=user, local_id=local_id)
            await message.channel.send(embed=embed)

        if message.content.startswith('.trade add pokemon'):
            local_id = message.content.split()
            if len(local_id) > 3:
                embed = await add_pokemon_to_trade(user=user, local_id=local_id[3])
                await message.channel.send(embed=embed)
        if message.content.startswith('.trade add item'):
            local_message = message.content.split()
            if len(local_message) > 4:
                embed = await add_item_to_trade(user=user, item_name=local_message[3], item_quantity=int(local_message[4]))
                await message.channel.send(embed=embed)
        if message.content.startswith('.trade add money'):
            amount = message.content.split()
            if len(amount) > 3 and int(amount[3]) != 0:
                embed = await add_money_to_trade(user=user, amount=int(amount[3]))
                await message.channel.send(embed=embed)

        if message.content.startswith('.trade confirm'):
            embed = await confirm_trade(user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.trade cancel'):
            embed = await cancel_trade(user)
            await message.channel.send(embed=embed)
    ###########################################################
        if message.content.startswith('.leaderboard'):
            embed = await get_leaderboard()
            await message.channel.send(embed=embed)
        
        if message.content.startswith('.quest'):
            embed = await quest(user)
            await message.channel.send(embed=embed)

        if message.content.startswith('.challenge info'):
            embed = await challenge_info(user)
            await message.channel.send(embed=embed)
        elif message.content.startswith('.challenge') and str(message.channel.id) == PROFESSOR_ID:
            local_id = message.content.split()
            if len(local_id) > 1:
                embed = await challenge_professor(user, local_id=str(local_id[1]))
            else:
                embed = await challenge_professor(user, local_id=str(1))
            await message.channel.send(embed=embed)

        """if message.content.startswith(".battle"):
            embed = await start_trainer_battle(user)
            await message.channel.send(embed=embed)    
        """
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Message Response Time: {elapsed_time} seconds")

client.run(os.getenv('DISCORD_BOT_TOKEN'))


        

