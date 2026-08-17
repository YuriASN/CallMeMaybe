from . import function_finder as find

try:
    data = find.parse_data_files()
    res = find.run_prompts(*data)
    find.export_result(res, data[2])
except Exception as err:
    print(err)
