#!/usr/bin/env python3

"""
The Module receives a list of dict or the files to retreive the data.
It has the definition of functions for the LLM to find the best to solve a
prompt received. In case no data or files are passed as parameters, the default
will be used:
    definitions: data/input/functions_definition.json
    prompts: data/input/function_calling_tests.json
    output: data/output/function_calling_results.json
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

from .argument_parser import write_permission, check_input_file
from typing import Dict, List, Tuple, Any
from pathlib import Path
from llm_sdk import Small_LLM_Model  # type: ignore [attr-defined]
from colorama import Fore, Style
from .timeit import time_it
import numpy as np
import json
import os

min_float = -np.finfo(np.float64).max


def percentage_bar(success: int, total: int) -> str:
    width = 40
    percentage = success / total
    filled = int(width * percentage)

    bar = "█" * filled + "░" * (width - filled)

    return f"[{bar}] {percentage:6.2%}"


def _get_definition(
        definitions: List[Dict[str, Any]], funct_name: str) -> Dict[str, Any]:
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


def _param_type(definition: Dict[str, Any], param: str) -> str:
    """
    Finds the funct_name on the definitions list and return the type of
    the param on it.

    Args:
        definition: Dict of complete function definition.
        param: Parameter name of that function to return it's type.

    Return:
        The type of the given parameter.
        Raise error if parameter not found.
    """
    for key, value in definition["parameters"].items():
        if key == param:
            return str(value["type"])
    raise KeyError(f"In _param_type() on function {definition['name']}: "
                   f"Parameter: {param} not found.")


def _validate_input_received(definitions: List[Dict[str, Any]],
                             prompts: List[Dict[str, str]]) -> None:
    """
    Validate if the input is valid by searching for the necessary keys.
    If is invalid, raise an error.

    Args:
        definitions: List of dict with the function definitions having "name",
        "description" and "parameters" keys.
        Each dict inside parameters has "type".
        prompts: List of dicts with the "prompt" key.
    """
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
        # Check if prompt has " and change for \""
        each['prompt'] = each['prompt'].replace('"', '\\"')


def get_data(input_definitions: List[Dict[str, Any]] | str | None,
             input_prompt: List[Dict[str, str]] | str | None,
             output_file: str | None) -> Tuple[List[Dict[str, Any]],
                                               List[Dict[str, str]],
                                               str]:
    """
    Get the definition of the functions, prompts for the LLM
    and path to output the result.
    If a argument is None, default files are used.

    Args:
        definitions: List of dict with the definition of functions or
        string with file path.
        input_prompt: List of dict with prompts for the LLM to search for a
        function to be used or string with file path.
        output: String with the path of file to save the result.

    Return:
        Tuple with the list of dict for the definitions, list of dict for
        the prompts, and string with the file for the output.
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
            output = "data/output/function_calling_results.json"
        else:
            output = output_file
        write_permission(output)
    except Exception as err:
        raise Exception(f"Getting data: {err}")

    return definitions, prompts, output


def logit_in_str(logit: int, string: str, llm: Small_LLM_Model) -> bool:
    """
    Checks if the ligit is part of the given string.

    Args:
        logit: The logit to decode and search for.
        string: The string to search the logit on.
        llm: The LLM model being used.

    Return:
        True if the logit is there, False if not.
    """
    decoded = llm.decode([logit])
    if decoded in string:
        return True
    if decoded == '",':
        return True
    return False


