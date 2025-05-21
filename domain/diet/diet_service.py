# domain/diet/diet_service.py
"""
This module provides services related to diet information processing.

It includes:
- `DietUploadService`: A service class for processing uploaded diet-related data,
  such as extracting information from post titles, determining start dates,
  and identifying cafeteria details.
- `ProcessedDietData`: A Pydantic model representing the structured data
  derived from the diet upload process.
- `determine_location_from_utterance`: A function to determine cafeteria location
  from a user's text utterance.
"""
from pydantic import BaseModel
import datetime
import re
import os
from typing import List, Optional

from constants.cafeteria import CAFETERIA_NAME_TO_ID_MAP, CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES 
from utils.date_util import get_next_monday, get_last_monday


class ProcessedDietData(BaseModel):
    """
    Represents structured data extracted and processed from a diet information upload.

    Attributes:
        post_title (str): The original title of the diet post.
        post_create_date (datetime.datetime): The creation date of the diet post, parsed into a datetime object.
        start_date (datetime.datetime): The determined start date for the diet menu (typically a Monday).
        cafeteria_id (int): The unique identifier for the cafeteria.
        cafeteria_name_for_file (str): The canonical name of the cafeteria, used for generating filenames.
        img_url (str): The web-accessible URL for the diet image.
        img_path (str): The local filesystem path where the diet image is (or will be) stored.
        upload_file_name (str): The original filename of the uploaded diet image.
    """
    post_title: str
    post_create_date: datetime.datetime
    start_date: datetime.datetime
    cafeteria_id: int
    cafeteria_name_for_file: str 
    img_url: str
    img_path: str
    upload_file_name: str


