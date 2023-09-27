import json
import requests
import os


with open('rules.json', 'r', encoding='utf-8') as f:
    rules = json.load(f)
    for rule in rules:
        print(rule)
        res = requests.get(rule['file_url'])
        file_content = res.content
        file_name = f'{rule["title"]}_{rule["created_at"]}.hwp' 
        file_name = file_name.replace(' ', '_')
        if os.path.exists(file_name):
            print(file_name, 'already processed')
            continue
        else:
            try:
                with open(file_name, 'wb') as hwp_file:
                    hwp_file.write(file_content)
                print(rule['title'], 'saving is done')
                
                command = f"hwp5html {os.path.join(os.getcwd(), file_name)}"
                return_code = os.system(command)

                if return_code == 0:
                    print(f"Conversion Successful {file_name}")
                else:
                    print(f"Command failed with return code {return_code}.")
            except Exception as e:
                print(e)

            