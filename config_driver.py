import json
from path import DOCS_PATH
import os
from utiles import search

CONFIG_FILE = os.path.join(DOCS_PATH, "config.json")

def load_data():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"__error__": str(e)}

def save_data(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

def update_config(parKey, childKey , value):
    data = load_data()
    
    if "__error__" in data:
        print(f"File read error: {data['__error__']}")
        return False

    data[parKey][childKey] = value

    if(save_data(data)):
        print("Config updated sucessfully\n")
        return True
    
    print("Fail to update.\n")
    return False


def Check_Keys(parKey, childKey):
    data = search(parKey)

    if(data[childKey] == ""):
        value = input(f"Please provide the {childKey} value to continue this service: ")

        if(update_config(parKey, childKey, value)):
            return value
        else:
            return ""
    
    return data[childKey]