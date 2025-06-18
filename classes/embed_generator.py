import json
import math
import discord

from classes.odds import Odds

default_color = 0xffffff

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

    def create_raid_finish_embed(self, pokemon_name, url, color, rewards):
        embed=discord.Embed(title=f"Caught {pokemon_name.capitalize()}!", color=color)
        embed.set_author(name="goomybot")
        for key, value in rewards.items():
            embed.add_field(name=key, value=value)
        embed.set_image(url=url)
        return embed

    def create_already_in_raid_embed(self,user_name):
        embed=discord.Embed(title=f"Already in raid!", color=default_color)
        embed.set_author(name=user_name)
        return embed

    def create_raid_embed(self, user_name, pokemon_name, join_code, duration, url, color):
        embed=discord.Embed(title=f"Raid!\n{pokemon_name.capitalize()}", color=color)
        embed.set_author(name=user_name)
        embed.set_image(url=url)
        embed.add_field(name="local code:", value=f"{join_code}")
        if duration > 60:
            minutes = math.floor(duration / 60)
            seconds = duration % 60
            # Use f-string for formatting, adding a leading zero to seconds if less than 10
            formatted_duration = f"duration: ~ {minutes}m {seconds:02d}s"
        else:
            formatted_duration = f"duration: ~ {duration} seconds"
        embed.set_footer(text=formatted_duration)
        return embed
    
    def create_join_raid_embed(self, user_name, new_duration):
        embed=discord.Embed(title=f"Joined raid!", color=default_color)
        if new_duration > 60:
            minutes = math.floor(new_duration / 60)
            seconds = new_duration % 60
            # Use f-string for formatting, adding a leading zero to seconds if less than 10
            formatted_duration = f"{minutes}m {seconds:02d}s"
        else:
            formatted_duration = f"{new_duration} seconds"
        embed.add_field(name="duration", value=formatted_duration)
        embed.set_author(name=user_name)
        return embed

    def create_raid_failure_embed(self, user_name):
        embed=discord.Embed(title=f"Could not start raid, please check that you have a raidpass!", color=default_color)
        embed.set_author(name=user_name)
        return embed

    def create_battle_embed(self, user_name, pokemon_name, join_code, duration, url, color):
        embed=discord.Embed(title=f"{pokemon_name.capitalize()} Spawned!", color=color)
        embed.set_author(name=user_name)
        embed.set_image(url=url)
        embed.add_field(name="local code:", value=f"{join_code}")
        embed.set_footer(text=f"duration: ~ {duration} seconds")
        return embed
    
    def create_battle_finish_embed(self, pokemon_name, url, color, rewards):
        embed=discord.Embed(title=f"Caught {pokemon_name.capitalize()}!", color=color)
        embed.set_author(name="goomybot")
        for key, value in rewards.items():
            embed.add_field(name=key, value=value)
        embed.set_image(url=url)
        return embed

    def create_already_in_battle_embed(self,user_name):
        embed=discord.Embed(title=f"Already in battle!", color=default_color)
        embed.set_author(name=user_name)
        return embed
    
    def create_run_from_battle_embed(self, user_name):
        embed=discord.Embed(title=f"Ran from battle!", color=default_color)
        embed.set_author(name=user_name)
        return embed
    
    def create_run_from_battle_fail_embed(self, user_name):
        embed=discord.Embed(title=f"Cannot run from a battle with other users!", color=default_color)
        embed.set_author(name=user_name)
        return embed   
    
    def create_join_battle_embed(self, user_name, new_duration):
        embed=discord.Embed(title=f"Joined battle!", color=default_color)
        embed.add_field(name="duration", value=new_duration)
        embed.set_author(name=user_name)
        return embed
    
    def create_evolved_fail_embed(self, user_name, message):
        embed=discord.Embed(description=message, color=default_color)
        embed.set_author(name=user_name)
        return embed
    
        
    def create_user_view_table(self, user, page, total_pages):
        embed=discord.Embed(color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        for key, value in user.view_table.items():
            embed.add_field(name=key, value=value['name'], inline=True)
        embed.set_footer(text=f"Page {page}/{total_pages}")
        return embed
    
    def create_pokemon_view(self, user, pokemon):
        embed=discord.Embed(description=pokemon.__str__(), color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed
    
    def create_shiny_frame(self, user, shiny_frame):
        embed=discord.Embed(description=f"Current Frame: {user.frame}\nShiny Frame: {shiny_frame}", color=0xf5a8ff)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed

    def create_full_shiny_frame(self, user, shiny_frame, pokemon_url):
        embed=discord.Embed(description=f"Current Frame: {user.frame}\nShiny Frame: {shiny_frame}", color=0xf5a8ff)
        embed.set_author(name=user.name)
        embed.set_image(url=pokemon_url)
        return embed
    
    def create_frame_embed(self, user):
        embed=discord.Embed(description=f"Current Frame: {user.frame}\nRaid Frame: {user.raid_frame}", color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_reset_seeds_embed(self, user):
        embed=discord.Embed(description=f"Reset Seeds!", color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_admin_embed(self, command):
        embed=discord.Embed(description=f"Executed admin command: {command}", color=0xff00ae)
        embed.set_author(name='goomybot')
        return embed
    
    def create_help_embed(self, info):
        embed=discord.Embed(description=f"{info}", color=0xff00ae)
        embed.set_author(name='goomybot')
        return embed
    
    def create_register_embed(self, name):
        embed=discord.Embed(description=f"Registered {name}!", color=0xff00ae)
        embed.set_author(name='goomybot')
        return embed

    def create_not_registered_embed(self):
        embed=discord.Embed(description=f"Please use .register to get started!", color=0xff00ae)
        embed.set_author(name='goomybot')
        return embed
    
    def create_already_registered_embed(self):
        embed=discord.Embed(description=f"You are already registered", color=0xff00ae)
        embed.set_author(name='goomybot')
        return embed
    
    def create_user_profile_embed(self, user):
        embed=discord.Embed(description=user.__str__(), color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
        
    def create_user_profile_image_success_embed(self, user):
        embed=discord.Embed(description='Successfully set profile image', color=default_color)
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_user_profile_image_failed_embed(self, user, host_string):
        embed=discord.Embed(description=f'Failed to set profile image, please select an image from:\n{host_string}', color=default_color)
        embed.set_author(name=user.name)
        return embed

    def create_item_bought_embed(self, user, item_name, quantity):
        embed=discord.Embed(description=f'Bought {item_name} x{quantity}', color=default_color)
        embed.set_author(name=user.name)
        return embed
    
    def create_item_bought_failed_embed(self, user, item_name, quantity):
        embed=discord.Embed(description=f'Could not buy {item_name} x{quantity}\nAvailable funds: {user.wallet}', color=default_color)
        embed.set_author(name=user.name)
        return embed
    
    def create_invalid_syntax_embed(self, user):
        embed=discord.Embed(description=f'Could not process command, please use .help for syntax', color=default_color)
        embed.set_author(name=user.name)
        return embed
    
    def create_item_failure_embed(self, user, item_name):
        embed=discord.Embed(description=f'Could not use {item_name}. Please check quantity or command syntax', color=default_color)
        embed.set_author(name=user.name)
        return embed
    
    def create_skip_frames_embed(self, user):
        embed=discord.Embed(description=f"Skipped 100 frames!\nCurrent Frame: {user.frame}", color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_skip_to_shiny_embed(self, user):
        embed=discord.Embed(description=f"Skipped to shiny frame!\nCurrent Frame: {user.frame}", color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        return embed
    
    def create_items_view_table(self, user, items):
        embed=discord.Embed(color=default_color)
        embed.set_author(name=user.name)
        if user.profile_image and user.profile_image != 'None':
            embed.set_thumbnail(url=user.profile_image)
        for item in items:
            embed.add_field(name=item.name, value=item.quantity, inline=True)
        return embed
    
    def create_shop_view_table(self, user, items):
        embed=discord.Embed(description="Goomybot Shop", color=default_color)
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        for key, value in items.items():
            embed.add_field(name=key, value=f"${value:,.0f}\n", inline=True)
        embed.set_footer(text='.buy <item_name> <quantity>')
        return embed

    def create_odds_table(self, user):
        odds = Odds()
        embed=discord.Embed(description=f"Goomybot Odds\n{odds}", color=default_color)
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_flex_embed(self, user, pokemon):
        embed=discord.Embed(title=f"{pokemon.name.capitalize()}", color=0xf5a8ff)
        embed.set_image(url=pokemon.sprite_front)
        embed.set_footer(text=f'Spawned by {user.name}')
        return embed
    
    def create_rerolliv_view(self, user, pokemon):
        embed=discord.Embed(color=self.get_color(pokemon=pokemon))
        for key, value in pokemon.iv.items():
            embed.add_field(name=key, value = value, inline=True)
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_bug_reported_embed(self, user):
        embed=discord.Embed(description= "Bug Reported!", color=default_color)
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_bug_log_embed(self, user, content):
        embed=discord.Embed(description= content, color=default_color)
        embed.set_author(name=f"Reported By: {user.name}")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_lottery_embed(self, user, content):
        embed=discord.Embed(description= content, color=default_color)
        if user:
            embed.set_author(name=f"{user.name}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_release_embed(self, user, content):
        embed=discord.Embed(description= content, color=default_color)
        if user:
            embed.set_author(name=f"{user.name}")
        else:
            embed.set_author(name=f"Goomybot")
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed
    
    def create_safe_pokemon_view(self, user, pokemon):
        embed=discord.Embed(description=f"Marked Safe! {pokemon.__str__()}", color=self.get_color(pokemon=pokemon))
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=pokemon.sprite_front)
        return embed

    def create_safe_pokemon_failure_view(self, user):
        embed=discord.Embed(description=f"Could not mark safe! Please try again!", color=default_color)
        embed.set_author(name=user.name)
        embed.set_thumbnail(url=r'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/704.png')
        return embed