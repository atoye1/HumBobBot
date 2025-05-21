# domain/cafeteria/cafeteria_crud.py
"""
This module provides CRUD (Create, Read, Update, Delete) operations
for Cafeteria related data in the database.

Currently, it focuses on retrieving cafeteria information:
- Fetching a cafeteria's unique ID based on its location name.
- Fetching the meal operation times for a cafeteria.
"""
from typing import List, Optional # Optional added for return type hinting
import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound # To handle cases where .one() might fail
import logging # For logging

from models import Cafeteria

logger = logging.getLogger(__name__) # Initialize logger

def get_cafeteria_id(db: Session, location: str) -> Optional[int]:
    """
    Retrieves the unique ID of a cafeteria based on its location name.

    Args:
        db (Session): The database session.
        location (str): The canonical location name of the cafeteria (e.g., "본사", "노포").

    Returns:
        Optional[int]: The ID of the cafeteria if found, otherwise None.
    """
    try:
        # Query the Cafeteria table for a record matching the given location.
        # .one() will raise NoResultFound if no record matches, or MultipleResultsFound if multiple match.
        cafeteria = db.query(Cafeteria).filter_by(location=location).one()
        return cafeteria.id
    except NoResultFound:
        logger.warning(f"No cafeteria found for location: {location}")
        return None
    except Exception as e: # Catch other potential SQLAlchemy errors
        logger.error(f"Error fetching cafeteria ID for location {location}: {e}", exc_info=True)
        return None

def get_operation_times(db: Session, cafeteria_id: int) -> Optional[List[Optional[datetime.time]]]:
    """
    Retrieves the meal operation times for a cafeteria given its ID.

    The times are returned as a list in the following order:
    [breakfast_start, breakfast_end, lunch_start, lunch_end, dinner_start, dinner_end]
    Any of these times can be None if not set in the database.

    Args:
        db (Session): The database session.
        cafeteria_id (int): The unique ID of the cafeteria.

    Returns:
        Optional[List[Optional[datetime.time]]]: A list of `datetime.time` objects
                                                 representing the meal times, or None
                                                 if the cafeteria is not found.
                                                 Individual times within the list can also be None.
    """
    try:
        # Retrieve the cafeteria by its primary key (ID).
        # .get() is a shortcut for fetching by primary key and returns None if not found.
        cafeteria: Optional[Cafeteria] = db.query(Cafeteria).get(cafeteria_id)
        if cafeteria:
            return [
                cafeteria.breakfast_start_time, cafeteria.breakfast_end_time,
                cafeteria.lunch_start_time, cafeteria.lunch_end_time,
                cafeteria.dinner_start_time, cafeteria.dinner_end_time
            ]
        else:
            logger.warning(f"No cafeteria found with ID: {cafeteria_id} when trying to get operation times.")
            return None
    except Exception as e:
        logger.error(f"Error fetching operation times for cafeteria ID {cafeteria_id}: {e}", exc_info=True)
        return None