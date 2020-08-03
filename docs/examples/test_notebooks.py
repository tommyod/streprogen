#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 08:46:26 2019

@author: tommy
"""
import pytest
import subprocess
import os


def _exec_notebook(path):
    script = path.replace(".ipynb", ".py")
    stdout = open(os.devnull, "w")

    subprocess.check_call(["jupyter", "nbconvert", "--to", "python", path], stdout=stdout)

    with open(script, "r") as file:
        lines = "".join(l for l in file if "get_ipython()" not in l)

    with open(script, "w") as file:
        file.write(lines)

    subprocess.check_call(["python", script], stdout=stdout)


# Run examples
here = os.path.abspath(os.path.dirname(__file__))
notebooks = [os.path.join(here, f) for f in os.listdir(here) if f.endswith(".ipynb")]


@pytest.mark.parametrize("notebook", notebooks)
def test_example_notebooks(notebook):
    """Test a notebook by running it. Smoketest."""

    _exec_notebook(notebook)


if __name__ == "__main__":
    pytest.main(args=[".", "--doctest-modules", "-v"])
