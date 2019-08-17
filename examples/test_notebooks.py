#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 08:46:26 2019

@author: tommy
"""

import subprocess
import tempfile
import os


def _exec_notebook(path):
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
        args = [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=1000",
            "--output",
            fout.name,
            path,
        ]
        subprocess.check_call(args)


def test_example_notebooks():
    here = os.path.abspath(os.path.dirname(__file__))

    # Loop over every notebook
    for file in os.listdir(here):

        if not file.endswith(".ipynb"):
            continue

        _exec_notebook(os.path.join(here, file))


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
