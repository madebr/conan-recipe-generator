{#
 Template for the test_package CMakeLists.txt
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
#}cmake_minimum_required(VERSION 2.8.11)
project(test_package C{% if package.with_cxx %} CXX{% endif %})

include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
conan_basic_setup()

add_executable(${PROJECT_NAME} {% if package.with_cxx %}test_package.cpp{% else %}test_package.c{% endif %})
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})

