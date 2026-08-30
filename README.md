*This project has been created as part of the 42 curriculum by ysantos-*

## Description

This project develops a function calling system, using the functions provided to solve a prompt. It helps choosing the best function to solve the prompt using a Large Language Model *(LLM)* that was constrained to give the result in a valid json file.  
Small models like the default of this project [Qwen/Qwen3-0.6B](https://cdn.intra.42.fr/document/document/54153/llm_sdk.zip) provided by 42 are good to generate a output in human language but bad at producing structured or machine executable outputs. LLM constraining is a method that guides the LLM response, helping to keep the json structure.  

## Instructions

For this project we have a makefile that already handles all the dependencies and run the program, clean the cache and do the checks (flake8 and mypy).  
```bash
make install
# Creates a virtual environment installing all the dependencies there using 'uv'.
```

```bash
make run
# Runs the the main on the virtual environment using 'uv'.
```

```bash
make clean
# Recursively removes the cache from mypy and python, printing what was removed.
```

```bash
make lint
# Runs flake8 and  mypy on the files, except for the venv and llm directories.
```

```bash
make lint-strict
# Same as above but with the strict flag.
```

## Resources

Ironically, AI was used as my resource to explain how a LLM works.  
Asked for a extensive explanation behind the LLM calls and what the tokens can really be regardless of the model being used.

## Algorithm explanation

Working prompt by prompt, the program writes the beginning of the dict with the *prompt* key already filled and the *name* key to be filled but already having the `"fn` to reduce tokens for the function name. Before that a small prompt followed by the functions definitions are provided so it knows where to look for.  
Once a `",` is found, the program stops the LLM calls and add the *parameters* key leaving a `{"` in the end to force the LLM to create a dicts of each parameter. This time instead of passing all function definitions, only the function of the name provided before is passed. Then once it has the closing brackets marking the end of the parameters, it stops the LLM calls and add a `}` if needed.  
After each prompt is solved, the string is converted to a dict and added to the list.

## Design decisions

Although LLMs works with strings, I decide to use the list of dicts through most of the program. That way I could access and convert only a single function definition when getting the parameters, and with that reduce the amount of tokens used on the LLM.  
The conversion of the string to dict done for each prompt -instead of creating a list as a string- was done so that we can find if that prompt is a valid json and if not just ignore it.  

An extra step was done where the module can also take function definitions and prompts directly or passing the file name. On a hierarchy it goes from a parameter passed to the module, to the system args and by last the default files. This was done so that the module can be used by other programs that might have the data instead of always using files.  

## Performance analysis

The way the constraining was done it makes the json structure and content 100% reliable, although if a prompt asks for something that doesn't have a function for it, it'll give a random answer for it.  
By leaving the `fn` to find a function and passing only 1 function for the parameters, we use less tokens and therefore process everything faster.  

## Challenges faced:

- **source_string**: The string was being changed by the LLM when it was passed as an parameter of a function. To solve the problem a prompt was added before everything so that the LLM would keep the source string unchanged when passed as a parameter.  
- **numeric values**: Numeric values were being added as a string. Used constrained code where it sees if the parameter type is a numeric value (int, foat, etc) and leave the higher logits of only digits.  

## Testing Strategy

To validate the output, the *json* module is used to convert the LLM output to a dict. If a error is encountered, the program print the error, but keep running the next prompts. I used a wrapper to keep track of how long it took for the LLM to find something and with that figured out what's the best solution for all the prompts.  

## Example usage:

