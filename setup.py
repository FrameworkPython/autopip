from setuptools import setup

setup(
    name="autopip",
    version="0.1.0",
    description="Automatic dependency installer for Python scripts",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="FrameworkPython",
    author_email="amirmahdi21r21@gmail.com",  
    url="https://github.com/FrameworkPython/autopip",  
    py_modules=["autopip", "banner"],
    entry_points={
        "console_scripts": [
            "autopip=autopip:main_cli",
        ],
    },
    python_requires=">=3.7"
    ],
    license="MIT",
)
