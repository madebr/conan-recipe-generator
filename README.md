# conan-recipe-generator

Conan-recipe-generator creates recipes for c/c++ source releases.

## How to use

```python
$ conan-recipe-generator --url "$PATH_TO_RELEASE" 
```

The script will (try to) detect the name and version of the package and create a folder named after the deteced name in the current working directory.
This folder will contain the recipe.

This script will not generate a working recipe if it detects multiple build systems.
Code to build with all build systems will be generated, but you will have to modify the script manually.
The heuristics might always fail.

## How to contribute

There are multiple issues open with ideas to improve this project.
Bugs, ideas, or improvements can be sent to the [issue tracker at github](https://github.com/madebr/conan-recipe-generator).

## Requirements

- [conan](https://pypi.org/project/conan/)
- [jinja2](https://pypi.org/project/Jinja2/)

## License

This project is licensed under the [GNU Affero GPLv3](https://www.gnu.org/licenses/agpl-3.0.html) (or later).
The generated conan recipes are licensed using the [WTFPL](https://spdx.org/licenses/WTFPL.html).
