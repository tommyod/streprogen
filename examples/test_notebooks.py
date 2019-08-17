#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 17 08:46:26 2019

@author: tommy
"""
import pytest
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


here = os.path.abspath(os.path.dirname(__file__))
notebooks = [os.path.join(here, f) for f in os.listdir(here) if f.endswith(".ipynb")]


@pytest.mark.parametrize("notebook", notebooks)
def test_example_notebooks(notebook):
    """Test a notebook by running it. Smoketest."""

    _exec_notebook(notebook)


if __name__ == "__main__":
    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
