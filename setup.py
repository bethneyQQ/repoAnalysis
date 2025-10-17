from setuptools import setup, find_packages

setup(
    name="repo-analysis",
    version="1.0.0",
    description="Pluggable repository analysis framework",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0.0",
        "requests>=2.28.0",
        "gitpython>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "repo-analysis=cli:cli",
        ],
    },
)
