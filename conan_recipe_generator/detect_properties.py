# Detect properties of a source tree, that might be needed by the conan recipe
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

import collections
import dataclasses
import itertools
import os
from pathlib import Path
import urllib.parse
import re
import shlex
import shutil
import sys
from typing import Dict, Iterable, List, Optional, Set

import conans

from .properties import AutotoolsReconfType, AutotoolsProperties, BuildSystemsProperties, CMakeProperties, ConanRecipeProperties, DefaultPackageProperties, MesonProperties, MsbuildProperties, PackageProperties



KNOWN_ARCHIVE_EXTS = [
    ".tar",
    ".tar.bz2",
    ".tar.gz",
    ".tar.xz",
    ".tgz",
    ".zip",
]


@dataclasses.dataclass(frozen=True)
class DetectedText(object):
    text: str
    path: Optional[Path]
    origin: object

    @property
    def depth(self) -> int:
        if self.path:
            return len(self.path.parts)
        else:
            return 0


def extract_basename(filename: str) -> Optional[str]:
    for known_ext in KNOWN_ARCHIVE_EXTS:
        if filename[-len(known_ext):] == known_ext:
            return filename[:-len(known_ext)]
    return None


class ConanPackageDetector(object):
    def __init__(self, workpath: Path, download_url: str, download_sha256: Optional[str]):
        self.detected_names: Set[DetectedText] = set()
        self.detected_versions: Set[DetectedText] = set()
        self.detected_homepages: Set[DetectedText] = set()
        self.detected_descriptions: Set[DetectedText] = set()
        self.detected_licenses: List[Path] = list()
        self.detected_cpp = False

        self.detected_autotools: List[AutotoolsProperties] = list()
        self.detected_cmake: List[CMakeProperties] = list()
        self.detected_meson: List[MesonProperties] = list()
        self.detected_msbuild: List[MsbuildProperties] = list()

        self._workpath = workpath
        self._extract_path = workpath / "extract"
        self._download_url = download_url
        self._download_sha256 = download_sha256

        self._extracted_path: Optional[Path] = None

    def detect_name_version(self, path: Path):
        for split in ("-", "_"):
            try:
                name, version = path.name.rsplit(split, 1)
                self.detected_names.add(DetectedText(text=name, path=None, origin=None))
                self.detected_versions.add(DetectedText(text=version, path=None, origin=None))
                break
            except ValueError:
                pass

    def _download_extract(self):
        url_components = urllib.parse.urlparse(self._download_url)
        filename = Path(url_components.path).name

        archive_path = self._workpath / filename

        if self._download_sha256 is None:
            try:
                os.unlink(str(archive_path))
            except FileNotFoundError:
                pass
        if not archive_path.exists() or conans.tools.sha256sum(str(archive_path)) != self._download_sha256:
            conans.tools.download(url=self._download_url, filename=str(archive_path), sha256=self._download_sha256, retry=5, retry_wait=5)

        self._download_sha256 = conans.tools.sha256sum(str(archive_path))
        print("sha256 of '{}' is '{}'".format(self._download_url, self._download_sha256))

        try:
            shutil.rmtree(self._extract_path)
        except FileNotFoundError:
            pass
        self._extract_path.mkdir()
        conans.tools.unzip(filename=str(archive_path), destination=str(self._extract_path))
        print("Extracted archive to '{}'".format(self._extract_path))

    def detect_pre_download(self):
        basename = extract_basename(self._download_url)
        if not basename:
            raise Exception("Unknown archive extension!")
        self.detect_name_version(Path(basename))

    def detect(self):
        self.detect_pre_download()
        self._download_extract()

        extracted_paths = tuple(self._extract_path.iterdir())
        if len(extracted_paths) != 1:
            raise Exception("Don't know how to handle archives (yet) that extract more than one file")
        self._extracted_path = extracted_paths[0]

        self.detect_name_version(self._extracted_path)

        for root, dirs, files in os.walk(str(self._extracted_path)):
            root = Path(root)
            rel_root = self._make_extracted_path(root)
            root_autotools = None
            for file in files:
                if file.lower() == "version":
                    try:
                        version = open(root / file).readline().strip()
                        self.detected_versions.add(DetectedText(text=version, path=rel_root))
                    except IOError:
                        pass
                if file == "CMakeLists.txt":
                    cmake = CMakeProperties(path=rel_root)
                    self._detect_cmake_script(cmake, root / file)
                    self.detected_cmake.append(cmake)
                if file in ("configure", "configure.ac", "configure.in", ):
                    if not root_autotools:
                        # autotools object is added at end of loop of current directory
                        root_autotools = AutotoolsProperties(path=rel_root)
                    self._detect_autoconfigure_script(root_autotools, root / file)
                if "meson.build" in files:
                    meson = MesonProperties(path=rel_root)
                    self._detect_meson_script(meson, root / file)
                    self.detected_meson.add(meson)
                for known_license in self.KNOWN_LICENSES_PREFIX:
                    if file.lower().startswith(known_license):
                        self.detected_licenses.append(rel_root / file)
                        break
                file_suffix = Path(file).suffix
                if file_suffix == ".C" or file_suffix.lower in (".cc", ".cpp", ".cxx", ):
                    self.detected_cpp = True
            if root_autotools:
                self.detected_autotools.append(root_autotools)

    def _make_extracted_path(self, path: Path) -> Path:
        return path.relative_to(self._extracted_path)

    KNOWN_LICENSES_PREFIX = [
        "license",
        "copying",
        "copyright",
    ]

    def _detect_autoconfigure_script(self, autotools: AutotoolsProperties, scriptpath: Path):
        filename = scriptpath.name
        if filename in ("configure", ):
            autotools.script = True
        if filename in ("configure.ac", "configure.in", ):
            content = scriptpath.read_text()

            # Detect autotools type
            if "LT_" in content:
                autotools.autoreconf = AutotoolsReconfType.LIBTOOL
            elif "AM_INIT_AUTOMAKE" in content:
                autotools.autoreconf = AutotoolsReconfType.AUTOMAKE
            else:
                autotools.autoreconf = AutotoolsReconfType.AUTOCONF

            # Extract name, version and url from AC_INIT
            for m in re.finditer(r"AC_INIT[ \t]*\(\[?(?P<name>[a-zA-Z0-9-.]+)\]?[ \t]*,[ \t]?\[?(?P<version>[a-zA-Z0-9.-]+)\]?([ \t]*,[ \t]*\[(?P<bugreport>[a-zA-Z]+)\])?([ \t]*,[ \t]*\[(?P<tarname>[a-zA-Z]+)\])?([ \t]*,[ \t]*\[(?P<homepage>[a-zA-Z]+)\])?", content):
                relpath = self._make_extracted_path(scriptpath.parent)
                self.detected_names.add(DetectedText(text=m.group("name"), path=relpath, origin=autotools.tag))
                self.detected_versions.add(DetectedText(text=m.group("version"), path=relpath, origin=autotools.tag))
                if m.group("homepage"):
                    self.detected_homepages.add(DetectedText(text=m.group("homepage"), path=relpath, origin=autotools.tag))
                break

    def _detect_cmake_script(self, cmake: CMakeProperties, scriptpath: Path):
        content = scriptpath.read_text()
        relpath = self._make_extracted_path(scriptpath.parent)
        for m in re.finditer(r"project[ \t\n]*\(([^)]+)\)", content, flags=re.IGNORECASE):
            try:
                project_args = shlex.split(m.group(1))
            except ValueError:
                continue
            try:
                name = project_args[0]
                self.detected_names.add(DetectedText(name, path=relpath, origin=cmake.tag))
            except IndexError:
                pass
            try:
                version = project_args[project_args.index("VERSION") + 1]
                self.detected_versions.add(DetectedText(version, path=relpath, origin=cmake.tag))
            except (IndexError, ValueError):
                pass
            try:
                description = project_args[project_args.index("DESCRIPTION") + 1]
                self.detected_descriptions.add(DetectedText(description, path=relpath, origin=cmake.tag))
            except (IndexError, ValueError):
                pass
            try:
                homepage = project_args[project_args.index("HOMEPAGE_URL") + 1]
                self.detected_homepages.add(DetectedText(homepage, path=relpath, origin=cmake.tag))
            except (IndexError, ValueError):
                pass

    def lookup_tag(self, tag) -> Optional[object]:
        for taggable in itertools.chain(self.detected_autotools, self.detected_cmake, self.detected_meson, self.detected_msbuild):
            if taggable.tag == tag:
                return taggable
        return None

    def _detect_meson_script(self, meson: MesonProperties, scriptpath: Path):
        # content = scriptpath.read_text()
        # relpath = self._make_extracted_path(scriptpath.parent)
        return

    def properties(self, url: str, default_packages: DefaultPackageProperties) -> ConanRecipeProperties:
        name = self._select_first(self.detected_names) or "UNKNOWN_NAME"
        version = self._select_first(self.detected_versions) or "UNKNOWN_VERSION"
        description = self._select_first(self.detected_descriptions) or "UNKNOWN_DESCRIPTION"
        homepage = self._select_first(self.detected_homepages) or "UNKNOWN_HOMEPAGE"
        licenses = ("UNKNOWN_LICENSES",)


        license_paths = tuple(self.detected_licenses)

        pick_first = lambda x: x[0] if x else None

        autotools = pick_first(self._compress_autotools()) or None
        cmake = pick_first(self._compress_cmake()) or None
        meson = pick_first(self._compress_meson()) or None

        props = ConanRecipeProperties(
            name=name,
            version=version,
            description=description,
            homepage=homepage,
            topics=("conan", name),
            licenses=licenses,
            url=url,
            download_url=self._download_url,
            download_sha256=self._download_sha256,
            default_packages=default_packages,
            build_systems=BuildSystemsProperties(
                autotools=autotools,
                cmake=cmake,
                meson=meson,
            ),
            package=PackageProperties(
                build_context=bool(autotools or meson),
                license_paths=license_paths,
                glob_rename=self._extracted_path.name != "{}-{}".format(name, version),
                with_cxx=self.detected_cpp,
            ),
        )

        return props

    def _select_first(self, set_detected: Set[DetectedText]) -> Optional[str]:
        if not set_detected:
            return None
        prioritized = self._prioritize_detected(set_detected)
        return prioritized[0].text

    def _prioritize_detected(self, set_detected: Set[DetectedText]) -> List[DetectedText]:
        # Group detected texts by detected text
        text_detecteds = collections.defaultdict(list)
        for detected in set_detected:
            text_detecteds[detected.text].append(detected)

        # Order the detected for each text
        def _sort_detected_importance(detecteds: List[DetectedText]):
            # 1st sort on depth
            detecteds.sort(key=lambda d: d.depth)
            # 2nd sort on presence tag
            detecteds.sort(key=lambda d: 1 if d.origin else 0, reverse=True)
        for detecteds in text_detecteds.values():
            _sort_detected_importance(detecteds)

        # For each value, pick the detected text with highest priority
        detecteds = list(d[0] for d in text_detecteds.values())
        _sort_detected_importance(detecteds)
        return detecteds

    def _compress_cmake(self) -> List[CMakeProperties]:
        cmake_included_paths = set()
        for cmake in self.detected_cmake:
            cmake_abs_path = self._extracted_path / cmake.path / "CMakeLists.txt"
            cmake_text = cmake_abs_path.read_text()
            for m in re.finditer(r"add_subdirectory\(([a-z0-9_ ]+)\)", cmake_text, flags=re.IGNORECASE):
                as_args = shlex.split(m.group(1))
                try:
                    subcmake_relpath = Path(as_args[0])
                except IndexError:
                    continue
                subcmake_path = cmake.path / subcmake_relpath
                subcmake_abs_path = cmake_abs_path / subcmake_relpath
                if not subcmake_abs_path.exists():
                    print("cmake script '{}' points to non-existing '{}' cmake script".format(cmake.path, cmake.path / subcmake_path), file=sys.stderr)
                cmake_included_paths.add(subcmake_path)

        cmake_reduced = list(cmake for cmake in self.detected_cmake if cmake.path not in cmake_included_paths)
        cmake_reduced.sort(key=lambda c: len(c.path.parts), reverse=True)
        return cmake_reduced

    def _compress_meson(self) -> List[MesonProperties]:
        meson_included_paths = set()
        for meson in self.detected_meson:
            meson_abs_path = self._extract_path / meson.path / "meson.build"
            meson_text = meson_abs_path.read_text()
            for m in re.finditer(r"subdir[ \t\n]*\([ \t\n]*['\"]([^'\"]+)", meson_text):
                subdir_args = shlex.split(m.group(1))
                try:
                    submeson_relpath = Path(subdir_args[0])
                except IndexError:
                    continue
                submeson_path = meson.path / submeson_relpath
                submeson_abs_path = meson_abs_path / submeson_relpath
                if not submeson_abs_path.exists():
                    print("meson script '{}' points to non-existing '{}' meson script".format(meson.path, meson.path / submeson_path), file=sys.stderr)
                meson_included_paths.add(submeson_path)

        meson_reduced = list(meson for meson in self.detected_meson if meson.path not in meson_included_paths)
        meson_reduced.sort(key=lambda c: len(c.path.parts), reverse=True)
        return meson_reduced

    def _compress_autotools(self) -> List[AutotoolsProperties]:
        autotools = list(self.detected_autotools)
        autotools.sort(key=lambda x: len(x.path.parts))
        return autotools
