import os
import platform
import subprocess


class FileNotFoundOnDisk(Exception):
    pass


class LaunchFailed(Exception):
    pass


def open_file(path, quiet=False):
    # check the file actually exists before asking the OS to open it
    if not path or not os.path.isfile(path):
        raise FileNotFoundOnDisk(path)

    system = platform.system()
    # print(f"open_file: system={system} path={path}")  # debug

    # quiet=True suppresses the launched program's stdout/stderr
    # so xdg-open diagnostic noise doesn't bleed into our terminal
    if quiet:
        capture = {"capture_output": True}
    else:
        capture = {}

    try:
        if system == "Darwin":
            # macOS -- use the built-in open command
            subprocess.run(["open", path], check=True, **capture)

        elif system == "Windows":
            # os.startfile is windows-only -- not available on mac/linux
            # no subprocess here so nothing to suppress
            os.startfile(path)  # type: ignore[attr-defined]

        else:
            # linux and other unix-likes
            # note: xdg-open exit code isn't perfectly reliable on all desktop environments
            subprocess.run(["xdg-open", path], check=True, **capture)

    except (subprocess.CalledProcessError, OSError) as e:
        raise LaunchFailed(f"Could not open '{path}': {e}")
