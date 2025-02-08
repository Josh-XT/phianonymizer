from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="phianonymizer",
    version="0.0.1",
    description="A tool to anonymize data before sending to LLM providers, then re-identify the data after receiving the response.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Josh XT",
    author_email="josh@devxt.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "cryptography",
        "llama-cpp-python",
        "huggingface-hub",
    ],
)
