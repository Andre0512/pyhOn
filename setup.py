#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pyhon",
    version="0.0.1",
    author="Andre Basche",
    description="Control Haier devices with pyhon",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/Andre0512/pyhon",
    license="MIT",
    platforms="any",
    package_dir={"": "pyhon"},
    packages=[""],
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=["aiohttp"]
)
