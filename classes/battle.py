import uuid
import datetime
import json  # <--- IMPORTANT: Import json
from typing import List, Dict, Any, Optional

class Battle:
    """
    Represents an active battle instance in the Goomybot system,
    mapping directly to the 'battles' PostgreSQL table.
    """

    def __init__(self,
                 id: uuid.UUID,
                 user_ids: List[int],
                 local_id: int,
                 channel_id: int,
                 start_time: datetime.datetime,
                 duration: int,
                 end_time: datetime.datetime,
                 rewards: Dict[str, Any],
                 status: str,
                 battle_pokemon_id: Optional[uuid.UUID] = None):
        """
        Initializes a Battle object.

        Args:
            id (uuid.UUID): The unique identifier for this battle.
            user_ids (List[int]): A list of Discord user IDs participating in the battle.
            start_time (datetime.datetime): The timestamp when the battle started.
            duration (int): The planned duration of the battle in seconds.
            end_time (datetime.datetime): The calculated timestamp when the battle is expected to end.
            rewards (Dict[str, Any]): A dictionary containing rewards (e.g., {'money': 123, 'item': 'potion'}).
            status (str): The current status of the battle (e.g., 'active', 'caught', 'fled', 'completed').
            battle_pokemon_id (Optional[uuid.UUID]): The ID of the specific wild Pokémon involved in this battle,
                                                      if applicable (links to a potential 'battle_pokemon' table).
        """
        self.id = id
        self.user_ids = user_ids
        self.local_id = local_id
        self.channel_id = channel_id
        self.start_time = start_time
        self.duration = duration
        self.end_time = end_time
        self.rewards = rewards
        self.status = status
        self.battle_pokemon_id = battle_pokemon_id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Battle':
        """
        Creates a Battle object from a dictionary, typically obtained from a database query result.
        When reading from the database, the JSONB column 'rewards' will likely already be
        deserialized into a Python dict by the database driver (e.g., psycopg2),
        so no json.loads() is typically needed here.

        Args:
            data (Dict[str, Any]): A dictionary containing battle data, matching the database column names.

        Returns:
            Battle: An initialized Battle object.
        """
        battle_id = uuid.UUID(data['id'])

        battle_pokemon_id = None
        if data.get('battle_pokemon_id'):
            battle_pokemon_id = uuid.UUID(data['battle_pokemon_id'])

        # Most PostgreSQL drivers (like psycopg2) will return datetime objects directly
        # for TIMESTAMP WITH TIME ZONE, but handling strings for robustness is good.
        start_time_dt = data['start_time']
        if isinstance(start_time_dt, str):
            start_time_dt = datetime.datetime.fromisoformat(start_time_dt)

        end_time_dt = data['end_time']
        if isinstance(end_time_dt, str):
            end_time_dt = datetime.datetime.fromisoformat(end_time_dt)

        # Rewards should already be a Python dict when coming from JSONB column
        # if the database driver handles deserialization.
        rewards_data = data['rewards']
        # If your driver returns it as a string despite JSONB, you would add:
        # if isinstance(rewards_data, str):
        #    rewards_data = json.loads(rewards_data)


        return cls(
            id=battle_id,
            user_ids=data['user_ids'],
            local_id=data['local_id'],
            channel_id=data['channel_id'],
            start_time=start_time_dt,
            duration=data['duration'],
            end_time=end_time_dt,
            rewards=rewards_data, # Use the potentially deserialized rewards_data
            status=data['status'],
            battle_pokemon_id=battle_pokemon_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Battle object into a dictionary suitable for database insertion or update.
        Crucially, it serializes the 'rewards' dictionary into a JSON string
        for the PostgreSQL JSONB column.

        Returns:
            Dict[str, Any]: A dictionary representing the battle data, ready for the database.
        """
        battle_id_str = str(self.id)
        battle_pokemon_id_str = str(self.battle_pokemon_id) if self.battle_pokemon_id else None

        start_time_str = self.start_time.isoformat()
        end_time_str = self.end_time.isoformat()

        # <--- THIS IS THE CRUCIAL CHANGE! --- >
        # Convert the Python dictionary self.rewards into a JSON string
        # for storage in the PostgreSQL JSONB column.
        rewards_json_string = json.dumps(self.rewards)

        return {
            'id': battle_id_str,
            'user_ids': self.user_ids,
            'local_id': self.local_id,
            'channel_id': self.channel_id,
            'start_time': start_time_str,
            'duration': self.duration,
            'end_time': end_time_str,
            'rewards': rewards_json_string, # Now passing a JSON string
            'status': self.status,
            'battle_pokemon_id': battle_pokemon_id_str
        }
    
    def __str__(self):
         return (
            f"--- Battle Details ---\n"
            f"ID: {self.id}\n"
            f"User IDs: {self.user_ids}\n"
            f"Local ID: {self.local_id}\n"
            f"Channel ID: {self.channel_id}\n"
            f"Status: {self.status}\n"
            f"Pokemon ID: {self.battle_pokemon_id}\n"
            )