#!/usr/bin/env python3

from typing import Dict, List
from pathlib import Path
import os
import json


def file_permission(io_files: Dict[str, str]) -> None:
    """
    Checks for files permission to read and write depending on the file.
    If doesn't exist, checks for directory permission.

    Args:
        io_files: Dictionary with definition, input and output files
    """
    func_def = Path(io_files["functions_definition"])
    input = Path(io_files["input"])
    output = Path(io_files["output"])
    # Checking Function definition file
    if not func_def.exists():
        raise FileNotFoundError(
            f"File '{io_files['functions_definition']}' not found"
            )
    if not os.access(func_def, os.R_OK):
        raise PermissionError(
            f"No permission to access '{io_files['functions_definition']}'"
            )
    # Checking input file
    if not input.exists():
        raise FileNotFoundError(
            f"File '{io_files['input']}' not found"
            )
    if not os.access(input, os.R_OK):
        raise PermissionError(
            f"No permission to access '{io_files['input']}'"
            )
    # Checking output directory and file
    if (io_files["output"] == "data/output/function_calls.json"):
        if (
            not Path("data").exists()
            or not os.access(Path("data"), os.W_OK)
        ):
            raise PermissionError("'data' directory missing or without "
                                    "writing permission for output"
                                    )
    else:
        if not output.parent.exists():
            raise FileNotFoundError(
                f"Directory '{output.parent}' "
                "for the output file does not exists"
                )
        if not os.access(output.parent, os.W_OK):
            raise PermissionError(
                f"No permissions to write on directory'{output.parent}'"
                )
        if output.exists():
            if not os.access(output, os.W_OK):
                raise PermissionError(
                    f"No permission to write on '{io_files['output']}'"
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
        file_permission(io_files)
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
