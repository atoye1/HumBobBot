# constants/cafeteria.py
"""
This module defines constants related to cafeteria identification and naming.

These constants are used throughout the application to:
- Map various cafeteria name spellings or aliases (e.g., from post titles or user utterances) 
  to unique cafeteria IDs.
- Provide canonical names for cafeterias, often used for generating filenames or for display purposes.

The primary goal is to have a centralized place for managing cafeteria-related identifiers,
making the system more robust to variations in naming and easier to update if cafeteria
information changes.
"""

# CAFETERIA_NAME_TO_ID_MAP:
# This dictionary serves as a comprehensive mapping from various possible string representations
# of cafeteria names (including Korean names, English transliterations, or common aliases)
# to a standardized, unique integer ID for each cafeteria.
# This is crucial for parsing cafeteria information from unstructured text sources like
# diet post titles or user messages.
# Example: "본사", "HumetroHQ" both map to ID 1.
CAFETERIA_NAME_TO_ID_MAP = {
    # ID 1: 본사 (Head Office)
    "본사": 1, "HumetroHQ": 1,
    # ID 2: 노포 (Nopo)
    "노포": 2, "Nopo": 2,
    # ID 3: 신평 (Sinpyeong)
    "신평": 3, "Sinpyeong": 3,
    # ID 4: 호포 (Hopo)
    "호포": 4, "Hopo": 4,
    # ID 5: 광안 (Gwangan)
    "광안": 5, "Gwangan": 5,
    # ID 6: 대저 (Daejeo)
    "대저": 6, "Daejeo": 6,
    # ID 7: 경전철 (Light Rail Transit - includes 안평)
    # 안평 (Anpyeong) is often operationally part of or referred to under the "경전철" (Light Rail) system.
    "경전철": 7, "LightRail": 7, 
    "안평": 7  # Explicitly map "안평" to ID 7 if it appears in titles or utterances.
}

# CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES:
# This list provides the canonical (standard or official) names for each cafeteria.
# It is indexed such that the name for Cafeteria ID `n` is found at index `n-1`.
# These names are typically used for constructing filenames (e.g., for diet images)
# or for consistent display of cafeteria names in the user interface or responses.
# Example: For Cafeteria ID 1, the canonical name is "본사".
CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES = [
    "본사",    # Corresponds to Cafeteria ID 1
    "노포",    # Corresponds to Cafeteria ID 2
    "신평",    # Corresponds to Cafeteria ID 3
    "호포",    # Corresponds to Cafeteria ID 4
    "광안",    # Corresponds to Cafeteria ID 5
    "대저",    # Corresponds to Cafeteria ID 6
    "경전철"   # Corresponds to Cafeteria ID 7
]

# The following lists are considered deprecated and are replaced by the more structured
# CAFETERIA_NAME_TO_ID_MAP and CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES.
# They are kept here for historical reference or if any part of the code still uses them,
# but should be phased out.
# cafeteria_full_name_list = ['본사', '노포', '신평', '호포', '광안', '대저', '경전철', '안평']
# cafeteria_semi_name_list = ['ㅂㅅ', 'ㄴㅍ', 'ㅅㅍ', 'ㅎㅍ', 'ㄱㅇ', 'ㄷㅈ', 'ㄱㅈㅊ', 'ㅇㅍ']
