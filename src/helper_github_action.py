import os
from datetime import datetime


# Debug function
def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)

        # only until level 2
        if level > 2:
            continue

        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


def str_to_boolean(value_in_str: str):
    value_in_str = str(value_in_str).lower()
    if value_in_str in ("false", "f", "0"):
        return False
    return True




def get_input(name):
    return os.getenv(f"SPLUNK_{name}")

def set_input(name, value):
    os.environ["SPLUNK_{}".format(name)] = value


def set_env(name, value):
    # os.environ[name] = value   # this does not work with github action
    # ret_code = os.system('export {}={}'.format(name, value))   # this does not work with github action
    ret_code = os.system('echo "{}={}" >> $GITHUB_ENV'.format(name, value))
    print("ret_code for setting env variable. {}".format(ret_code))


def set_output(name, value):
    print(f"::set-output name={name}::{_escape_data(value)}")


def format_message(message):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")
    return "{} | {}".format(timestamp, message)


def debug(message):
    message = format_message(message)
    print(f"::debug::{_escape_data(message)}")


def info(message):
    message = format_message(message)
    print(f"{_escape_data(message)}")


def warning(message):
    message = format_message(message)
    print(f"::warning::{_escape_data(message)}")


def error(message):
    message = format_message(message)
    print(f"::error::{_escape_data(message)}")


def group(title):
    print(f"::group::{title}")


def end_group():
    print(f"::endgroup::")


def add_mask(value):
    print(f"::add-mask::{_escape_data(value)}")


def stop_commands():
    print(f"::stop-commands::pause-commands")


def resume_commands():
    print(f"::pause-commands::")


def save_state(name, value):
    print(f"::save-state name={name}::{_escape_data(value)}")


def _escape_data(value: str):
    return value.replace("%", "%25").replace("\r", "%0D")
    # .replace("\n", "%0A")


class CommonDirPaths:
    MAIN_DIR = None
    REPO_DIR = None
    APP_DIR = None

    @staticmethod
    def generate_paths():
        if CommonDirPaths.MAIN_DIR is None:
            CommonDirPaths.MAIN_DIR = os.getcwd()
        if CommonDirPaths.REPO_DIR is None:
            CommonDirPaths.REPO_DIR = os.path.join(CommonDirPaths.MAIN_DIR, 'repodir')
        if CommonDirPaths.APP_DIR is None:
            app_dir = get_input('app_dir')
            CommonDirPaths.APP_DIR = os.path.join(CommonDirPaths.REPO_DIR, app_dir)

    def __init__(self):
        CommonDirPaths.generate_static_variable()