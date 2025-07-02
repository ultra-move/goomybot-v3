import random


class Team:

    def __init__(self, id, user_ids, team_name, rewards):
        self.id = id
        self.user_ids = user_ids
        self.team_name = team_name
        self.rewards = rewards

    def random_reward(self):
        items = {
            'rerolliv': 2000,
            'rarecandy': 3000,
            'resetseed': 5000,
            'raidpass': 5000,
            'skipframe': 10000,
            'skipraidframe': 50000,
            'regionpass': 100000
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
            if item_name == 'regionpass':
                quantity = 1
            if item_name == 'skipraidframe':
                quantity = random.randrange(1,3)
            elif item_name == 'skipframe':
                quantity = random.randrange(5,10)
            else:
                quantity = random.randrange(10,20)
            
        if reward_type == 'money' or reward_type == 'both':
            money = random.randrange(25000, 40000)
            money = round(money / 100) * 100
        #{item: {name: "", quantity: ""}, money: 0}
        self.reward = {'item': {'name': item_name, 'quantity': quantity*tier}, 'money': money*tier}

    def random_condition(self):
        pokemon_types = ["Normal","Fire","Water","Grass","Flying","Fighting","Poison","Electric","Ground","Rock","Psychic","Ice","Bug","Ghost","Steel","Dragon","Dark","Fairy"]
        tier = random.randrange(1,5)
        quantity = 50*tier
        shiny_count = 3*tier
        pokemon_type = random.choice(pokemon_types)
        self.condition = {'pokedex_id': pokedex_id, 'tier': tier, "quantity": quantity}