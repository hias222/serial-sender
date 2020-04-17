ADD_EXECUTABLE( 01-test-data 01-test-data.cpp )

target_link_libraries(01-test-data PUBLIC sender)

target_include_directories(01-test-data PUBLIC
                          "${PROJECT_BINARY_DIR}"
                          "${PROJECT_BINARY_DIR}/sender"
                          )

ADD_TEST( 01-test-data  01-test-data )