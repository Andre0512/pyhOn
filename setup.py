#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="pyhon",
    version="0.0.5",
    author="Andre Basche",
    description="Control hOn devices with python",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/Andre0512/pyhon",
    license="MIT",
    platforms="any",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=["aiohttp"]
)
