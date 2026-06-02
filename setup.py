from setuptools import setup, find_packages

setup(
    name="monkeyui",
    version="0.1.0",
    author="MonkeyUI Team",
    description="An enterprise-grade PySide6 UI component library inspired by Element Plus.",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md", encoding="utf-8") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["gallery", "scripts", "examples"]),
    install_requires=[
        "PySide6>=6.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
