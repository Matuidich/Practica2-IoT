"""Compila pruebas nativas y contrasta el parser C++ con el contrato JSON."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="g++")
    args = parser.parse_args()
    compiler = shutil.which(args.compiler)
    if not compiler:
        parser.exit(1, "Se necesita g++ (MSYS2 en Windows) para las pruebas nativas.\n")
    root = Path(__file__).resolve().parents[1]
    build = root / ".tools/native-tests"
    build.mkdir(parents=True, exist_ok=True)
    executable = build / ("contract_probe.exe" if os.name == "nt" else "contract_probe")
    native = root / "firmware/tests_native"
    libraries = root / "firmware/lib"
    includes = [native, libraries / "Communication/src", libraries / "LedController/src", libraries / "UltrasonicSensor/src"]
    sources = [native / "contract_probe.cpp", libraries / "Communication/src/ProtocolCodec.cpp",
               libraries / "LedController/src/LedController.cpp", libraries / "UltrasonicSensor/src/UltrasonicSensor.cpp"]
    compile_options = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", *(f"-I{path}" for path in includes)]
    command = [*compile_options, *(str(path) for path in sources), "-o", str(executable)]
    subprocess.run(command, check=True, cwd=root)
    compilation_database = [
        {"directory": str(root), "file": str(source), "arguments": [*compile_options, "-c", str(source)]}
        for source in sources
    ]
    (build / "compile_commands.json").write_text(json.dumps(compilation_database, indent=2) + "\n", encoding="utf-8")
    subprocess.run([str(executable), "--self-test"], check=True, cwd=root)
    cases = json.loads((root / "contracts/protocol-cases.json").read_text(encoding="utf-8"))
    result = subprocess.run([str(executable)], input="\n".join(case["line"] for case in cases) + "\n",
                            text=True, capture_output=True, check=True, cwd=root)
    answers = result.stdout.splitlines()
    if len(answers) != len(cases):
        raise AssertionError("El parser C++ no respondió a todos los casos.")
    for case, answer in zip(cases, answers):
        expected = "OK " + case["command"] if case["valid"] else "ERROR "
        if not answer.startswith(expected):
            raise AssertionError(f"Contrato incompatible: {case['name']}: {answer}")
    print(f"Contrato C++: {len(cases)} casos compartidos verificados.")


if __name__ == "__main__":
    main()
