import importlib

from . import *
from .utils import *
from typing import List

def start(args: List[str]):
    if not args:
        print_usage()
    else:
        language = language_resolver(args.pop(0))
        if language not in ("java", "all"):
            raise Exception("'{}' is not a supported language.".format(language))
        
        # Import the relevant modules based on the chosen language
        mod_path = "gt.languages.{}".format(language)
        mod      = importlib.import_module(mod_path)
        
        if not args:
            if language == "all":
                print("Commands applicable to all languages:")
            else:
                print(f"Commands applicable to {language}:")
            for cmd in mod.COMMANDS:
                print(f"• {cmd}")
            raise Exception("")
        
        command  = args.pop(0)
        
        # Each language module exposes a COMMAND mapping
        # The COMMAND mapping maps a string to a function
        try:
            mod.COMMANDS[command](args)
        except KeyError:
            print(f"Invalid command: '{command}'")
            print(f"To get a list of all available commands, run gt <languge> without providing any arguments.")

def print_usage() -> None:
    help_file = os.path.join(APP_HOME, "src/resources/usage.txt")
    with open(help_file, "r") as file:
        print(file.read())

