#----------------------------------------------------------------
# Generated CMake target import file.
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ros_gz_sim::gzserver_component" for configuration ""
set_property(TARGET ros_gz_sim::gzserver_component APPEND PROPERTY IMPORTED_CONFIGURATIONS NOCONFIG)
set_target_properties(ros_gz_sim::gzserver_component PROPERTIES
  IMPORTED_LOCATION_NOCONFIG "${_IMPORT_PREFIX}/lib/libgzserver_component.so"
  IMPORTED_SONAME_NOCONFIG "libgzserver_component.so"
  )

list(APPEND _cmake_import_check_targets ros_gz_sim::gzserver_component )
list(APPEND _cmake_import_check_files_for_ros_gz_sim::gzserver_component "${_IMPORT_PREFIX}/lib/libgzserver_component.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
