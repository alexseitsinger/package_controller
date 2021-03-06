import json
import toml
from io import open

from ..utils.run import run
from ..utils.find_file import find_file
from ..utils.replace_line import replace_line
from ..utils.assert_which import assert_which
from ..utils.python.is_python_package import is_python_package
from ..utils.python.get_python_package_version import get_python_package_version
from ..utils.node.is_node_package import is_node_package


def pin_versions_python(toml_dict, name):
    deps = toml_dict.get(name, None)
    if deps is None:
        return
    for k, v in deps.items():
        version = v
        if version == "*":
            version = get_python_package_version(k)
            toml_dict[name][k] = "=={}".format(version)


def pin_python(development):
    pipfile = find_file("Pipfile")

    toml_dict = None
    with open(pipfile, "r") as f:
        toml_dict = toml.loads(f.read())

    if toml_dict is None:
        raise RuntimeError("Failed to read Pipfile")

    pin_versions_python(toml_dict, "packages")
    if development is True:
        pin_versions_python(toml_dict, "dev-packages")

    with open(pipfile, "w") as f:
        f.write(toml.dumps(toml_dict))

    return {"packages": True, "dev-packages": development}


def pin_versions_node(json_dict, key):
    deps = json_dict.get(key, None)
    if deps is None:
        return
    for k, v in deps.items():
        version = v
        if version.startswith("^"):
            version = version[1:]
        deps[k] = version


def pin_node(development, peer, optional):
    # Find the package file we're going to alter.
    package_file = find_file("package.json")

    # Get the original content from the package file
    original_content = None
    with open(package_file, "r") as f:
        # Read the JSON into a dictionary.
        original_content = json.loads(f.read())

    # If we didnt get the original content, there wa san error.
    if original_content is None:
        raise RuntimeError("Failed to read package file.")

    # Process the deps
    pin_versions_node(original_content, "dependencies")
    if development is True:
        pin_versions_node(original_content, "devDependencies")
    if peer is True:
        pin_versions_node(original_content, "peerDependencies")
    if optional is True:
        pin_versions_node(original_content, "optionalDependencies")

    # Write the new content to the file.
    with open(package_file, "w") as f:
        f.write(json.dumps(original_content, indent=2, sort_keys=True))

    # Return a dictionary of each section that was pinned.
    return {
        "dependencies": True,
        "devDependencies": development,
        "optionalDependencies": optional,
        "peerDependencies": peer,
    }


def pin(development=False, optional=False, peer=False):
    is_python = is_python_package()
    is_node = is_node_package()
    if is_python and not is_node:
        return pin_python(development)
    elif is_node and not is_python:
        return pin_node(development, optional, peer)
    elif is_node and is_python:
        raise RuntimeError("Both python and node packages were detected.")
    else:
        raise RuntimeError("Neither python nor node package was detected.")
