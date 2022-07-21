import setuptools
import configparser

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("./src/pyecotrend_ista/const.py") as f:
    config_string = "[dummy_section]\n" + f.read()
    config = configparser.ConfigParser(allow_no_value=True)
    config.read_string(config_string)
    version = config["dummy_section"]["VERSION"].strip('"')

setuptools.setup(
    name="pyecotrend-ista",
    version=version,
    author="Ludy87",
    author_email="android@astra-g.org",
    description="Python ecotrend-ista Api",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ludy87/pyecotrend-ista",
    project_urls={
        "Bug Tracker": "https://github.com/Ludy87/pyecotrend-ista/issues",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="python api ecotrend ista",
    install_requires=["aiohttp==3.8.1"],
    python_requires=">=3.6",
)
