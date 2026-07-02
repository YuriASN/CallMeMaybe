#!/usr/bin/env python3

from .argument_parser import parse_files
import sys


def main() -> None:
    try:
        definitions, tests, output = parse_files(sys.argv)
    except Exception as err:
        print(err)
        exit(42)