class DietUploadService:
    """
    Service class for processing diet information uploads.

    This class encapsulates the logic for extracting meaningful data from
    raw diet post information, such as determining the diet's start date,
    identifying the cafeteria, and preparing paths for image storage.
    """
    def _extract_date_from_title(self, post_title: str) -> Optional[datetime.datetime]:
        """
        Extracts a potential start date from the diet post title using regex.

        It searches for various date patterns (e.g., "MM/DD", "YYYY/MM/DD", "MM월 DD일")
        and, if found, normalizes it and returns the preceding Monday.

        Args:
            post_title (str): The title of the diet post.

        Returns:
            Optional[datetime.datetime]: The determined start date (a Monday) if a date
                                         is found in the title, otherwise None.
        """
        # Multiple regex patterns to catch various date formats
        date_patterns = [
            r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}\b",  # Optional YYYY/ and MM/DD
            r"\b\d{4}/\d{1,2}/\d{1,2}\b",        # YYYY/MM/DD
            r"\b\d{1,2}/\d{1,2}\b",              # MM/DD
            r"\b\d{1,2}\.\d{1,2}\b",              # MM.DD
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",        # YYYY-MM-DD
            r"\b\d{1,2}-\d{1,2}\b",              # MM-DD
            r"\b\d{1,2}월\s?\d{1,2}일\b",         # MM월 DD일 (Korean format)
        ]
        date_regex = re.compile("|".join(date_patterns))
        extracted_dates = date_regex.findall(post_title)
        
        # Normalize found date strings
        extracted_dates = [
            date.replace(".", "/").replace("-", "/").replace("월", "/").replace("일", "").replace(" ", "")
            for date in extracted_dates
        ]
        if not extracted_dates:
            return None
        
        datetime_list = []
        current_year = datetime.datetime.now().year
        for date_str in extracted_dates:
            parts = date_str.split('/')
            year = current_year
            if len(parts) == 3: # YYYY/MM/DD format, use the given year
                try: # Check if the first part is a year
                    potential_year = int(parts[0])
                    if 2000 <= potential_year <= current_year + 5: # Plausible year range
                        year = potential_year
                        month, day = int(parts[1]), int(parts[2])
                    else: # First part is not a year, assume MM/DD/something or MM/DD/YY
                        month, day = int(parts[0]), int(parts[1])
                except ValueError: # First part not an int, assume MM/DD
                     month, day = int(parts[0]), int(parts[1])
            elif len(parts) == 2: # MM/DD format
                month, day = int(parts[0]), int(parts[1])
            else:
                continue # Skip invalid formats
            
            try:
                datetime_list.append(datetime.datetime(year, month, day))
            except ValueError: # Handles invalid dates like Feb 30
                continue 
                
        if not datetime_list:
            return None
        
        datetime_list.sort() # Get the earliest date found
        return get_last_monday(datetime_list[0]) # Return the Monday of that week

    def _determine_start_date(self, post_title: str, parsed_post_create_date: datetime.datetime) -> datetime.datetime:
        """
        Determines the effective start date for the diet menu.

        It first tries to extract a date from the post title. If successful,
        that date (adjusted to the preceding Monday) is used. Otherwise,
        it defaults to the next Monday following the post's creation date.

        Args:
            post_title (str): The title of the diet post.
            parsed_post_create_date (datetime.datetime): The creation date of the post.

        Returns:
            datetime.datetime: The determined start date for the diet menu.
        """
        extracted_start_date = self._extract_date_from_title(post_title)
        return extracted_start_date or get_next_monday(parsed_post_create_date)

    def _determine_cafeteria_info(self, post_title: str) -> tuple[Optional[int], Optional[str]]:
        """
        Determines the cafeteria ID and its canonical name from the post title.

        It iterates through known cafeteria name variations (from `CAFETERIA_NAME_TO_ID_MAP`)
        and checks for their presence in the post title.

        Args:
            post_title (str): The title of the diet post.

        Returns:
            tuple[Optional[int], Optional[str]]: A tuple containing the cafeteria ID
                                                 and its canonical name for filenames.
                                                 Returns (None, None) if no match is found.
        """
        for name_variation, c_id in CAFETERIA_NAME_TO_ID_MAP.items():
            if name_variation in post_title:
                # Ensure the found ID is valid and has a corresponding canonical name
                if 0 < c_id <= len(CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES):
                    return c_id, CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES[c_id - 1] 
        return None, None

    def process_diet_upload_data(
        self,
        post_title: str,
        post_create_date_str: str, # e.g., "231130" for YYMMDD
        upload_file_name: str 
    ) -> ProcessedDietData:
        """
        Processes raw diet upload data to produce structured `ProcessedDietData`.

        This involves parsing the post creation date, determining the diet start date,
        identifying the cafeteria, and constructing image URLs and paths.

        Args:
            post_title (str): The title of the diet post.
            post_create_date_str (str): The creation date of the post as a string (format YYMMDD).
            upload_file_name (str): The original filename of the uploaded image.

        Returns:
            ProcessedDietData: An object containing all processed information.

        Raises:
            ValueError: If the cafeteria name cannot be determined from the title or
                        if there's a mapping issue.
        """
        parsed_post_create_date = datetime.datetime.strptime(post_create_date_str, '%y%m%d')
        
        start_date = self._determine_start_date(post_title, parsed_post_create_date)
        
        cafeteria_id, cafeteria_name_for_file = self._determine_cafeteria_info(post_title)
        if cafeteria_id is None or cafeteria_name_for_file is None:
            raise ValueError('Invalid cafeteria name in post title or mapping issue.')

        # Construct image filename and paths
        img_filename = f'{start_date.strftime("%y%m%d")}_{cafeteria_name_for_file}.jpg'
        img_url = f'image/diet/{img_filename}' # Web-accessible URL path
        
        # Determine absolute base directory for assets path construction
        # Assumes this service file is in domain/diet/
        # So, ../../.. takes it to the project root where 'assets' should be.
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        img_path = os.path.join(base_dir, 'assets', 'image', 'diet', img_filename) # Filesystem path

        return ProcessedDietData(
            post_title=post_title,
            post_create_date=parsed_post_create_date,
            start_date=start_date,
            cafeteria_id=cafeteria_id,
            cafeteria_name_for_file=cafeteria_name_for_file,
            img_url=img_url,
            img_path=img_path,
            upload_file_name=upload_file_name
        )

def determine_location_from_utterance(utterance: str) -> Optional[str]:
    """
    Determines a canonical cafeteria location name from a user's utterance.

    It checks the utterance against known cafeteria name variations (defined in
    `CAFETERIA_NAME_TO_ID_MAP`). If a match is found, it returns the
    corresponding canonical name (from `CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES`).

    Args:
        utterance (str): The user's text input (e.g., "본사 식단 알려줘").

    Returns:
        Optional[str]: The canonical name of the matched cafeteria (e.g., "본사"),
                       or None if no known cafeteria is mentioned.
    """
    for name_variation, c_id in CAFETERIA_NAME_TO_ID_MAP.items():
        if name_variation in utterance: # Check if any known name variation is in the utterance
            # Ensure the ID is valid for the canonical names list
            if 0 < c_id <= len(CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES):
                return CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES[c_id - 1] # Return the canonical name
    return None
