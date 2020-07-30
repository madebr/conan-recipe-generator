{#
 Template for the main conanfile.py
 Copyright (C) 2020 Anonymous Maarten

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
#}from conans import {% if autotools %}AutoToolsBuildEnvironment, {%endif%}{% if cmake %}CMake, {% endif %}ConanFile, {% if meson %}MesonBuild, {% endif %}tools{% if package.build_context %}
from contextlib import contextmanager{% endif %}{% if package.glob_rename %}
import glob{% endif %}
import os


class {{ name | classize }}Conan(ConanFile):
    name = "{{ name }}"
    description = "{{ description | strescape }}"
    topics = {{ topics | to_string_or_tuple }}
    license = {{ licenses | to_string_or_tuple }}
    homepage = "{{homepage}}"
    url = "{{url}}"
    settings = "os", "arch", "compiler", "build_type"{% if exports_sources %}
    exports_sources = {{ exports_sources }}{% endif %}{% if package.with_shared %}
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }{% endif %}{% if generators %}
    generators = {{ generators | to_string_or_tuple(False) }}{% endif %}{% if autotools or cmake or meson %}
{% if autotools %}
    _autotools = None{% endif %}{% if cmake %}
    _cmake = None{% endif %}{% if meson %}
    _meson = None{% endif %}{% endif %}

    @property
    def _source_subfolder(self):
        return "source_subfolder"{% if meson %}

    @property
    def _build_subfolder(self):
        return "build_subfolder"{% endif %}{% if package.with_shared %}

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC{% endif %}

    def configure(self):{% if package.with_shared %}
        if self.options.shared:
            del self.options.fPIC{% endif %}{% if not package.with_cxx %}
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd{% endif %}

    # def requirements(self):
    #     pass{% if autotools %}

    def build_requirements(self):
        if tools.os_info.is_windows and not tools.get_env("CONAN_BASH_PATH") and \
                tools.os_info.detect_windows_subsystem() != "msys2":
            self.build_requires("{{ default_packages.winbash }}"){% if autotools.autoreconf %}
        self.build_requires("{{ default_packages[autotools.autoreconf.value] }}"){% endif %}{% endif %}

    def source(self):
        tools.get(**self.conan_data["sources"][self.version]){% if package.glob_rename %}
        os.rename(glob.glob("{{ name }}-*")[0], self._source_subfolder){% else %}
        os.rename("{}-{}".format(self.name, self.version), self._source_subfolder){% endif %}{% if package.build_context %}

    @contextmanager
    def _build_context(self):
        env = {}
        if self.settings.compiler == "Visual Studio":
            with tools.vcvars(self.settings):
                env.update({
                    "AR": "{} lib".format(tools.unix_path(self.deps_user_info["automake"].ar_lib)),
                    "CC": "{} cl -nologo".format(tools.unix_path(self.deps_user_info["automake"].compile)),
                    "CXX": "{} cl -nologo".format(tools.unix_path(self.deps_user_info["automake"].compile)),
                    "NM": "dumpbin -symbols",
                    "OBJDUMP": ":",
                    "RANLIB": ":",
                    "STRIP": ":",
                })
                with tools.environment_append(env):
                    yield
        else:
            with tools.environment_append(env):
                yield{% endif %}{% if autotools %}

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        conf_args = [
        ]
        if self.options.shared:
            conf_args.extend(["--enable-shared", "--disable-static"])
        else:
            conf_args.extend(["--disable-shared", "--enable-static"])
        self._autotools.configure(args=conf_args, configure_dir=self._source_subfolder)
        return self._autotools{% elif cmake %}

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self){% if cmake.verbose %}
        self._cmake.verbose = True{% endif %}
        self._cmake.configure()
        return self._cmake{% endif %}{% if meson %}

    def _configure_meson(self):
        if self._meson:
            return self._meson
        self._meson = MesonBuild(self)
        self._meson.configure(source_folder=self._source_subfolder, build_folder=self._build_subfolder)
        return self._meson{% endif %}{% if package.patches %}

    def _patch_sources(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch){% endif %}

    def build(self):{% if package.patches %}
        self._patch_sources(){% endif %}{% if optlen(build_systems) > 1 %}
        from conans.errors import ConanException
        raise ConanException("Multiple build systems detected"){% endif %}{% if cmake %}
        cmake = self._configure_cmake()
        cmake.build(){% endif %}{% if autotools %}{% if not autotools.script and autotools.autoreconf %}
        with tools.chdir(self._source_subfolder):
            self.run("autoreconf -fiv", run_environment=True, win_bash=tools.os_info.is_windows){% endif %}{% cond_indent package.build_context "with self._build_context():" %}
        autotools = self._configure_autotools()
        autotools.make({% if autotools.verbose %}args=["V=1"]{% endif %}){% end_cond_indent %}{% endif %}{% if meson %}{% cond_indent package.build_context "with self._build_context():" %}
        meson = self._configure_meson()
        meson.build({% if meson.verbose %}args=["-v"]{% endif %}){% end_cond_indent %}{% endif %}{% if optlen(build_systems) == 0 %}
        from conans.errors import ConanException
        raise ConanException("implement build here"){% endif %}

    def package(self):{% if optlen(build_systems) > 1 %}
        from conans.errors import ConanException
        raise ConanException("Multiple build systems detected"){% endif %}{% for license in package.license_paths %}
        self.copy("{{ license.name }}", src={{ license.parent | makesrcsubdir() }}, dst="licenses"){% endfor %}{% if cmake %}
        cmake = self._configure_cmake()
        cmake.install()

        # tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        # tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        # tools.rmdir(os.path.join(self.package_folder, "share")){% endif %}{% if autotools %}{% cond_indent package.build_context "with self._build_context():" %}
        autotools = self._configure_autotools()
        autotools.install(){% end_cond_indent %}

        # os.unlink(os.path.join(os.path.join(self.package_folder, "lib", "lib{{ name | libname }}.la")))
        # tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        # tools.rmdir(os.path.join(self.package_folder, "share")){% endif %}{% if meson %}{% cond_indent package.build_context "with self._build_context():" %}
        meson = self._configure_meson()
        meson.install(){% end_cond_indent %}

        # tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        # tools.rmdir(os.path.join(self.package_folder, "share")){% endif %}{% if optlen(build_systems) == 0 %}
        from conans.errors import ConanException
        raise ConanException("implement package here"){% endif %}

    def package_info(self):
        self.cpp_info.libs = ["{{ name | libname }}"]

