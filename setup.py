from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='code-rag',
    version='0.1.0',
    description='A simple RAG application to chat wth your code',
    author='Aasheesh Singh',
    author_email='your.email@example.com',
    install_requires=required,
    python_requires='>=3.10',
)