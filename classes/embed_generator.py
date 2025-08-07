import json
import math
import discord

from classes.odds import Odds

default_color = 0xffffff
event_color = 0xff7b00
trade_color = 0x5900ff

region_sprite_map = {
    "kanto": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/1.png",
    "johto": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/152.png",
    "hoenn": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/252.png",
    "sinnoh": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/387.png",
    "unova": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/494.png",
    "kalos": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/650.png",
    "alola": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/722.png",
    "galar": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/810.png",
    "paldea": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/906.png",
    "no region": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png"
}

class EmbedGenerator():

    def get_color(self, pokemon):
        if pokemon.is_shiny:
            return 0xf5a8ff
        elif pokemon.tier == 1:
            return 0x002aff
        elif pokemon.tier == 2:
            return 0x0cb800
        elif pokemon.tier == 3:
            return 0xeeff00
        elif pokemon.tier == 4:
            return 0xff0000
        
    def get_color_by_tier(self, tier):
        if tier == 1:
            return 0x002aff
        elif tier == 2:
            return 0x0cb800
        elif tier == 3:
            return 0xeeff00
        elif tier == 4:
            return 0xff0000
        
    def create_raid_finish_embed(self, pokemon_name, url, color, rewards):
        if color == 0xf5a8ff:
            pokemon_name = f"✨{pokemon_name.capitalize()}✨"
        else:
            pokemon_name = pokemon_name.capitalize()
        desc = f"**Base XP**: {rewards['exp']}\n**Money**: ${rewards['money']:,}"
        embed=discord.Embed(title=f"Caught {pokemon_name}!", description=desc, color=color)
        embed.set_author(name="Goomybot")
        embed.set_image(url=url)
        return embed

    def create_already_in_raid_embed(self,user_name):
        embed=discord.Embed(title=f"Already in raid!", color=default_color)
        embed.set_author(name=user_name.capitalize())
        return embed

    def create_raid_embed(self, user_name, pokemon_name, join_code, duration, url, color):
        if color == 0xf5a8ff:
            pokemon_name = f"✨{pokemon_name.capitalize()}✨"
        else:
            pokemon_name = pokemon_name.capitalize()
        embed=discord.Embed(title=f"Raid!\n{pokemon_name}", description=f"Local code: **{join_code}**", color=color)
        embed.set_author(name=user_name.capitalize())
        embed.set_image(url=url)
        if duration > 60:
            minutes = math.floor(duration / 60)
            seconds = duration % 60
            # Use f-string for formatting, adding a leading zero to seconds if less than 10
            formatted_duration = f"Duration: ~ {minutes}m {seconds:02d}s"
        else:
            formatted_duration = f"Duration: ~ {duration} seconds"
        embed.set_footer(text=formatted_duration)
        return embed
    
    def create_join_raid_embed(self, user, new_duration):
        embed=discord.Embed(title=f"Joined raid!", color=default_color)
        if new_duration > 60:
            minutes = math.floor(new_duration / 60)
            seconds = new_duration % 60
            # Use f-string for formatting, adding a leading zero to seconds if less than 10
            formatted_duration = f"Time left: {minutes}m {seconds:02d}s!"
        else:
            formatted_duration = f"Time left: {new_duration} seconds!"
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url = user.profile_image)
        embed.set_footer(text=formatted_duration)
        embed.set_author(name=user.name.capitalize())
        return embed

    def create_raid_failure_embed(self, user):
        embed=discord.Embed(title = "Failure!",description=f"Could not start raid, please check that you have a raidpass!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_trainer_use_fail_embed(self, user_name, message):
        embed=discord.Embed(title=f"Move Failed", description=message, color=default_color)
        embed.set_author(name=user_name.capitalize())
        return embed

    def create_trainer_battle_embed(self, user_name, pokemon, trainer_name, trainer_sprite, conditions:dict, conditions_met:list, bonus_duration):
        print(conditions)
        print(conditions_met)
        color = self.get_color(pokemon)
        pokemon_name = self.format_pokemon_name(pokemon)
        embed=discord.Embed(title=f"{trainer_name} challenges you with {pokemon_name}", description="Use moves that match the following conditions to win:", color=color)
        embed.set_author(name=user_name.capitalize())
        embed.set_image(url=pokemon.sprite_front)
        embed.set_thumbnail(url=trainer_sprite)
        #embed.set_footer(text=f"Complete in {bonus_duration} seconds to gain 2x rewards!")
        for con in conditions.keys():
            if con in conditions_met:
                embed.add_field(name="~~"+str(con).capitalize()+"~~", value="~~"+str(conditions[con])+"~~", inline=False)
            else:
                embed.add_field(name=str(con).capitalize(), value=str(conditions[con]), inline=False)

        return embed

    def create_trainer_battle_finish_embed(self, pokemon_name, url, color, rewards):
        if color == 0xf5a8ff:
            pokemon_name = f"✨{pokemon_name.capitalize()}✨"
        else:
            pokemon_name = pokemon_name.capitalize()
        desc = f"**Money**: ${rewards:,}"
        embed=discord.Embed(title=f"Defeated {pokemon_name}!", description=desc, color=color)
        embed.set_author(name="Goomybot")
        embed.set_image(url=url)
        return embed
    
    def create_battle_embed(self, user_name, pokemon_name, join_code, duration, url, color):
        if color == 0xf5a8ff:
            pokemon_name = f"✨{pokemon_name.capitalize()}✨"
        else:
            pokemon_name = pokemon_name.capitalize()
        embed=discord.Embed(title=f"{pokemon_name} Spawned!", description=f"Local code: **{join_code}**", color=color)
        embed.set_author(name=user_name.capitalize())
        embed.set_image(url=url)
        embed.set_footer(text=f"Duration: ~ {duration} seconds")
        return embed
    
    def create_battle_finish_embed(self, pokemon_name, url, color, rewards):
        if color == 0xf5a8ff:
            pokemon_name = f"✨{pokemon_name.capitalize()}✨"
        else:
            pokemon_name = pokemon_name.capitalize()
        desc = f"**Base XP**: {rewards['exp']}\n**Money**: ${rewards['money']:,}"
        embed=discord.Embed(title=f"Caught {pokemon_name}!", description=desc, color=color)
        embed.set_author(name="Goomybot")
        embed.set_image(url=url)
        return embed

    def create_already_in_battle_embed(self,user):
        embed=discord.Embed(title=f"Already in battle!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url = user.profile_image)
        return embed
    
    def create_run_from_battle_embed(self, user):
        embed=discord.Embed(title=f"Ran from battle!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url = user.profile_image)
        return embed
    
    def create_run_from_trainer_battle_embed(self, user):
        embed=discord.Embed(title=f"Ran from trainer battle!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url = user.profile_image)
        return embed

    def create_run_from_battle_fail_embed(self, user, reason):
        embed=discord.Embed(title=f"Cannot run from a battle\nReason: {reason}", color=default_color)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url = user.profile_image)
        embed.set_author(name=user.name.capitalize())
        return embed   
    
    def create_join_battle_embed(self, user, new_duration):
        embed=discord.Embed(title=f"Joined battle!", color=default_color)
        embed.set_footer(text=f"Time left: {new_duration} seconds!")
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url = user.profile_image)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_evolved_fail_embed(self, user_name, message):
        embed=discord.Embed(description=message, color=default_color)
        embed.set_author(name=user_name.capitalize())
        return embed
    
    def format_pokemon_name(self, pokemon):
        if pokemon.is_shiny:
            return f"✨{pokemon.name.capitalize()}✨"
        else:
            return f"{pokemon.name.capitalize()}"

    def create_learnset_table(self, user, pokemon, moves, page, total_pages):
        embed=discord.Embed(title=f"{self.format_pokemon_name(pokemon)} Learnset",description=f"{moves}", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        embed.set_footer(text=f"Page {page}/{total_pages}")
        return embed

    def create_who_learns_table(self, user, move, pokemon, page, total_pages):
        embed=discord.Embed(title=f"Who Learns {move.capitalize()}?",description=f"{pokemon}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url="https://github.com/PokeAPI/sprites/blob/master/sprites/items/tm-normal.png?raw=true")
        embed.set_footer(text=f"Page {page}/{total_pages}")
        return embed
    
    def create_move_table(self, user, pokemon, moves):
        embed=discord.Embed(title=f"{self.format_pokemon_name(pokemon)} Moves",description=f"{moves}", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed
    
    def create_move_view(self, move):
        embed=discord.Embed(title=f"{move.name.capitalize()}",description=f"{move.__str__()}", color=default_color)
        embed.set_author(name="Goomybot")
        embed.set_thumbnail(url="https://github.com/PokeAPI/sprites/blob/master/sprites/items/tm-normal.png?raw=true")
        return embed
    
    def format_view_table(self, user):
        result = ''
        for key, value in user.view_table.items():
            result = result + f"**{key}**: {value['name']}\n"
        return result

    def create_user_view_table(self, user, page, total_pages):
        embed=discord.Embed(description=f"{self.format_view_table(user)}",color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        embed.set_footer(text=f"Page {page}/{total_pages}")
        return embed
    
    def create_missing_view_table(self, user, pokemon_table, page, total_pages, total_count, all_pokemon_count):
        embed=discord.Embed(title = f"{((all_pokemon_count - int(total_count))/all_pokemon_count):.2%} complete!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        for key, value in pokemon_table.items():
            embed.add_field(name=value['id'], value=value['name'], inline=True)
        embed.set_footer(text=f"Page {page}/{total_pages}")
        return embed
    
    def create_pokemon_view(self, user, pokemon):
        embed=discord.Embed(description=pokemon.__str__(), color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed
    
    def create_pokemon_stats_view(self, user, pokemon):
        embed=discord.Embed(description=pokemon.stats_str(), color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_master_pokemon_view(self, pokemon_master):
        pokemon_master.is_shiny = False
        embed=discord.Embed(description=pokemon_master.__str__(), color=self.get_color(pokemon_master))
        embed.set_author(name="Goomybot")
        embed.set_image(url=pokemon_master.front_shiny_sprite)
        embed.set_thumbnail(url=pokemon_master.front_default_sprite)
        return embed

    def create_master_pokemon_view_failure(self):
        embed=discord.Embed(description=f"No pokemon found, please check name", color=default_color)
        embed.set_author(name="Goomybot")
        return embed
    
    def create_rare_candy_view(self, user, pokemon, quantity):
        embed=discord.Embed(description=f"{pokemon.name.capitalize()} leveled up {quantity} time(s)!\nLevel: {pokemon.level}", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_rare_candy_fail_view(self, user, pokemon):
        embed=discord.Embed(description=f"{pokemon.name.capitalize()} cannot level up!", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_region_view(self, user, region):
        embed=discord.Embed(description=f"Set region to: {region.capitalize()}", color=default_color)
        embed.set_thumbnail(url=region_sprite_map[region.lower()])
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_region_failure_view(self, user, reason):
        embed=discord.Embed(description=f"Could not change region, {reason}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_shiny_frame(self, user, shiny_frame):
        embed=discord.Embed(description=f"Current Frame: {user.frame}\nShiny Frame: {shiny_frame}", color=0xf5a8ff)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_raid_shiny_frame(self, user, shiny_frame):
        embed=discord.Embed(description=f"Current Frame: {user.raid_frame}\nShiny Frame: {shiny_frame}", color=0xf5a8ff)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_full_shiny_frame(self, user, shiny_frame, pokemon_name, pokemon_url):
        embed=discord.Embed(title=f"✨{pokemon_name.capitalize()}✨", description=f"Current Frame: {user.frame}\nShiny Frame: {shiny_frame}", color=0xf5a8ff)
        embed.set_author(name=user.name.capitalize())
        embed.set_image(url=pokemon_url)
        return embed

    def create_full_trainer_frame(self, user, shiny_frame, pokemon_name, pokemon_url):
        embed=discord.Embed(title=f"✨{pokemon_name.capitalize()}✨", description=f"Current Frame: {user.battle_frame - 99999}\nShiny Frame: {shiny_frame - 100000}", color=0xf5a8ff)
        embed.set_author(name=user.name.capitalize())
        embed.set_image(url=pokemon_url)
        return embed

    def create_full_raid_shiny_frame(self, user, shiny_frame, pokemon_name, pokemon_url):
        embed=discord.Embed(title=f"✨{pokemon_name.capitalize()}✨", description=f"Current Frame: {user.raid_frame}\nShiny Frame: {shiny_frame}", color=0xf5a8ff)
        embed.set_author(name=user.name.capitalize())
        embed.set_image(url=pokemon_url)
        return embed
    
    def create_frame_embed(self, user):
        embed=discord.Embed(description=f"Current Frame: {user.frame}\nRaid Frame: {user.raid_frame}\nTrainer Frame: {user.battle_frame - 99999}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_reset_seeds_embed(self, user):
        embed=discord.Embed(description=f"Reset Seeds!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_admin_embed(self, command):
        embed=discord.Embed(description=f"Executed admin command: {command}", color=0xff00ae)
        embed.set_author(name='Goomybot')
        return embed
    
    def create_help_embed(self, info):
        embed=discord.Embed(description=f"{info}", color=0xff00ae)
        embed.set_author(name='Goomybot')
        return embed
    
    def create_register_embed(self, name):
        embed=discord.Embed(description=f"Registered {name}!", color=0xff00ae)
        embed.set_author(name='Goomybot')
        return embed

    def create_not_registered_embed(self):
        embed=discord.Embed(description=f"Please use .register to get started!", color=0xff00ae)
        embed.set_author(name='Goomybot')
        return embed
    
    def create_already_registered_embed(self):
        embed=discord.Embed(description=f"You are already registered", color=0xff00ae)
        embed.set_author(name='Goomybot')
        return embed
    
    def create_user_profile_embed(self, user):
        embed=discord.Embed(description=user.__str__(), color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
        
    def create_user_profile_image_success_embed(self, user):
        embed=discord.Embed(description='Successfully set profile image', color=default_color)
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_user_profile_image_failed_embed(self, user, host_string):
        embed=discord.Embed(description=f'Failed to set profile image, please select an image from:\n{host_string}', color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed

    def create_item_bought_embed(self, user, item_name, quantity):
        embed=discord.Embed(description=f'Bought {item_name} x{quantity}', color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_item_bought_failed_embed(self, user, item_name, quantity):
        embed=discord.Embed(description=f'Could not buy {item_name} x{quantity}\nAvailable funds: {user.wallet}', color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_invalid_syntax_embed(self, user):
        embed=discord.Embed(description=f'Could not process command, please use .help for syntax', color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_item_failure_embed(self, user, item_name):
        embed=discord.Embed(description=f'Could not use {item_name}. Please check quantity or command syntax', color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed

    def create_item_failure_generic_embed(self, user, message):
        embed=discord.Embed(description=f'{message}', color=default_color)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_skip_frames_embed(self, user, num_frames):
        embed=discord.Embed(description=f"Skipped {num_frames} frames!\nCurrent Frame: {user.frame}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_skip_trainer_frames_embed(self, user, num_frames):
        embed=discord.Embed(description=f"Skipped {num_frames} frames!\nCurrent Frame: {user.battle_frame - 99999}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_skip_raid_frames_embed(self, user, num_frames):
        embed=discord.Embed(description=f"Skipped {num_frames} raid frames!\nCurrent Frame: {user.raid_frame}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_skip_to_shiny_raid_embed(self, user):
        embed=discord.Embed(description=f"Skipped to shiny frame!\nCurrent Frame: {user.raid_frame}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_skip_to_shiny_embed(self, user):
        embed=discord.Embed(description=f"Skipped to shiny frame!\nCurrent Frame: {user.frame}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed

    def create_skip_to_trainer_shiny_embed(self, user):
        embed=discord.Embed(description=f"Skipped to shiny frame!\nCurrent Frame: {user.battle_frame-99999}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed

    def create_change_buddy_failed_embed(self, user):
        embed=discord.Embed(description=f"Cannot change buddy while in a battle/raid!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_level_up_embed(self, user, buddy, levels, reward):
        embed=discord.Embed(description=f"{buddy.name.capitalize()} gained {levels} level(s)\nEarned: ${reward:,.0f}", color=self.get_color(buddy))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=buddy.sprite_front)
        return embed
    
    def format_items(self,items):
        items = sorted(items, key=lambda item: item.name)
        result = ""
        for i, item in enumerate(items):
            if item.name != 'Nothing':
                result = result + f"**{i}**: {item.name.capitalize()} - {item.quantity}\n"
        return result

    def create_items_view_table(self, user, items):
        embed=discord.Embed(description=self.format_items(items), color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def format_shop(self, items):
        result = ''
        for item_name, item_price in items.items():
            result += f"**{item_name.capitalize()}**  -  ${item_price:,.0f}\n"
        return result.strip() # .strip() removes the trailing newline from the last item
            
    def create_shop_view_table(self, user, items):
        embed=discord.Embed(title="Goomybot Shop", description=f"{self.format_shop(items)}", color=default_color)
        #embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        embed.set_footer(text='.buy <item_name> <quantity>')
        return embed

    def create_odds_table(self, user):
        odds = Odds()
        embed=discord.Embed(description=f"Goomybot Odds\n{odds}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_flex_embed(self, user, pokemon, flex_type):
        if pokemon.is_shiny:
            pokemon_name = f"✨{pokemon.name.capitalize()}✨"
        else:
            pokemon_name = pokemon_name.capitalize()
        embed=discord.Embed(title=f"{pokemon_name}", color=0xf5a8ff)
        embed.set_image(url=pokemon.sprite_front)
        embed.set_footer(text=f'{flex_type} {user.name.capitalize()}')
        return embed
    
    def create_rerolliv_view(self, user, pokemon, reroll_choice):
        embed=discord.Embed(title=f"{self.format_pokemon_name(pokemon)}", description=f"{pokemon.reroll_str(reroll_choice)}",color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_rerollnature_view(self, user, pokemon):
        embed=discord.Embed(description=f"New Nature: {pokemon.nature}", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_bug_reported_embed(self, user):
        embed=discord.Embed(description= "Bug Reported!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_bug_log_embed(self, user, content):
        embed=discord.Embed(description= content, color=default_color)
        embed.set_author(name=f"Reported By: {user.name.capitalize()}")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_lottery_embed(self, user, content):
        embed=discord.Embed(description= content, color=default_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_release_embed(self, user, content):
        embed=discord.Embed(description= content, color=default_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_safe_pokemon_view(self, user, pokemon):
        embed=discord.Embed(description=f"{pokemon.__str__()}", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_safe_pokemon_failure_view(self, user):
        embed=discord.Embed(description=f"Could not mark safe! Please try again!", color=default_color)
        embed.set_author(name=user.name.capitalize())
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed

    def create_joined_swaps_embed(self, user):
        embed=discord.Embed(description= "Swaps enabled!", color=default_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_left_swaps_embed(self, user):
        embed=discord.Embed(description= "Swaps disabled!", color=default_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed

    def create_joined_event_embed(self, user):
        embed=discord.Embed(description= "Joined Event!", color=event_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_left_event_embed(self, user):
        embed=discord.Embed(description= "Left Event!", color=event_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed

    def create_event_embed(self, user):
        embed=discord.Embed(title="??? used Water Gun!", color=event_color)
        embed.set_author(name="Goomybot")
        embed.set_image(url=r'https://raw.githubusercontent.com/ultra-move/Goomybot-v3/refs/heads/prod/sprites/water.png')
        embed.set_footer(text="use .event toggle to join/leave the event")
        return embed
    
    def create_not_in_event_embed(self, user):
        embed=discord.Embed(title="Not in the event!",description= "Use .event toggle to join the event", color=event_color)
        if user:
            embed.set_author(name=f"{user.name.capitalize()}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_full_frame_embed(self, user):
        embed=discord.Embed(description=f"Full Shiny Frame: {user.full_frame}", color=default_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    ##############Trade embeds###################

    def create_trade_started_embed(self, user, user_mentioned, local_id):
        embed=discord.Embed(description=f"Trade initiated with {user_mentioned.name}", color=trade_color)
        embed.add_field(name="Local code:", value=local_id)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        embed.set_footer(text="use .trade join <local id> to join the trade")
        return embed
    
    def create_trade_invalid_user_embed(self, user):
        embed=discord.Embed(description=f"Invalid user, please @ a valid user!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed

    def create_trade_already_active_embed(self, user):
        embed=discord.Embed(description=f"You are already in a trade!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_trade_already_mentioned_active_embed(self, user, user_mentioned):
        embed=discord.Embed(description=f"{user_mentioned.name} is already in a trade!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_join_trade_success_embed(self, user):
        embed=discord.Embed(description=f"{user.name.capitalize()} activated the trade!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        embed.set_footer(text="please use .help trade!")
        return embed
    
    def create_join_trade_failure_embed(self, user):
        embed=discord.Embed(description=f"Could not join trade, please try again", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_trade_block_embed(self, user, reason):
        embed=discord.Embed(description=f"{reason}", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_trade_add_failure_embed(self, user, reason):
        embed=discord.Embed(description=f"{reason} Please try again", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)        
        return embed
    
    def create_trade_add_pokemon_embed(self, user, pokemon):
        embed=discord.Embed(description=f"Added {pokemon.name} to trade!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        embed.set_image(url=pokemon.sprite_front)
        return embed

    def create_trade_add_item_embed(self, user, item_name, item_quantity):
        embed=discord.Embed(description=f"Added {item_name} x{item_quantity} to trade!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_trade_add_money_embed(self, user, amount):
        embed=discord.Embed(description=f"Added ${amount:,.0f} to trade!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_trade_add_money_failure_embed(self, user, amount):
        embed=discord.Embed(description=f"Could not add ${amount:,.0f} to trade!\nCurrent wallet: {user.wallet}", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_trade_display_embed(self, user, content, user1_name, user2_name):
        embed = discord.Embed(
            title=f"Trade between {user1_name} and {user2_name}",
            description=content,
            color=trade_color
        )
        embed.set_footer(text="Use .trade confirm to finalize the trade!")
        return embed
    
    def create_trade_completed_embed(self, active_trade):
        embed=discord.Embed(description=f"Trade {active_trade.local_id} completed!", color=trade_color)
        embed.set_author(name="Goomybot")
        return embed
    
    def create_trade_canceled_embed(self, user):
        embed=discord.Embed(description=f"Trade canceled!", color=trade_color)
        embed.set_author(name=user.name.capitalize())
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_leaderboard_embed(self, leaderboard_stats):
        """
        Creates a discord.Embed object to display leaderboard statistics.

        Args:
            leaderboard_stats (list of dict): A list of dictionaries, where each dict
                                            contains 'category', 'user_name', and 'count'
                                            for the top user in that category.
        Returns:
            discord.Embed: The formatted embed for the leaderboard.
        """

        embed = discord.Embed(
            title="🏆 Goomybot Leaderboards 🏆",
            color=default_color
        )

        # You can set a thumbnail relevant to leaderboards if you have one
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')

        if not leaderboard_stats:
            embed.add_field(name="No Data Available", value="Could not fetch any leaderboard statistics at this time.", inline=False)
            return embed

        for entry in leaderboard_stats:
            category = entry["category"]
            user_name = entry["user_name"]
            count = entry["count"]

            # Format the count. Use currency format for "Total Spent".
            if category == "Big Spender":
                formatted_count = f"${count:,.2f}" # Format as currency with 2 decimal places
            else:
                formatted_count = f"{count:,}" # Format with comma for thousands

            # Add a field for each category
            embed.add_field(
                name=f"{category}",
                value=f"**{user_name.capitalize()}** with {formatted_count}",
                inline=False # Set to True if you want them side-by-side, but false is often clearer for leaderboards
            )
        return embed
    
    def create_quest_embed(self, user, pokemon, quest):
        pokemon.is_shiny = False
        embed=discord.Embed(title=f"Daily Quest:\n{quest.name}", description=quest.__str__(), color=self.get_color(pokemon))
        embed.set_image(url=pokemon.front_default_sprite)
        embed.set_author(name=user.name.capitalize())
        embed.set_footer(text=f"Remaining Time: \n{quest.get_time_remaining()}")
        return embed
    
    def create_quest_complete(self, user, pokemon, quest):
        pokemon.is_shiny = False
        embed=discord.Embed(title=f"Quest: {quest.name} Complete!", description=quest.__str__(), color=self.get_color(pokemon))
        embed.set_thumbnail(url=pokemon.front_default_sprite)
        embed.set_author(name=user.name.capitalize())
        return embed

    def create_quest_already_complete(self, user, pokemon, quest):
        pokemon.is_shiny = False
        embed=discord.Embed(title=f"Quest Already Complete!", description=f"Next quest can be started in:\n{quest.get_time_remaining()}", color=self.get_color(pokemon))
        embed.set_thumbnail(url=pokemon.front_default_sprite)
        embed.set_author(name=user.name.capitalize())
        return embed

    def create_professor_view(self, professor):
        embed=discord.Embed(title=f"Professor Challenge!", description=f"{professor.get_condition_string()}", color=self.get_color_by_tier(professor.tier))
        embed.set_thumbnail(url=r"https://play.pokemonshowdown.com/sprites/trainers/oak.png")
        embed.set_author(name="Professor Oak")
        embed.set_footer(text="Complete a bonus condition to earn 2x rewards!\nThis challenge expires in 30 minutes")
        return embed
    
    def create_challenge_complete_view(self, user, pokemon, challenge, bonus_met, reduced_rewards, reduced_mult):
        embed=discord.Embed(title=f"Challenge Complete!", description=f"{user.name.capitalize()} Completed the challenge with {pokemon.name.capitalize()}\n{challenge.get_reward_string(bonus_met, reduced_rewards, reduced_mult)}", color=self.get_color(pokemon))
        embed.set_thumbnail(url=r"https://play.pokemonshowdown.com/sprites/trainers/oak.png")
        embed.set_image(url=pokemon.sprite_front)
        embed.set_author(name=user.name.capitalize())
        return embed
    
    def create_challenge_failure_view(self, user, pokemon, challenge, failure_display):
        embed=discord.Embed(title=f"Failure!", description=f"{pokemon.name.capitalize()} does not meet the conditions!\n{failure_display}", color=self.get_color_by_tier(challenge.tier))
        embed.set_thumbnail(url=r"https://play.pokemonshowdown.com/sprites/trainers/oak.png")
        embed.set_author(name="Professor Oak")
        return embed
    
    def create_challenge_time_view(self, user, challenge):
        embed=discord.Embed(title=f"This isn't the time to use that!", description=f"{user.name.capitalize()}, you have completed a challenge within the last 10 minutes! Try again later", color=self.get_color_by_tier(challenge.tier))
        embed.set_thumbnail(url=r"https://play.pokemonshowdown.com/sprites/trainers/oak.png")
        embed.set_author(name="Professor Oak")
        return embed
    
    def create_challenge_time_left_view(self, user, time_left):
        embed=discord.Embed(title=f"{user.name.capitalize()}", description=f"Full rewards can be earned in\n{time_left}", color=default_color)
        embed.set_thumbnail(url=r"https://play.pokemonshowdown.com/sprites/trainers/oak.png")
        embed.set_author(name="Professor Oak")
        return embed
    
    def create_challenge_full_rewards_view(self, user):
        embed=discord.Embed(title=f"{user.name.capitalize()}", description=f"Full rewards can be earned now", color=default_color)
        embed.set_thumbnail(url=r"https://play.pokemonshowdown.com/sprites/trainers/oak.png")
        embed.set_author(name="Professor Oak")
        return embed
    
    def create_swap_test_view(self, user, buddy):
        embed=discord.Embed(title=f"{self.format_pokemon_name(buddy)}", description=f"Swap test!", color=default_color)
        embed.set_author(name=f"{user.name.capitalize()}")
        embed.set_image(url="attachment://swapped_image.png")
        return embed

    def create_get_url_view(self, user, buddy):
        embed=discord.Embed(title=f"{self.format_pokemon_name(buddy)}", description=f"{buddy.sprite_front}", color=default_color)
        embed.set_author(name=f"{user.name.capitalize()}")
        return embed