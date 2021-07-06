# -*- coding: utf-8 -*-
# python-todo-to-issue/main.py

# Copyright (c) 2021, Kevin Sawade (kevin.sawade@uni-konstanz.de)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1
# of the License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# Find the GNU Lesser General Public License under <http://www.gnu.org/licenses/>.
"""Convert python Todos to github issues.

"""
################################################################################
# Globals
################################################################################


__all__ = ['main', 'GithubClient']

################################################################################
# Imports
################################################################################


import ast
from sphinxcontrib.napoleon import GoogleDocstring

################################################################################
# Classes
################################################################################


class GitHubClient():
    def __init__(self, repo_url, secret):
        print(secret)

################################################################################
# Main
################################################################################

def main(testing):
    if testing:
        print("Running in Test Mode")
    print("Running Main")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Python code Todos to github issues.")
    parser.add_argument('--testing', dest='testing', action='store_true', help="Whether a testing run is executed and tests will be conducted.")
    parser.set_defaults(testing=False)
    args = parser.parse_args()
    main(testing=args.testing)
