#!/usr/bin/env python3

"""
The Module receives a list of dict with the definition of functions for
the LLM to find the best to solve a prompt received.
Returns a List of dict with the prompt received, name of the function found
and parameters of the prompt filling the ones on the function.

The definition has to be as following:
[
    {
        "name": String with function name,
        "description": String with description of the function,
        "parameters": {
            "a": {
                "type": String with parameter type
            },
            "b": {
                "type": String with parameter type
            }
    }
]

The prompts are as it follows:
[
    {
        "prompt": Prompt for the LLM
    }
]

The Results given will be:
[
    {
        "prompt": "What is the sum of 2 and 3?",
        "name": "fn_add_numbers",
        "parameters": {"a": 2.0, "b": 3.0}
    }
]
"""

from .argument_parser import parse_files, write_permission, check_input_file
from typing import Dict, List
from pydantic import BaseModel, model_validator, ValidationError
from pathlib import Path
import json
import sys
import os


class FuncFinder(BaseModel):
    definitions: List[Dict]
    prompts: List[Dict]
    output: str
    result: str

    @model_validator(mode="after")
    def validate_input_received(self) -> "FuncFinder":
        function_keys = ["name", "description", "parameters", "returns"]
        for each in self.definitions:
            # Check if all needed keys are on the definition
            if not all(key in each for key in function_keys):
                raise ValidationError(
                    "Missing parameters on a function definition.")
            # Checks if there're extra keys on the definition
            if not all(key in function_keys for key in each.keys()):
                raise KeyError(
                    "There's a invalid key on a function definition")
            # Checks if all parameters have a 'type' key
            for param in each["parameters"]:
                if "type" not in param.keys():
                    raise ValidationError(
                        "Missing type of parameter on a function definition")
                # Checks if only 'type' is a key on a parameter
                if not all(key == "type" for key in param.keys()):
                    raise KeyError(
                        "There's invalid key on a function parameter")

        for each in self.prompts:
            # Check for the prompt key
            if "prompt" not in each.keys():
                raise ValidationError(
                    "Missing the 'prompt' key in a test")
            # Check if no extra key is given
            for key in each.keys():
                if key == "prompt":
                    raise KeyError(
                        f"Key '{key}' is invalid for a prompt.")

        return self

    def get_data(self, definitions: List[Dict] | str | None,
                 prompts: List[Dict] | str | None,
                 output: str | None) -> None:
        """
        Get the definition of the functions, prompts for the LLM
        and path to output the result.
        If a argument is None, default files are used.

        Args:
            definitions: List of dict with the definition of functions or
            string with file path.
            prompts: List of dict with prompts for the LLM to search for a
            function to be used or string with file path.
            output: String with the path of file to save the result.
        """
        try:
            # Checking definitions
            if type(definitions) is List:
                try:
                    # Check if json is valid.
                    json.dumps(definitions)
                    self.definitions = definitions
                except json.JSONDecodeError as err:
                    raise Exception(f"Error enconding definitions: {err}")
            else:
                if not definitions:
                    self.definitions = check_input_file(
                        "data/input/functions_definition.json")
                elif type(definitions) is str:
                    self.definitions = check_input_file(definitions)
                else:
                    raise TypeError("Handling definitions, wrong parameter "
                                    f"type received: '{type(definitions)}'")
            # Checking prompts
            if type(prompts) is List:
                try:
                    # Check if json is valid.
                    json.dumps(prompts)
                    self.prompts = prompts
                except json.JSONDecodeError as err:
                    raise Exception(f"Error enconding prompts: {err}")
            else:
                if not prompts:
                    self.prompts = check_input_file(
                        "data/input/function_calling_tests.json")
                elif type(prompts) is str:
                    self.prompts = check_input_file(prompts)
                else:
                    raise TypeError("Handling definitions, wrong parameter "
                                    f"type received: '{type(definitions)}'")
        except Exception as err:
            raise err
        # Checking output permissions
        try:
            if not output:
                write_permission("data/output/function_calls.json")
            else:
                write_permission(output)
        except Exception as err:
            raise err

    def parse_data_files(self) -> None:
        """
        Parse the definitions, inputs and output from
        files passed as parameters on sys args.
        Or uses default files if a parameter isn't passed.
        """
        self.definitions, self.prompts, self.output = parse_files(sys.argv)

    def export_result(self) -> None:
        """
        Export the result to a json file.
        """
        try:
            if (self.output == "data/output/function_calls.json"
                    and not Path("data/output")):
                os.mkdir("data/output")
            with open(self.output, "w") as file:
                json.dump(self.result, file)
        except Exception as err:
            raise Exception(f"Writing to output: {err}")
