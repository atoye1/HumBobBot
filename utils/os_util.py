import os

def check_file_exist(filename: str) -> bool:
    file_path = os.path.join("assets","image", "diet", filename)
    if os.path.exists(file_path):
        return True
    return False
