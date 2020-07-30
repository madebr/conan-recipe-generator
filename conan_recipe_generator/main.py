# conan-recipe-generator main script entry point
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

from argparse import ArgumentParser
from pathlib import Path

from .config import GLOBAL_CONFIG
from .detect_properties import ConanPackageDetector
from .properties import DefaultPackageProperties
from .template.create import ConanRecipeGenerator


def main(args=None):
    parser = ArgumentParser()

    location_parser = parser.add_argument_group("Location of the source archive")
    location_parser.add_argument("--url", "-U", required=True, help="Url of the source archive")
    location_parser.add_argument("--checksum", default=None, help="checksum of the source archive (sha256)")

    ns = parser.parse_args(args)

    generator = ConanRecipeGenerator()

    download_url = ns.url
    download_sha256 = ns.checksum

    workpath = GLOBAL_CONFIG.get_work_path()
    workpath.mkdir(exist_ok=True, parents=True)
    print("work path is {}".format(workpath))

    default_packages = DefaultPackageProperties(
        autoconf="autoconf/2.69",
        automake="automake/1.16.2",
        libtool="libtool/2.4.6",
        winbash="msys2/20190524",
    )

    detector = ConanPackageDetector(workpath=workpath, download_url=download_url, download_sha256=download_sha256)
    detector.detect()
    props = detector.properties(
        url="https://github.com/conan-io/conan-center-index",
        default_packages=default_packages,
    )

    target_path = generator.generate(props)
    print("Generated conan recipe at '{}'".format(target_path))


if __name__ == "__main__":
    main()
