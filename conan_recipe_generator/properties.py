# Dataclasses used for storing the package properties
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
import enum
from pathlib import Path
from typing import Optional, Set, Tuple


@dataclasses.dataclass
class Taggable(object):
    _tag: object = dataclasses.field(default_factory=object)

    @property
    def tag(self):
        return self._tag


@dataclasses.dataclass
class CMakeProperties(Taggable):
    verbose: bool = False
    find_package: bool = False
    find_package_multi: bool = False
    path: Optional[Path] = "."

    @classmethod
    def NAME(cls):
        return "cmake"

    @property
    def generators(self) -> Set[str]:
        res = {"cmake"}
        if self.find_package:
            res.add("cmake_find_package")
        if self.find_package_multi:
            res.add("cmake_find_package_multi")
        return res


@dataclasses.dataclass
class MesonProperties(Taggable):
    verbose: bool = False
    find_package: bool = False
    find_package_multi: bool = False
    path: Optional[Path] = None

    @classmethod
    def NAME(cls):
        return "meson"

    @property
    def generators(self) -> Set[str]:
        return {"pkg_config"}


class AutotoolsReconfType(enum.Enum):
    AUTOCONF = "autoconf"
    AUTOMAKE = "automake"
    LIBTOOL = "libtool"


@dataclasses.dataclass
class AutotoolsProperties(Taggable):
    script: bool = False
    verbose: bool = False
    autoreconf: Optional[AutotoolsReconfType] = None
    path: Optional[Path] = None

    @classmethod
    def NAME(cls):
        return "autotools"

    @property
    def generators(self) -> Set[str]:
        return {"pkg_config"}


@dataclasses.dataclass
class MsbuildProperties(Taggable):
    path: Optional[Path] = None

    @classmethod
    def NAME(cls):
        return "msbuild"

    @property
    def generators(self) -> Set[str]:
        return {"visual_studio"}


@dataclasses.dataclass
class BuildSystemsProperties:
    autotools: Optional[AutotoolsProperties] = None
    cmake: Optional[CMakeProperties] = None
    meson: Optional[MesonProperties] = None
    msbuild: Optional[MsbuildProperties] = None
    path: Optional[Path] = None

    @property
    def generators(self) -> Set[str]:
        res = set()
        if self.autotools:
            res = res.union(self.autotools.generators)
        if self.cmake:
            res = res.union(self.cmake.generators)
        if self.meson:
            res = res.union(self.meson.generators)
        if self.msbuild:
            res = res.union(self.msbuild.generators)
        return res

    def ___contains__(self, key: str) -> bool:
        return getattr(self, key) is not None

    def __len__(self) -> int:
        return len(tuple(filter(lambda x: x, dataclasses.astuple(self))))


@dataclasses.dataclass
class PatchProperties(object):
    filename: str
    base_path: str


@dataclasses.dataclass
class PackageProperties(object):
    glob_rename: bool = False
    with_shared: bool = True
    with_cxx: bool = True
    license_paths: Tuple[Path] = dataclasses.field(default_factory=tuple)
    patches: Tuple[PatchProperties] = dataclasses.field(default_factory=tuple)
    extra_generators: Set[str] = dataclasses.field(default_factory=set)
    build_context: bool = False

    def add_patch(self, filename, base_path) -> None:
        self.patches += (PatchProperties(filename=filename, base_path=base_path), )


@dataclasses.dataclass
class DefaultPackageProperties(object):
    autoconf: str
    automake: str
    libtool: str
    winbash: str


@dataclasses.dataclass
class ConanRecipeProperties(object):
    name: str
    version: str
    description: str
    topics: Tuple[str, ...]
    homepage: str
    url: str
    licenses: Tuple[str]
    download_url: str
    download_sha256: str
    default_packages: DefaultPackageProperties
    build_systems: BuildSystemsProperties = dataclasses.field(default_factory=BuildSystemsProperties)
    exports_sources: Set[str] = dataclasses.field(default_factory=list)
    package: PackageProperties = dataclasses.field(default_factory=PackageProperties)
