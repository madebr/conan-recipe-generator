# Load and save settings from configuration file (or environment)
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

import json
import os
from pathlib import Path
import tempfile
from typing import Dict, Optional


class CrgConfig(object):
    CONFIG_NAME = "config"

    __slots__ = ("home", "_data")

    def __init__(self, home: Optional[Path]=None):
        self.home = home if home is not None else self.default_home()
        self._data = self.read_config_data(self.CONFIG_NAME) or {}

    def get_tempfolder(self) -> Path:
        tmp = os.environ.get("CRG_TEMP") or self._data.get("temporary_folder") or tempfile.gettempdir()
        return Path(tmp)

    def get_work_path(self) -> Path:
        work = os.environ.get("CRG_CACHE") or self._data.get("work_folder")
        if not work:
            work = self.get_tempfolder() / "crg_work"
        return Path(work)

    def get_config_variable(self, name: str, default: Optional[object]) -> object:
        return self._config.get(name, default)

    def read_config_data(self, section: str) -> Optional[Dict]:
        try:
            data = json.load((self.home / section).with_suffix(".json").open())
            if not isinstance(data, dict):
                return None
            return data
        except IOError:
            return None

    def write_config_data(self, section: str, data: object) -> None:
        json.dump(data, (self.home / section).with_suffix(".json"))

    @staticmethod
    def default_home() -> Path:
        crg_home = os.environ.get("CRG_HOME")
        if crg_home is not None:
            return Path(cfg_home)
        return (Path("~") / ".local" / "conan-recipe-generator").expanduser()


GLOBAL_CONFIG = CrgConfig()
