
from setuptools import setup, find_packages

setup(
    name="bras-autotune",
    version="1.0.0",
    description="BRAS/PPPoE autotuning generator with P/E core detection and NIC queue sync",
    author="Maxx",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "bras-autotune=bras_autotune.cli:main",
        ],
    },
)
