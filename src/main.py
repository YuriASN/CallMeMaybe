#!/usr/bin/env python3

#from .llm_sdk.llm_sdk import Small_LLM_Model
from .argument_parser import parse_files
import sys


def main():
    try:
        files = parse_files(sys.argv)
    except Exception as err:
        print(err)
        exit(42)
if __name__ == "__main__":
    main()
