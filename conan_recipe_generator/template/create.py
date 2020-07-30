# Using the Jinja2 template engine, create a recipe
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

import dataclasses
from pathlib import Path
from typing import Optional, Tuple, Union

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .extensions import ConditionalIndentationExtension
from ..properties import ConanRecipeProperties


def global_optlen(d):
    return len(tuple(v for k, v in d.items() if v))


class ConanRecipeGenerator(object):
    TEMPLATE_DIR = Path(__file__).resolve().parent / "files"

    def __init__(self):
        self._loader = FileSystemLoader(searchpath=self.TEMPLATE_DIR)
        self._environment = Environment(
            loader=self._loader,
            undefined=StrictUndefined,
            extensions=(
                ConditionalIndentationExtension,
            ),
        )
        from .filters import filter_classize, filter_libname, filter_makesrcsubdir, filter_strescape, filter_to_string_or_tuple
        self._environment.filters.update({
            "classize": filter_classize,
            "libname": filter_libname,
            "makesrcsubdir": filter_makesrcsubdir,
            "strescape": filter_strescape,
            "to_string_or_tuple": filter_to_string_or_tuple,
        })
        self._environment.globals.update({
            "getattr": getattr,
            "optlen": global_optlen,
        })

    @staticmethod
    def props_to_context(props: ConanRecipeProperties):
        context = dataclasses.asdict(props)
        context.update(dataclasses.asdict(props.build_systems))
        context.update({
            "generators": props.package.extra_generators.union(props.build_systems.generators),
        })
        return context

    def generate(self, props: ConanRecipeProperties, target_path: Optional[Path]=None):
        if target_path is None:
            target_path = Path(props.name)

        if target_path.exists():
            raise FileExistsError("target already exists!")

        files = [
            "config.yml",
            "all/conandata.yml",
            "all/conanfile.py",
            "all/test_package/conanfile.py",
            "all/test_package/CMakeLists.txt",
        ]
        if props.build_systems.cmake:
            files.extend([
                "all/CMakeLists.txt",
            ])
            props.exports_sources.append("CMakeLists.txt")
        if props.package.patches:
            files.extend([
                "all/patches/0001-todo.patch",
            ])
        if props.package.with_cxx:
            files.append("all/test_package/test_package.cpp")
        else:
            files.append("all/test_package/test_package.c")

        target_path.mkdir()
        ctx = self.props_to_context(props)
        for file in files:
            file_path = target_path / file
            file_path.parent.mkdir(parents=True, exist_ok=True)

            template = self._environment.get_template(file)
            template.stream(ctx).dump((target_path / file).open("w"))
        
        return target_path


