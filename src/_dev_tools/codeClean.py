import json
from sys import platform
from subprocess import run

div = "=================================="
use_shell = platform == "win32"

print(f"\nFinding unused dependencies\n{div}\n")

cmd = ["npx", "depcheck", "--json"]
depcheck_result = run(cmd, shell=use_shell, capture_output=True, text=True)

unused_dependencies = json.loads(depcheck_result.stdout)["dependencies"]
if len(unused_dependencies) > 0:
    print(f"Found these unused dependencies\n{div}")
    print(*unused_dependencies, sep="\n")

    affirmative_responses = {"y", "yes", "Y", "YES", ""}
    response = input(f"{div}\n\nRemove all? [yes] ").lower() in affirmative_responses

    if response:
        cmd = ["yarn", "remove", *unused_dependencies]
        run(cmd, shell=use_shell)

    print(f"\nDone!\n{div}\n")

else:
    print(f"\nDone! - No unused dependencies found.\n{div}\n")
