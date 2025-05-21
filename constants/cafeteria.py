# constants/cafeteria.py

# Mapping from various name spellings/aliases found in post titles to a unique Cafeteria ID
CAFETERIA_NAME_TO_ID_MAP = {
    # ID 1: 본사
    "본사": 1, "HumetroHQ": 1,
    # ID 2: 노포
    "노포": 2, "Nopo": 2,
    # ID 3: 신평
    "신평": 3, "Sinpyeong": 3,
    # ID 4: 호포
    "호포": 4, "Hopo": 4,
    # ID 5: 광안
    "광안": 5, "Gwangan": 5,
    # ID 6: 대저
    "대저": 6, "Daejeo": 6,
    # ID 7: 경전철 (안평 is considered part of 경전철 for ID purposes)
    "경전철": 7, "LightRail": 7, 
    "안평": 7  # If "안평" appears in titles, map it to ID 7
}

# List of canonical cafeteria names used for generating filenames or display.
# The index of the list corresponds to (Cafeteria ID - 1).
# For example, CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES[0] is for Cafeteria ID 1.
CANONICAL_CAFETERIA_NAMES_FOR_FILENAMES = [
    "본사",    # ID 1
    "노포",    # ID 2
    "신평",    # ID 3
    "호포",    # ID 4
    "광안",    # ID 5
    "대저",    # ID 6
    "경전철"   # ID 7
]

# The old lists are now deprecated by the map and the canonical name list above.
# cafeteria_full_name_list = ['본사', '노포', '신평', '호포', '광안', '대저', '경전철', '안평']
# cafeteria_semi_name_list = ['ㅂㅅ', 'ㄴㅍ', 'ㅅㅍ', 'ㅎㅍ', 'ㄱㅇ', 'ㄷㅈ', 'ㄱㅈㅊ', 'ㅇㅍ']
