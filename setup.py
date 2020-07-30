from setuptools import find_packages, setup


with open("README.md", "r") as fh:
    long_description = fh.read()

packages = find_packages(exclude=("tests", "tests.*", "*.tests"))

setup(
    name="conan-recipe-generator",
    version="0.0.1",
    license="AGPLv3",
    packages=packages,
    entry_points={
        "console_scripts": [
            "conan-recipe-generator = conan_recipe_generator.main:main",
        ],
    },
    include_package_data=True,
    install_requires=[
        "conan>=1.28.0",
        "jinja2>=2.9",
    ],
    author="Anonymous Maarten",
    author_email="anonymous.maarten@gmail.com",
    description="Generate conan recipe from a source release",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://github.com/madebr/conan-recipe-generator",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3",
        "Programming Language :: C",
        "Programming Language :: C++",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
