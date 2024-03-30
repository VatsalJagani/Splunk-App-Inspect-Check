import os
import sys
import io
import shutil
import subprocess
from contextlib import contextmanager

@contextmanager
def setup_action_yml(test_app_repo,
                            app_dir=".",
                            use_ucc_gen="false",
                            to_make_permission_changes="false",
                            is_app_inspect_check="true",
                            splunkbase_username="NONE",
                            splunkbase_password="NONE",
                            app_utilities="",
                            my_github_token="NONE",
                            current_branch="NONE",
                            logger_log_files_prefix="NONE",
                            logger_sourcetype="NONE",
                            splunk_python_sdk_install_path="bin",
                            is_remove_pyc_from_splunklib_dir="true"):

    app_dir_path = os.path.join(os.path.dirname(__file__), "test_app_repos", test_app_repo)
    print(f"TestIntegration.setup_action_yml_work -> app_dir_path={app_dir_path}")

    # copy the app module there
    shutil.copytree(app_dir_path, os.path.join("repodir"))

    # setup inputs
    os.environ["SPLUNK_app_dir"] = app_dir
    os.environ["SPLUNK_use_ucc_gen"] = use_ucc_gen
    os.environ["SPLUNK_to_make_permission_changes"] = to_make_permission_changes
    os.environ["SPLUNK_is_app_inspect_check"] = is_app_inspect_check
    os.environ["SPLUNK_splunkbase_username"] = splunkbase_username
    os.environ["SPLUNK_splunkbase_password"] = splunkbase_password
    os.environ["SPLUNK_app_utilities"] = app_utilities
    os.environ["GITHUB_TOKEN"] = my_github_token
    os.environ["SPLUNK_current_branch_name"] = current_branch
    os.environ["SPLUNK_logger_log_files_prefix"] = logger_log_files_prefix
    os.environ["SPLUNK_logger_sourcetype"] = logger_sourcetype
    os.environ["SPLUNK_splunk_python_sdk_install_path"] = splunk_python_sdk_install_path
    os.environ["SPLUNK_is_remove_pyc_from_splunklib_dir"] = is_remove_pyc_from_splunklib_dir

    try:
        yield
    finally:
        print("TestIntegration Cleanup after each test-case.")
        try:
            shutil.rmtree("repodir")
        except:
            pass

        try:
            shutil.rmtree("without_ucc_build")
        except:
            pass

        try:
            shutil.rmtree("ucc_build_dir")
        except:
            pass

        for filename in os.listdir():
            if filename.startswith("my_app_"):
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)


@contextmanager
def get_temp_directory():
    temp_dir = os.path.join(os.path.dirname(__file__), 'tempdir')
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    try:
        yield temp_dir
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@contextmanager
def get_temp_git_repo(current_branch="my_current_branch"):
    temp_dir = os.path.join(os.path.dirname(__file__), 'temprepo')
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    original_pwd = os.getcwd()

    os.chdir(temp_dir)

    os.environ["GITHUB_TOKEN"] = "this_is_my_github_token"
    os.environ["SPLUNK_current_branch_name"] = current_branch

    # Initialize a git repository
    subprocess.run(['git', 'init'], check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)

    # Create some initial files and commit them
    with open('file1.txt', 'w') as f:
        f.write('Initial content')
    subprocess.run(['git', 'add', 'file1.txt'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)

    # Create a branch
    subprocess.run(['git', 'checkout', '-b', current_branch], check=True)

    try:
        yield temp_dir
    finally:
        del os.environ["GITHUB_TOKEN"]
        del os.environ["SPLUNK_current_branch_name"]

        os.chdir(original_pwd)  # go back to original directory

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)



@contextmanager
def stdout_capture():
    # Redirect stdout to a StringIO object
    captured_output = io.StringIO()
    sys.stdout = captured_output

    try:
        yield captured_output
    finally:
        # Reset stdout to its original value
        sys.stdout = sys.__stdout__


@contextmanager
def setup_temporary_env_vars(vars):
    for name, value in vars.items():
        os.environ[name] = value
    try:
        yield
    finally:
        for name, value in vars.items():
            del os.environ[name]
