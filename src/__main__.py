from . import function_finder as find
from colorama import Fore, Style

try:
    data = find.parse_data_files()
    res = find.run_prompts(*data)
    find.export_result(res, data[2])
except Exception as err:
    print(f"{Fore.RED}{err}{Style.RESET_ALL}")
