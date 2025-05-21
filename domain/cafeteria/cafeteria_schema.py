# domain/cafeteria/cafeteria_schema.py
"""
This module defines Pydantic schemas and enumerations related to cafeteria data.

Currently, it includes an enumeration for canonical cafeteria location names,
which can be used for type hinting, validation, or defining choices in API requests
or data models.
"""
from enum import Enum

class CafeteriaLocationEnum(str, Enum):
    """
    Enumeration of canonical cafeteria location names.

    This enum provides a standardized set of cafeteria location names.
    Using this enum can help ensure consistency when referring to cafeteria
    locations throughout the application (e.g., in database models,
    API request parameters, or internal logic).

    The values are the Korean names of the cafeterias.
    """
    본사 = "본사"      # Head Office
    노포 = "노포"      # Nopo
    신평 = "신평"      # Sinpyeong
    호포 = "호포"      # Hopo
    광안 = "광안"      # Gwangan
    대저 = "대저"      # Daejeo
    경전철 = "경전철"  # Light Rail Transit