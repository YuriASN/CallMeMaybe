#!/usr/bin/env python3
from src import function_finder as find
from colorama import Fore, Style


if __name__ == "__main__":
    try:
        data = find.get_data(None, None, None)
        res = find.run_prompts(*data)
        find.export_result(res, data[2])
    except Exception as err:
        print(f"{Fore.RED}{err}{Style.RESET_ALL}")
