from setuptools import setup, find_packages

setup(
    name="dot2archimate",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.2",
        "uvicorn>=0.27.1",
        "python-multipart>=0.0.9",
        "graphviz>=0.20.1",
        "lxml>=5.1.0",
        "pyyaml>=6.0.1",
        "click>=8.1.7",
        "flask>=2.0.0",
    ],
    entry_points={
        'console_scripts': [
            'dot2archimate=dot2archimate.cli.commands:cli',
        ],
    },
) 