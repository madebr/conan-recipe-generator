# Custom filters used byb Jinja2 templates.Using the Jinja2 template engine, create a recipe
# Copyright (C) 2020 Anonymous Maarten
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pathlib import Path
import re
import string
from typing import Tuple, Union


def filter_classize(x: str):
    name = x
    if x.startswith("lib"):
        name = x[3:]
    new_name = "".join(p.capitalize() for p in re.split("[ _-]", name))
    if x.startswith("lib"):
        new_name = "Lib" + new_name
    if x and x[0] in string.digits:
        new_name = "Recipe" + new_name
    return new_name


def filter_strescape(x: str) -> str:
    return x.replace("\"", "\\\"")


def filter_to_string_or_tuple(x: Union[str, Tuple[str, ...]], parentheses=True):
    lparen, rparen = ("(", ")") if parentheses else ("", "")
    if isinstance(x, str):
        return "\"{}\"".format(x)
    else:
        if len(x) == 1:
            return "\"{}\"".format(list(x)[0])
        return lparen + "{}".format(", ".join("\"{}\"".format(l) for l in x)) + rparen


def filter_makesrcsubdir(x: Path):
    if x.parts:
        return "os.path.join(self._source_subfolder, {})".format(", ".join("\"{}\"".format(s) for s in x.parts))
    else:
        return "self._source_subfolder"


def filter_libname(x: str):
    if x.startswith("lib"):
        return x[3:]
    return x
