from pydantic import BaseModel
import datetime
import re
import os
from typing import List, Optional # Added Optional

# Assuming constants/cafeteria.py will be updated as described below
# These imports will be resolved once constants/cafeteria.py is updated
from constants.cafeteria import CAFETERIA_NAME_TO_ID_MAP, CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES 
from utils.date_util import get_next_monday, get_last_monday # Ensure these are correctly pathed if moved


class ProcessedDietData(BaseModel):
    post_title: str
    post_create_date: datetime.datetime
    start_date: datetime.datetime
    cafeteria_id: int
    cafeteria_name_for_file: str # Canonical name for filename
    img_url: str
    img_path: str
    upload_file_name: str # Original filename from UploadFile


class DietUploadService:
    def _extract_date_from_title(self, post_title: str) -> Optional[datetime.datetime]:
        # (Logic from DietUpload.extract_date_from_title)
        # Ensure it returns Optional[datetime.datetime]
        date_patterns = [
            r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}\b",
            r"\b\d{4}/\d{1,2}/\d{1,2}\b",
            r"\b\d{1,2}/\d{1,2}\b",
            r"\b\d{1,2}\.\d{1,2}\b",
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
            r"\b\d{1,2}-\d{1,2}\b",
            r"\b\d{1,2}월\s?\d{1,2}일\b",
        ]
        date_regex = re.compile("|".join(date_patterns))
        extracted_dates = date_regex.findall(post_title)
        extracted_dates = [
            date.replace(".", "/").replace("-", "/").replace("월", "/").replace("일", "").replace(" ", "")
            for date in extracted_dates
        ]
        if not extracted_dates:
            return None
        datetime_list = []
        year = datetime.datetime.now().year
        for date_str in extracted_dates: # Renamed 'date' to 'date_str' to avoid conflict
            splitted_date = date_str.split('/')
            if len(splitted_date) == 3: # Handles YYYY/MM/DD, takes MM/DD
                month, day = splitted_date[1], splitted_date[2]
            elif len(splitted_date) == 2: # Handles MM/DD
                month, day = splitted_date[0], splitted_date[1]
            else:
                continue # Skip invalid formats
            datetime_list.append(datetime.datetime(year, int(month), int(day)))
        if not datetime_list:
            return None
        datetime_list.sort()
        return get_last_monday(datetime_list[0])


    def _determine_start_date(self, post_title: str, parsed_post_create_date: datetime.datetime) -> datetime.datetime:
        # (Logic from DietUpload.set_start_date)
        extracted_start_date = self._extract_date_from_title(post_title)
        return extracted_start_date or get_next_monday(parsed_post_create_date)

    def _determine_cafeteria_info(self, post_title: str) -> tuple[Optional[int], Optional[str]]:
        # (Logic from DietUpload.set_cafeteria_id using the new CAFETERIA_NAME_TO_ID_MAP)
        # Returns (cafeteria_id, canonical_name_for_file)
        for name_variation, c_id in CAFETERIA_NAME_TO_ID_MAP.items():
            if name_variation in post_title:
                if 0 < c_id <= len(CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES):
                     # Ensure ID is valid for CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES
                    return c_id, CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES[c_id - 1] 
        return None, None # If no match found

    def process_diet_upload_data(
        self,
        post_title: str,
        post_create_date_str: str, # e.g., "231130"
        upload_file_name: str # Original filename from UploadFile
    ) -> ProcessedDietData:
        parsed_post_create_date = datetime.datetime.strptime(post_create_date_str, '%y%m%d')
        
        start_date = self._determine_start_date(post_title, parsed_post_create_date)
        
        cafeteria_id, cafeteria_name_for_file = self._determine_cafeteria_info(post_title)
        if cafeteria_id is None or cafeteria_name_for_file is None:
            raise ValueError('Invalid cafeteria name in post title or mapping issue.')

        img_filename = f'{start_date.strftime("%y%m%d")}_{cafeteria_name_for_file}.jpg'
        img_url = f'image/diet/{img_filename}'
        # Ensure assets directory exists, using relative path from project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        img_path = os.path.join(base_dir, 'assets', 'image', 'diet', img_filename)


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
    # Logic adapted from old DietUtterance.set_location
    # It should use the keys of CAFETERIA_NAME_TO_ID_MAP for matching
    # The original logic used two separate lists (full_name_list, semi_name_list)
    # We need to decide what the canonical "location" string returned should be.
    # The old DietUtterance.set_location returned the 'full_name' (e.g., "본사", "경전철").
    # Let's find the ID first, then map back to a canonical name if needed, or just return the matched key.
    # The CAFETERIA_NAME_TO_ID_MAP maps variations to an ID.
    # We need a way to get a canonical display name from an ID or a matched variation.
    # Let's assume for now we return the first key that matched from CAFETERIA_NAME_TO_ID_MAP,
    # or better, a canonical name associated with the ID.
    # The CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES is indexed by ID-1.

    # Simplified logic: iterate through map keys. If a key is in utterance, find its ID, then get canonical name.
    for name_variation, c_id in CAFETERIA_NAME_TO_ID_MAP.items():
        if name_variation in utterance:
            if 0 < c_id <= len(CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES):
                # Return the canonical name for that ID
                return CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES[c_id - 1]
    return None # If no location is found
