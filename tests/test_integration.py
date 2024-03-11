import os, sys

# path to be added -> /<this-repo>/tests/src
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'src'
    )
)

import unittest
from unittest.mock import patch

import glob
import shutil
import tarfile
from contextlib import contextmanager

from main import main


@contextmanager
def setup_action_yml_work(test_app_repo,
                            app_dir=".",
                            is_generate_build="true",
                            use_ucc_gen="false",
                            to_make_permission_changes="false",
                            is_app_inspect_check="true",
                            splunkbase_username="NONE",
                            splunkbase_password="NONE",
                            app_build_path="NONE",
                            app_utilities="",
                            my_github_token="NONE",
                            current_branch="NONE",
                            logger_log_files_prefix="NONE",
                            logger_sourcetype="NONE"):

    app_dir_path = os.path.join(os.path.dirname(__file__), "test_app_repos", test_app_repo)
    print(f"TestIntegration.setup_action_yml_work -> app_dir_path={app_dir_path}")

    # copy the app module there
    shutil.copytree(app_dir_path, os.path.join("repodir"))

    # setup inputs
    os.environ["SPLUNK_app_dir"] = app_dir
    os.environ["SPLUNK_is_generate_build"] = is_generate_build
    os.environ["SPLUNK_use_ucc_gen"] = use_ucc_gen
    os.environ["SPLUNK_to_make_permission_changes"] = to_make_permission_changes
    os.environ["SPLUNK_is_app_inspect_check"] = is_app_inspect_check
    os.environ["SPLUNK_splunkbase_username"] = splunkbase_username
    os.environ["SPLUNK_splunkbase_password"] = splunkbase_password
    os.environ["SPLUNK_app_build_path"] = app_build_path
    os.environ["SPLUNK_app_utilities"] = app_utilities
    os.environ["GITHUB_TOKEN"] = my_github_token
    os.environ["SPLUNK_current_branch_name"] = current_branch
    os.environ["SPLUNK_logger_log_files_prefix"] = logger_log_files_prefix
    os.environ["SPLUNK_logger_sourcetype"] = logger_sourcetype

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



class TestIntegration(unittest.TestCase):
    def setup_method(self, test_method):
        print("TestIntegration.setup_method")

        # Mock the set_env function during the test
        patcher = patch("helpers.github_action_utils.set_env")
        self.mock_set_env = patcher.start()

        def mock_set_env(name, value):
            print(f"Mocked set_env called with args: name={name}, value={value}")
            os.environ[name] = value
        self.mock_set_env.side_effect = mock_set_env


    def extract_app_build(self, tgz_file):
        # Create a temporary directory to extract the contents
        extract_dir = "temp_extraction"
        os.makedirs(extract_dir, exist_ok=True)

        try:
            # Extract the contents of the .tgz file
            with tarfile.open(tgz_file, 'r:gz') as tar:
                tar.extractall(extract_dir)

            # Initialize counters
            file_count = 0
            folder_count = 0
            all_files = []
            is_root = True

            # Walk through the extracted directory
            for root, dirs, files in os.walk(extract_dir):
                if is_root:
                    is_root = False
                    continue

                folder_count += len(dirs)
                file_count += len(files)

                # Print relative paths of files
                for file in files:
                    relative_path = os.path.relpath(os.path.join(root, file), extract_dir)
                    print("DEBUG: File:", relative_path)
                    all_files.append(relative_path)

            print("DEBUG: Total Files:", file_count)
            print("DEBUG: Total Folders:", folder_count)
            # print(f"All Files: {all_files}")
            return file_count, folder_count, all_files

        finally:
            # Cleanup: Remove the temporary extraction directory
            if os.path.exists(extract_dir):
                for root, dirs, files in os.walk(extract_dir, topdown=False):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))
                os.rmdir(extract_dir)



    def test_build_1_regular(self):
        with setup_action_yml_work("repo_1_regular_build", app_dir="my_app_1", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_1_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files = self.extract_app_build(app_build_name)
            assert folder_count == 7
            assert file_count == 10
            assert "my_app_1/static/appIconAlt.png" in all_files
            assert "my_app_1/default/data/ui/views/assets.xml" in all_files
            assert "my_app_1/default/app.conf" in all_files


    def test_build_repo_root_as_app_dir(self):
        with setup_action_yml_work("repo_root_as_app_dir", app_dir=".", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_1_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files = self.extract_app_build(app_build_name)
            assert folder_count == 7
            assert file_count == 10
            assert "my_app_1/static/appIconAlt.png" in all_files
            assert "my_app_1/default/data/ui/views/assets.xml" in all_files
            assert "my_app_1/default/app.conf" in all_files


    def test_ucc_build_1_regular(self):
        with setup_action_yml_work("repo_ucc_1_regular_build", app_dir="my_ta", use_ucc_gen="true", is_app_inspect_check="false"):
            main()

            app_build_name_pattern = "my_app_ucc_1_1_0_1_*"
            app_build_files = glob.glob(app_build_name_pattern)

            if not app_build_files or len(app_build_files) <= 0:
                assert f"No app build with name {app_build_name_pattern} found."

            app_build_name = app_build_files[0]
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files = self.extract_app_build(app_build_name)
            assert folder_count == 57
            assert file_count == 362
            assert "my_app_ucc_1/default/app.conf" in all_files
            assert "my_app_ucc_1/appserver/static/js/build/globalConfig.json" in all_files
            assert "my_app_ucc_1/lib/splunklib/client.py" in all_files
            assert "my_app_ucc_1/default/data/ui/views/inputs.xml" in all_files
            assert "my_app_ucc_1/bin/api.py" in all_files
            assert "my_app_ucc_1/bin/my_input.py" in all_files
            assert all("package/" not in s for s in all_files), "'package' folder should not be present in folder structure of the build."
            assert all("my_app_ucc_1/globalConfig.json" not in s for s in all_files), "'globalConfig.json' file shouldn't be in the root of the App."
            assert all("additional_packaging.py" not in s for s in all_files), "'additional_packaging.py' file shouldn't be part of the App build."


    def test_ucc_build_repo_root_as_app_dir(self):
        with setup_action_yml_work("repo_ucc_2_repo_root_as_app_dir", app_dir=".", use_ucc_gen="true", is_app_inspect_check="false"):
            main()

            app_build_name_pattern = "my_app_ucc_1_1_0_1_*"
            app_build_files = glob.glob(app_build_name_pattern)

            if not app_build_files or len(app_build_files) <= 0:
                assert f"No app build with name {app_build_name_pattern} found."

            app_build_name = app_build_files[0]
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files = self.extract_app_build(app_build_name)
            assert folder_count == 57
            assert file_count == 362
            assert "my_app_ucc_1/default/app.conf" in all_files
            assert "my_app_ucc_1/appserver/static/js/build/globalConfig.json" in all_files
            assert "my_app_ucc_1/lib/splunklib/client.py" in all_files
            assert "my_app_ucc_1/default/data/ui/views/inputs.xml" in all_files
            assert "my_app_ucc_1/bin/api.py" in all_files
            assert "my_app_ucc_1/bin/my_input.py" in all_files
            assert all("package/" not in s for s in all_files), "'package' folder should not be present in folder structure of the build."
            assert all("my_app_ucc_1/globalConfig.json" not in s for s in all_files), "'globalConfig.json' file shouldn't be in the root of the App."
            assert all("additional_packaging.py" not in s for s in all_files), "'additional_packaging.py' file shouldn't be part of the App build."

