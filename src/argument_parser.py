#!/usr/bin/env python3

from typing import Dict, List
from pathlib import Path
import os
import json


def write_permission(file: str) -> None:
    """
    Checks if file can be created nor written on, raising an error if not.
    If file is default, also checks if the 'output' directory can be created.

    Args:
        file: String with the path for the file.
    """
    pfile = Path(file)
    if (file == "data/output/function_calls.json"):
        if (
            not Path("data").exists()
            or not os.access(Path("data"), os.W_OK)
        ):
            raise PermissionError("'data' directory missing or without "
                                    "writing permission for output"
                                    )
    else:
        if not pfile.parent.exists():
            raise FileNotFoundError(
                f"Directory '{pfile.parent}' "
                "for the pfile file does not exists"
                )
        if not os.access(pfile.parent, os.W_OK):
            raise PermissionError(
                f"No permissions to write on directory'{pfile.parent}'"
                )
        if pfile.exists():
            if not os.access(pfile, os.W_OK):
                raise PermissionError(
                    f"No permission to write on '{file}'"
                    )


def parse_files(argv: List[str]) -> List:
    """
    Receives system args and overwrites defaults if any is passed as parameter.

    Args:
        argv: System parameters

    Return:
        dict[str, str]: Dictionary with 'file type' and 'file path'
    """

    try:
        io_files = {
            "functions_definition": "data/input/functions_definition.json",
            "input": "data/input/function_calling_tests.json",
            "output": "data/output/function_calls.json"
        }
        for i in range(1, len(argv) - 1, 2):
            flag = argv[i][2:]
            value = argv[i + 1]
            if argv[i].startswith("--"):
                if flag not in io_files.keys():
                    raise NameError(f"Flag: '{flag}' is invalid!")
                if not argv[i + 1] or value.startswith("--"):
                    raise ValueError(f"Missing '{flag}' flag's value!")
                io_files[flag] = value
            else:
                raise NameError(F"Invalid parameter: '{flag}'")
        write_permission(io_files["output"])
        definitions: List[Dict]
        tests: List[Dict]
        output = io_files["output"]
        with open(io_files["functions_definition"]) as file:
            definitions = json.load(file)
        with open(io_files["input"]) as file:
            tests = json.load(file)
    except Exception as err:
        raise Exception(f"Parsing files: {err}")

    return [definitions, tests, output]
