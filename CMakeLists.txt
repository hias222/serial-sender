cmake_minimum_required(VERSION 3.0.0)
project(serial VERSION 0.1.0)

if (NOT WIN32)
    EXECUTE_PROCESS(COMMAND bash ${CMAKE_HOME_DIRECTORY}/checkapi RESULT_VARIABLE RASPBERRYPI)
    EXECUTE_PROCESS(COMMAND bash ${CMAKE_HOME_DIRECTORY}/checkftdi RESULT_VARIABLE ISFTDI)
endif()

if (ISFTDI)
    message(STATUS "ISFTDI")
endif (ISFTDI)

if(APPLE)
    set(ENV{OPENSSL_ROOT_DIR} "/usr/local/opt/openssl@1.1")
    set(ENV{OPENSSL_LIBRARIES} "/usr/local/opt/openssl@1.1/lib")
endif()

if(WIN32)
    message(STATUS "FOUND Windows no RPI")
    set(ENV{OPENSSL_ROOT_DIR} "C:/Users/User/git/vcpkg/installed/x86-windows")
    set(RASPBERRYPI "0")
endif()

include(CTest)
enable_testing()

add_subdirectory(sender)

if(BUILD_TESTING)
    add_subdirectory(tests)
endif()

add_executable(serial-sender main.cpp)

target_link_libraries(serial-sender PUBLIC sender)

target_include_directories(serial-sender PUBLIC
                          "${PROJECT_BINARY_DIR}"
                          "${PROJECT_SOURCE_DIR}/receiver"
                          )


set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)
