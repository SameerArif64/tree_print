from setuptools import setup, find_packages

setup(
    name="tree_print",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "colorama",
        "pyperclip"
    ],
    entry_points={
        "console_scripts": [
            "tree_print=tree_print.cli:main",
        ],
    },
    python_requires=">=3.8",
)
