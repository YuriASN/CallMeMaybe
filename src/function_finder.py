#!/usr/bin/env python3

"""
The Module receives a list of dict or the files to retreive the data.
It has the definition of functions for the LLM to find the best to solve a
prompt received. In case no data or files are passed as parameters, the default
will be used:
    definitions: data/input/functions_definition.json
    prompts: data/input/function_calling_tests.json
    output: data/output/function_calls.json
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
from typing import Dict, List, Tuple
from pathlib import Path
from llm_sdk import Small_LLM_Model  # type: ignore [attr-defined]
from colorama import Fore, Style
import json
import sys
import os


def _get_definition(definitions: List[Dict], funct_name: str) -> Dict:
    """
    Finds the function definition in a list of definitions and returns it.

    Args:
        definitions: List with all function definitions.
        funct_name: The name of the function to be returned.

    Return:
        A dict with the function definition.
        Raise an error if function is not found.
    """
    for funct in definitions:
        if funct["name"] == funct_name:
            return funct

    raise KeyError(f"In _get_definition(): {funct_name} not found.")


def _param_type(definition: Dict, param: str) -> str:
    """
    Finds the funct_name on the definitions list and return the type of
    the param on it.

    Args:
        definition: Dict of function definition.
        param: Parameter name of that function to return it's type.

    Return:
        The type of the given parameter.
        Raise error if parameter not found.
    """
    for key, value in definition["parameters"].items():
        if key == param:
            return value["type"]
    raise KeyError(f"In _param_type() on function {definition['name']}: "
                   f"Parameter: {param} not found.")


def _validate_input_received(definitions: List[Dict],
                             prompts: List[Dict]) -> None:
    function_keys = ["name", "description", "parameters", "returns"]
    for each in definitions:
        # Check if all needed keys are on the definition
        if not all(key in each for key in function_keys):
            raise KeyError(
                "Missing parameters on a function definition.")
        # Checks if there're extra keys on the definition
        if not all(key in function_keys for key in each.keys()):
            raise KeyError(
                "There's a invalid key on a function definition")
        # Checks if all parameters have a 'type' key
        for key, value in each["parameters"].items():
            if "type" not in value.keys():
                raise KeyError(
                    "Missing type of parameter on a function definition.")
            # Checks if only 'type' is a key on a parameter
            if not all(key == "type" for key in value.keys()):
                raise KeyError(
                    "There's invalid key on a function parameter")

    for each in prompts:
        # Check for the prompt key
        if "prompt" not in each.keys():
            raise KeyError(
                "Missing the 'prompt' key in a test")
        # Check if no extra key is given
        for key in each.keys():
            if key != "prompt":
                raise KeyError(
                    f"Key '{key}' is invalid for a prompt.")
        # Check if prompt has " and change for '
        each['prompt'] = each['prompt'].replace('"', "'")


def get_data(input_definitions: List[Dict] | str | None,
             input_prompt: List[Dict] | str | None,
             output_file: str | None) -> Tuple[List[Dict], List[Dict], str]:
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
        if type(input_definitions) is list:
            try:
                # Check if json is valid.
                json.dumps(input_definitions)
                definitions = input_definitions
            except json.JSONDecodeError as err:
                raise Exception(f"Error enconding definitions: {err}")
        else:
            if input_definitions is None:
                definitions = check_input_file(
                    "data/input/functions_definition.json")
            elif type(input_definitions) is str:
                definitions = check_input_file(input_definitions)
            else:
                raise TypeError("Handling definitions, wrong parameter "
                                f"type received: '{type(input_definitions)}'")
        # Checking prompts
        if type(input_prompt) is list:
            try:
                # Check if json is valid.
                json.dumps(input_prompt)
                prompts = input_prompt
            except json.JSONDecodeError as err:
                raise Exception(f"Error enconding prompts: {err}")
        else:
            if input_prompt is None:
                prompts = check_input_file(
                    "data/input/function_calling_tests.json")
            elif type(input_prompt) is str:
                prompts = check_input_file(input_prompt)
            else:
                raise TypeError("Handling prompts, wrong parameter "
                                f"type received: '{type(input_prompt)}'")
        _validate_input_received(definitions, prompts)
    except Exception as err:
        raise err
    # Checking output permissions
    try:
        if not output_file:
            output = "data/output/function_calls.json"
        else:
            output = output_file
        write_permission(output)
    except Exception as err:
        raise Exception(f"Getting data: {err}")

    return definitions, prompts, output


def parse_data_files() -> Tuple[List[Dict], List[Dict], str]:
    """
    Parse the definitions, inputs and output from
    files passed as parameters on sys args.
    Or uses default files if a parameter isn't passed.
    """
    try:
        definitions, prompts, output = parse_files(sys.argv)
        _validate_input_received(definitions, prompts)
    except Exception as err:
        raise Exception(f"Parsing data files: {err}")

    return definitions, prompts, output


def logit_in_str(logit: int, string: str, llm: Small_LLM_Model) -> bool:
    decoded = llm.decode([logit])
    if decoded in string:
        return True
    if decoded == '",':
        return True
    return False


def run_prompts(definitions: List[Dict],
                prompts: List[Dict],
                output: str) -> List[Dict]:
    """
    Call the LLM to solve prompt by prompt from the list.
    Saving everything on the result string.

    Args:
        definitions: The List of Dicts with the functions available for use.
        prompts: The prompts to ask for the LLM.
        output: The str with the path to the file to be outputed on.
    """
    def get_name(definitions: List[Dict], result: str,
                 llm: Small_LLM_Model) -> str:
        """
        Get the name of the function constraining the json format.

        Args:
            definitions: The definitions of the functions to search on.
            result: Current llm prompt as will go to the output.
            llm: The llm being used.
        Return:
            The concactenation of last result and the name of the function
            contrained to a json format.
        """
        name = '"name": "fn'
        def_str = str(definitions)
        tokens = llm.encode(def_str + result + name).tolist()[0]
        while True:
            logits = llm.get_logits_from_input_ids(tokens)
            min_logit = min(logits)
            while True:
                max_index = logits.index(max(logits))
                if all((logit_in_str(max_index, def_str, llm),
                       llm.decode(logits.index(max(logits))) != " ")):
                    break
                logits[max_index] = min_logit
            new_token = llm.decode(logits.index(max(logits)))
            name += new_token
            if name.endswith('",'):
                return name
            tokens = llm.encode(def_str + result + name).tolist()[0]

    def get_parameters(definition: Dict, result: str,
                       llm: Small_LLM_Model) -> str:
        """
        Get the parameters of the function with the value passed on the prompt.

        Args:
            definition: The definition of the function to search parameters on.
            result: Current llm call and responses.
            llm: The llm being used.
        Return:
            The concactenation of last result and the parameters of the
            function constrained to a json format.
        """
        try:
            params = ' "parameters": {"'
            def_str = str(definition)
            tokens = llm.encode(def_str + result + params).tolist()[0]
            while True:
                logits = llm.get_logits_from_input_ids(tokens)
                new_token = llm.decode(logits.index(max(logits)))
                min_logit = min(logits)
                if new_token == " ":
                    logits[logits.index(max(logits))] = min_logit
                if params.endswith('":'):
                    params += ' '
                    last_quote = params.rfind('"')
                    prev_quote = params[:last_quote].rfind('"')
                    last_param = params[prev_quote + 1:last_quote]
                    param_type = _param_type(definition, last_param)
                    if param_type == "str":
                        params += '"'
                    tokens = llm.encode(def_str + result + params).tolist()[0]
                    logits = llm.get_logits_from_input_ids(tokens)
                    while True:
                        max_index = logits.index(max(logits))
                        if param_type in ("int", "float", "number"):
                            if llm.decode(logits.index(max(logits))).isdigit():
                                break
                        elif all(
                            (logit_in_str(max_index, result, llm),
                             llm.decode(logits.index(max(logits))) != " ")):
                            break
                        logits[max_index] = min_logit
                params += llm.decode(logits.index(max(logits)))
                if params.count("{") + 1 == params.count("}"):
                    return params
                if params.count("{") == params.count("}"):
                    return params[:params.rfind("}") + 1]
                tokens = llm.encode(def_str + result + params).tolist()[0]
        except Exception as err:
            raise Exception(f"Getting parameters: {err}\n"
                            f"Current parameter: {params}") from err

    if not definitions:
        raise NotImplementedError(
            "The functions definitions weren't loaded.")
    if not prompts:
        raise NotImplementedError("The prompts weren't loaded.")
    if not output:
        raise NotImplementedError("No file to store the output.")
    try:
        llm = Small_LLM_Model()

        result: List[Dict] = []
        for prompt in prompts:
            if prompt['prompt'] == "":
                continue
            print(f"{Fore.LIGHTBLUE_EX}Running prompt:{Style.RESET_ALL} '"
                  f"{prompt['prompt']}'")
            current_res: str = '{"prompt": "' + prompt['prompt'] + '", '
            current_res += get_name(definitions, current_res, llm)
            name: str = current_res[current_res.rfind('": "') + 4:-2]
            print("function name found...", end="", flush=True)
            current_res += get_parameters(_get_definition(definitions, name),
                                          current_res, llm)
            print(" function parameters found...", end="", flush=True)
            current_dict: Dict = json.loads(current_res)
            result.append(current_dict)
            print(f" {Fore.LIGHTGREEN_EX}valid json.{Style.RESET_ALL}")

    except Exception as err:
        raise Exception(f"Running LLM: {err}\nCurrent result:\n\t"
                        f"{current_res}") from err

    return result


def export_result(result: List[Dict], output: str) -> None:
    """
    Export the result to a json file.
    """
    try:
        if (output == "data/output/function_calls.json"
                and not Path("data/output")):
            os.mkdir("data/output")
        with open(output, "w") as file:
            json.dump(result, file, indent=4)
    except Exception as err:
        raise Exception(f"Writing to output: {err}")
