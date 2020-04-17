if (WIN32)
    set (OTHER_SRC sendwin.cpp )
else ()
    set (OTHER_SRC send.cpp)
endif (WIN32)

add_library(sender
                ${OTHER_SRC}
            )

target_include_directories(sender PUBLIC
      "${PROJECT_BINARY_DIR}"
      "${PROJECT_SOURCE_DIR}/sender"
      )