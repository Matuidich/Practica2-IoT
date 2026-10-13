"""Export a separate compilation database for each ESP32 environment."""

import os

Import("env")

env.Replace(
    COMPILATIONDB_PATH=os.path.join("$BUILD_DIR", "compile_commands.json"),
    COMPILATIONDB_INCLUDE_TOOLCHAIN=True,
)