def run_prompts(definitions: List[Dict[str, Any]],
                prompts: List[Dict[str, str]],
                output: str,
                model_name: str = "Qwen/Qwen3-0.6B") -> List[Dict[str, Any]]:
    """
    Call the LLM to solve prompt by prompt from the list.
    Saving everything on the result string.

    Args:
        definitions: The List of Dicts with the functions available for use.
        prompts: The prompts to ask for the LLM.
        output: The str with the path to the file to be outputed on.

    Return:
        A list of dicts with the solution for the prompts, having the
        "prompt", "name" and "parameters" keys.
    """
    @time_it
    def get_name(definitions: List[Dict[str, Any]], res: str,
                 llm: Small_LLM_Model) -> str:
        """
        Get the name of the function constraining the json format.

        Args:
            definitions: The definitions of the functions to search on.
            res: Current llm prompt result as will go to the output.
            llm: The llm being used.

        Return:
            The concactenation of last result with the name of the function
            contrained to a json format.
        """
        try:
            # Only name and description to save time and token usage.
            keys = ["name", "description"]
            definitions = [
                {key: each[key] for key in keys}
                for each in definitions
            ]
            names: str = ""
            for each in definitions:
                names = names + "," + each["name"]
            name: str = '"name": "fn'
            def_str = str(definitions)
            prompt = "Find the function to solve the prompt using " \
                     "only one of these functions. If no function can solve " \
                     "the prompt, forget about it and just say 'null'. "
            while True:
                new_token: str = ""
                tokens = llm.encode(prompt + def_str + res + name).tolist()[0]
                logits = llm.get_logits_from_input_ids(tokens)
                while True:
                    max_index = logits.index(max(logits))
                    new_token = llm.decode(logits.index(max(logits)))
                    if all((logit_in_str(max_index, names, llm),
                            new_token != " ")):
                        break
                    if new_token.find("null") != -1:
                        break
                    logits[max_index] = min_float
                name += new_token
                if name.endswith('",'):
                    return name
        except Exception as err:
            raise Exception(f"Getting name: {err}\n"
                            f"Current name: {name}") from err
        except KeyboardInterrupt as interr:
            raise Exception("Interrupted getting name\nCurrent name:\n"
                            f"\t'{name}'") from interr

    @time_it
    def get_parameters(definition: Dict[str, Any], res: str,
                       llm: Small_LLM_Model) -> str:
        """
        Get the parameters of the function with the value passed on the prompt.

        Args:
            definition: The definition of the function to search parameters on.
            res: Current llm call and responses.
            llm: The llm being used.

        Return:
            The concactenation of last result with the parameters of the
            function constrained to a json format.
        """
        try:
            # List with the name of all function parameters
            keys = list(definition["parameters"].keys())
            i = 1
            params: str = ' "parameters": { ' + f'"{keys[0]}":'
            param_type: str = _param_type(definition, keys[0])
            if param_type in ["string", "str"]:
                params += ' "'
            defs = str(definition)
            while True:
                new_token: str = ""
                if params.endswith(','):
                    # Read new parameter from the definitions
                    if i < len(keys):
                        params += f' "{keys[i]}": '
                        param_type = _param_type(
                            definition, keys[i])
                        if param_type in ["string", "str"]:
                            params += '"'
                        i = i + 1
                    else:
                        return params[:params.rfind(",")]
                # LLM call to find next token
                while True:
                    tokens = llm.encode(defs + res + params).tolist()[0]
                    logits = llm.get_logits_from_input_ids(tokens)
                    # Constraining the logits
                    while True:
                        max_index = logits.index(max(logits))
                        new_token = llm.decode(max_index)
                        if param_type in ("int", "float", "number"):
                            if new_token.isdigit():
                                break
                            elif new_token in ["}", ",", " null"]:
                                break
                        elif new_token != " ":
                            break
                        logits[max_index] = min_float
                    params += new_token
                    if params[-1] in ["}", '"', ","]:
                        break
                # If it's the end of the parameters
                if i == len(keys):
                    if params.endswith(','):
                        return params[:params.rfind(",")]
                    return params
        except Exception as err:
            raise Exception(f"Getting parameters: {err}\n"
                            f"Current parameter: {params}") from err
        except KeyboardInterrupt as interr:
            raise Exception("Interrupted getting parameters\nCurrent params:"
                            f"\n\t'{params}'") from interr

    if not definitions:
        raise NotImplementedError(
            "The functions definitions weren't loaded.")
    if not prompts:
        raise NotImplementedError("The prompts weren't loaded.")
    if not output:
        raise NotImplementedError("No file to store the output.")
    fails = 0
    success = 0
    current_res: str = ""
    try:
        llm = Small_LLM_Model(model_name)

        result: List[Dict[str, Any]] = []
        for each in prompts:
            prompt = each["prompt"]
            if prompt == "" or prompt.isspace():
                print(f"{Fore.LIGHTRED_EX}Prompt '{prompt}' is empty."
                      f"{Style.RESET_ALL}")
                continue
            print(f"{Fore.LIGHTBLUE_EX}Running prompt:{Style.RESET_ALL} '"
                  f"{prompt}'")
            current_res = '{"prompt": "' + prompt + '", '
            run_time: float = 0
            res_name, run_time = get_name(definitions, current_res, llm)
            current_res += res_name
            name: str = current_res[current_res.rfind('": "') + 4:-2]
            print(f"function name found in {run_time}s...", end="", flush=True)
            run_time = 0
            res_param, run_time = get_parameters(_get_definition(
                definitions, name),
                current_res, llm)
            current_res += res_param
            print(f" function parameters found in {run_time}s...",
                  end="", flush=True)
            while current_res.count("{") > current_res.count("}"):
                current_res += "}"
            try:
                current_dict: Dict[str, Any] = json.loads(current_res)
            except json.JSONDecodeError as err:
                print(f"\n{Fore.RED}Ivalid json output: {err}"
                      f"Output:\n\t{current_res}{Style.RESET_ALL}")
                fails += 1
            else:
                result.append(current_dict)
                print(f" {Fore.LIGHTGREEN_EX}valid json.{Style.RESET_ALL}")
                success += 1

        print(f"Json constraining: {percentage_bar(success, success + fails)}%"
              f" ({success}/{success + fails})")
        print(f"Prompts solved: {percentage_bar(success, len(prompts))}%"
              f" ({success}/{len(prompts)})")

    except Exception as err:
        raise Exception(f"Running LLM: {err}\nCurrent result:\n\t"
                        f"'{current_res}'") from err
    except KeyboardInterrupt as interr:
        raise Exception(f"Runnning LLM: {interr.args[0]}")

    return result


def export_result(result: List[Dict[str, Any]], output: str) -> None:
    """
    Export the result to a json file.

    Args:
        result: A list of dicts with the result of the LLM calls.
        output: The file to output the result using the json module.
    """
    try:
        if (output == "data/output/function_calling_results.json"
                and not Path("data/output").exists()):
            os.mkdir("data/output")
        with open(output, "w") as file:
            json.dump(result, file, indent=4)
        print(f"{Style.BRIGHT}{Fore.GREEN}Json file saved!{Style.RESET_ALL}")
    except Exception as err:
        raise Exception(f"Writing to output: {err}")
