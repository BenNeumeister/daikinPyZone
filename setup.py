import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="daikinPyZone",
    version="0.6",
    author="Ben Neumeister",
    author_email="benneumeister@gmail.com",
    description="Daikin Skyzone API for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BenNeumeister/daikinPyZone",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ),
)