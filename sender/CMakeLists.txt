if (WIN32)
    set (OTHER_SRC sendwin.cpp )
else (WIN32)
    if (RASPBERRYPI)
        message(STATUS "serial-sender RASPBERRY")
    else(RASPBERRYPI)
        message(STATUS "serial-sender no RASPBERRY")
        set (OTHER_SRC send.cpp)
    endif(RASPBERRYPI)
endif (WIN32)

if (ISFTDI)
    message(STATUS "only FTDI")
    set (OTHER_SRC send.cpp)
else (ISFTDI)
    if(RASPBERRYPI)
        message(STATUS "serial-sender add gpio libs")
        # Find the path to the pigpio includes.
        find_path(pigpio_INCLUDE_DIR 
            NAMES pigpio.h pigpiod_if.h pigpiod_if2.h
            HINTS /usr/local/include)
            
        # Find the pigpio libraries.
        find_library(pigpio_LIBRARY 
            NAMES libpigpio.so
            HINTS /usr/local/lib)
        find_library(pigpiod_if_LIBRARY 
            NAMES libpigpiod_if.so
            HINTS /usr/local/lib)
        find_library(pigpiod_if2_LIBRARY 
            NAMES libpigpiod_if2.so
            HINTS /usr/local/lib)
            
        # Set the pigpio variables to plural form to make them accessible for 
        # the paramount cmake modules.
        set(pigpio_INCLUDE_DIRS ${pigpio_INCLUDE_DIR})
        set(pigpio_INCLUDES     ${pigpio_INCLUDE_DIR})

        # Handle REQUIRED, QUIET, and version arguments 
        # and set the <packagename>_FOUND variable.
        include(FindPackageHandleStandardArgs)

        find_package_handle_standard_args(pigpio 
            DEFAULT_MSG 
            pigpio_INCLUDE_DIR pigpio_LIBRARY pigpiod_if_LIBRARY pigpiod_if2_LIBRARY)

        set (OTHER_SRC sendGPIO.cpp)

    endif(RASPBERRYPI)
endif (ISFTDI)

add_library(sender
        ${OTHER_SRC}
    )


if (ISFTDI)
    message(STATUS "ISFTDI")
else (ISFTDI)
    if(RASPBERRYPI)
        message(STATUS "serial-sender link pigpio")
        target_link_libraries(sender pigpio)
    endif(RASPBERRYPI)
endif (ISFTDI)

target_include_directories(sender PUBLIC
    "${PROJECT_BINARY_DIR}"
    "${PROJECT_SOURCE_DIR}/sender"
    )