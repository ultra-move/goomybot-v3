import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class FlexLog:
    """
    Represents a record in the public.flex_log table.
    """

    def __init__(
        self,
        id: Optional[uuid.UUID] = None,
        user_id: int = None,
        channel_id: Optional[int] = None,
        name: Optional[str] = None,
        status: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        expiration_date: Optional[datetime] = None
    ):
        """
        Initializes a new FlexLog instance.

        Args:
            id (Optional[uuid.UUID]): The unique identifier for the log entry.
                                     If None, a new UUID will be generated upon creation
                                     for database insertion, but typically you'd load
                                     existing UUIDs from the DB.
            user_id (Optional[uuid.UUID]): The UUID of the user associated with the log.
            channel_id (Optional[int]): The ID of the channel.
            name (Optional[str]): The name associated with the log entry.
            status (Optional[str]): The status of the log entry.
            timestamp (Optional[datetime]): The timestamp of the log entry.
                                           It's recommended to store timezone-aware datetimes.
                                           If None, current UTC time is used for `to_dict`
                                           if ID is also None (implying a new record).
        """
        self.id = id if id is not None else uuid.uuid4() # Assign a new UUID if not provided for new records
        self.user_id = user_id
        self.channel_id = channel_id
        self.name = name
        self.status = status
        self.timestamp = timestamp
        self.expiration_date = expiration_date

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the FlexLog instance into a dictionary suitable for database insertion/update.

        Handles UUID objects and datetime objects for proper serialization.
        Ensures timestamp is timezone-aware and defaults to now if not set for new records.
        """
        data: Dict[str, Any] = {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "channel_id": self.channel_id,
            "name": self.name,
            "status": self.status,
            "expiration_date": self.expiration_date
        }

        # Ensure timestamp is timezone-aware for PostgreSQL's timestamp with time zone
        if self.timestamp:
            if self.timestamp.tzinfo is None:
                # Assume UTC if no timezone info, or convert if you have a local time
                data["timestamp"] = self.timestamp.replace(tzinfo=timezone.utc)
            else:
                data["timestamp"] = self.timestamp
        elif self.id is None: # Only set default timestamp if creating a new record (id is None)
             data["timestamp"] = datetime.now(timezone.utc)
        else:
             data["timestamp"] = None # If it's an existing record and timestamp is None, keep it None

        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FlexLog':
        """
        Creates a FlexLog instance from a dictionary (e.g., from a database query result).

        Handles conversion of UUID strings back to UUID objects and
        timestamp strings/objects back to datetime objects.
        """
        flex_log_id = uuid.UUID(data["id"]) if data.get("id") else None
        user_id = int(data["user_id"]) if data.get("user_id") else None
        channel_id = int(data["channel_id"]) if data.get("channel_id") is not None else None
        name = data.get("name")
        status = data.get("status")

        timestamp = None
        if data.get("timestamp"):
            if isinstance(data["timestamp"], str):
                # Attempt to parse string to datetime.
                # PostgreSQL often returns ISO format, so handle that.
                try:
                    timestamp = datetime.fromisoformat(data["timestamp"])
                except ValueError:
                    # Fallback for other potential string formats or just leave as None
                    print(f"Warning: Could not parse timestamp string: {data['timestamp']}")
                    timestamp = None
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        if data.get("expiration_date"):
            if isinstance(data["expiration_date"], str):
                # Attempt to parse string to datetime.
                # PostgreSQL often returns ISO format, so handle that.
                try:
                    expiration_date = datetime.fromisoformat(data["expiration_date"])
                except ValueError:
                    # Fallback for other potential string formats or just leave as None
                    print(f"Warning: Could not parse expiration_date string: {data['expiration_date']}")
                    expiration_date = None
            elif isinstance(data["expiration_date"], datetime):
                timestamp = data["expiration_date"]

        return FlexLog(
            id=flex_log_id,
            user_id=user_id,
            channel_id=channel_id,
            name=name,
            status=status,
            timestamp=timestamp,
            expiration_date=expiration_date
        )

    def __repr__(self):
        return (
            f"FlexLog(id={self.id}, user_id={self.user_id}, channel_id={self.channel_id}, "
            f"name='{self.name}', status='{self.status}', timestamp={self.timestamp} expiration_date={self.expiration_date})"
        )