import datetime
import uuid
import json # Added for potential JSON string handling for complex types if they were present
import logging # For logging warnings, as seen in your example

# Basic logger setup, you might have a more sophisticated setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from typing import List, Optional, Dict, Any

class Lottery:
    """
    Represents a record in the public.lottery table.
    """

    def __init__(
        self,
        id: str, # id is a primary key, so it should always be present after creation
        user_ids: List[int],
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        amount: int,
    ):
        """
        Initializes a Lottery object.

        Args:
            id (str): The unique identifier for the lottery (UUID as string).
            user_ids (List[int]): A list of user IDs participating in the lottery.
            start_time (datetime.datetime): The start time of the lottery.
            end_time (datetime.datetime): The end time of the lottery.
            amount (int): The prize amount of the lottery.
        """
        self.id = id
        self.user_ids = user_ids
        self.start_time = start_time
        self.end_time = end_time
        self.amount = amount

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Lottery object to a dictionary, suitable for database insertion
        or serialization (e.g., to JSON). Handles UUID and datetime conversions for storage.
        """
        data = self.__dict__.copy()

        # Convert UUID object (if we ever stored it as UUID type, but current init is str) to string for storage
        # The schema defines 'id' as UUID, which typically gets stored as string in Python
        # If self.id was ever a uuid.UUID object, uncomment this:
        if isinstance(data.get('id'), uuid.UUID):
            data['id'] = str(data['id'])

        # Convert datetime objects to ISO format strings for storage
        if isinstance(data.get('start_time'), datetime.datetime):
            data['start_time'] = data['start_time'].isoformat()
        else:
            data['start_time'] = None # Ensure it's None if not a datetime object

        if isinstance(data.get('end_time'), datetime.datetime):
            data['end_time'] = data['end_time'].isoformat()
        else:
            data['end_time'] = None # Ensure it's None if not a datetime object

        # user_ids (list of bigint) should be handled as list of int in Python
        # No special conversion needed for a simple list of integers for to_dict,
        # assuming the database driver handles `list[int]` to `bigint[]` conversion.
        if not isinstance(data.get('user_ids'), list):
            data['user_ids'] = [] # Ensure it's a list

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lottery":
        """
        Creates a Lottery instance from a dictionary (e.g., typically from a database row or cache).
        Handles potential UUID, datetime, list, and integer conversions.
        """
        processed_data = data.copy()

        # --- UUID Handling for 'id' ---
        # The database stores UUID, which often comes back as a string.
        # Ensure it's a string, as our __init__ expects a string for 'id'.
        if 'id' in processed_data and processed_data['id'] is not None:
            if isinstance(processed_data['id'], uuid.UUID):
                processed_data['id'] = str(processed_data['id'])
            elif not isinstance(processed_data['id'], str):
                logger.warning(f"Lottery.from_dict: 'id' has unexpected type {type(processed_data['id'])}. Attempting conversion to string.")
                try:
                    processed_data['id'] = str(processed_data['id'])
                except Exception as e:
                    logger.error(f"Lottery.from_dict: Failed to convert 'id' to string: {e}. Setting to a new UUID.")
                    processed_data['id'] = str(uuid.uuid4()) # Fallback to a new UUID if conversion fails
        else:
            logger.warning("Lottery.from_dict: 'id' missing or None. Generating a new UUID.")
            processed_data['id'] = str(uuid.uuid4()) # Generate a new UUID if missing or None

        # --- List of BigInt Handling for 'user_ids' ---
        if 'user_ids' in processed_data and processed_data['user_ids'] is not None:
            if isinstance(processed_data['user_ids'], str):
                # If it comes as a string (e.g., from Redis without proper JSON handling)
                try:
                    # Attempt to parse as JSON list, then convert elements to int
                    parsed_list = json.loads(processed_data['user_ids'])
                    processed_data['user_ids'] = [int(x) for x in parsed_list if x is not None]
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Lottery.from_dict: Could not parse 'user_ids' string '{processed_data['user_ids']}' as list of int. Setting to empty list. Error: {e}")
                    processed_data['user_ids'] = []
            elif isinstance(processed_data['user_ids'], list):
                # Ensure all elements in the list are integers
                cleaned_user_ids = []
                for uid in processed_data['user_ids']:
                    if isinstance(uid, int):
                        cleaned_user_ids.append(uid)
                    elif isinstance(uid, str):
                        try:
                            cleaned_user_ids.append(int(uid))
                        except ValueError:
                            logger.warning(f"Lottery.from_dict: Could not convert user_id '{uid}' to int. Skipping.")
                    else:
                        logger.warning(f"Lottery.from_dict: user_id '{uid}' has unexpected type {type(uid)}. Skipping.")
                processed_data['user_ids'] = cleaned_user_ids
            else:
                logger.warning(f"Lottery.from_dict: 'user_ids' has unexpected type {type(processed_data['user_ids'])}. Setting to empty list.")
                processed_data['user_ids'] = []
        else:
            processed_data['user_ids'] = [] # Default to empty list if missing or None

        # --- Datetime Handling (start_time, end_time) ---
        for key in ['start_time', 'end_time']:
            if key in processed_data and processed_data[key] is not None:
                if isinstance(processed_data[key], str):
                    try:
                        # Use fromisoformat for robustness with timezone info
                        dt_obj = datetime.datetime.fromisoformat(processed_data[key])
                        # Ensure timezone awareness, default to UTC if naive
                        processed_data[key] = dt_obj if dt_obj.tzinfo is not None else dt_obj.replace(tzinfo=datetime.timezone.utc)
                    except ValueError:
                        logger.warning(f"Lottery.from_dict: Invalid datetime string for {key}: '{processed_data[key]}'. Setting to None.")
                        processed_data[key] = None
                elif isinstance(processed_data[key], datetime.datetime):
                    # Ensure datetime objects are timezone-aware, default to UTC if naive
                    if processed_data[key].tzinfo is None:
                        processed_data[key] = processed_data[key].replace(tzinfo=datetime.timezone.utc)
                else:
                    logger.warning(f"Lottery.from_dict: '{key}' has unexpected type {type(processed_data[key])}. Setting to None.")
                    processed_data[key] = None
            else:
                processed_data[key] = None # Explicitly set to None if missing or None

        # --- Integer Handling for 'amount' ---
        if 'amount' in processed_data and processed_data['amount'] is not None:
            if isinstance(processed_data['amount'], str):
                try:
                    processed_data['amount'] = int(processed_data['amount'])
                except ValueError:
                    logger.warning(f"Lottery.from_dict: Could not convert 'amount' value '{processed_data['amount']}' to int. Setting to 0.")
                    processed_data['amount'] = 0 # Default to 0
            elif not isinstance(processed_data['amount'], int):
                logger.warning(f"Lottery.from_dict: 'amount' has unexpected type {type(processed_data['amount'])}. Setting to 0.")
                processed_data['amount'] = 0
        else:
            processed_data['amount'] = 0 # Default to 0 if missing or None

        # Ensure all required attributes are present, even if defaults are used above
        # This is a bit redundant with the above but serves as a final check before instantiation
        for attr in ['id', 'user_ids', 'start_time', 'end_time', 'amount']:
            if attr not in processed_data or processed_data[attr] is None:
                # If 'id' is missing, it would have been generated.
                # If 'user_ids' is missing, it would have been defaulted to [].
                # If 'amount' is missing, it would have been defaulted to 0.
                # start_time and end_time can genuinely be None, as per schema and common usage for new entries
                if attr not in ['start_time', 'end_time']:
                     logger.error(f"Lottery.from_dict: Critical attribute '{attr}' missing after processing. This indicates an issue.")
                # Fallback for start_time/end_time if they MUST be datetime objects for init
                # For this specific schema, None is acceptable so no fallback to now() needed here unless desired.
                # processed_data[attr] = default_value_for_attr(attr) # Example: datetime.datetime.now(datetime.timezone.utc) for times


        return cls(**processed_data)

    def __repr__(self):
        return (
            f"Lottery(id='{self.id}', user_ids={self.user_ids}, "
            f"start_time={self.start_time.isoformat() if self.start_time else 'None'}, "
            f"end_time={self.end_time.isoformat() if self.end_time else 'None'}, "
            f"amount={self.amount})"
        )