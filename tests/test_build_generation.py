
import unittest
import os
import glob
import tarfile

from .helper import setup_action_yml
from main import main



def get_file_permissions(filepath):
    """
    Gets the Linux permissions of a file as a string.

    Args:
        filepath (str): The path to the file for which permissions are needed.

    Returns:
        str: A string representation of the file permissions (e.g., "rwxr-xr-x").
    """
    try:
        # Get file stat information
        stat = os.stat(filepath)
    except OSError as e:
        # Handle potential errors (e.g., file not found, permission denied)
        print(f"Error getting file permissions: {e}")
        return None

    # Extract permission bits using stat.st_mode
    permissions = stat.st_mode

    # Define permission character mappings for readability
    permission_map = {
        0: '-',  # No permission
        1: '--x',  # Execute
        2: '-w-',  # Write
        3: '-wx',  # Write + Execute
        4: 'r--',  # Read
        5: 'r-x',  # Read + Execute
        6: 'rw-',  # Read + Write
        7: 'rwx'   # Read + Write + Execute
    }

    # Separate permission sets for owner, group, and others
    owner_perms = (permissions >> 6) & 0o7  # User permissions
    group_perms = (permissions >> 3) & 0o7  # Group permissions
    other_perms = permissions & 0o7  # Other permissions

    # Convert permission bits to characters using the map
    owner_str = permission_map[owner_perms]
    group_str = permission_map[group_perms]
    other_str = permission_map[other_perms]

    # Combine permission strings for owner, group, and others
    file_permissions = f"{owner_str}{group_str}{other_str}"

    return file_permissions


def remove_ds_store_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == ".DS_Store":
                os.remove(os.path.join(root, file))


class TestAppBuild(unittest.TestCase):

    def extract_app_build(self, tgz_file):
        # Create a temporary directory to extract the contents
        extract_dir = "temp_extraction"
        os.makedirs(extract_dir, exist_ok=True)

        try:
            # Extract the contents of the .tgz file
            with tarfile.open(tgz_file, 'r:gz') as tar:
                tar.extractall(extract_dir)

            remove_ds_store_files(extract_dir)

            # Initialize counters
            all_files = []
            all_folders = []
            is_root = True

            # Walk through the extracted directory
            for root, dirs, files in os.walk(extract_dir):
                if is_root:
                    is_root = False
                    continue

                for file in files:
                    relative_path = os.path.relpath(os.path.join(root, file), extract_dir)
                    # print("DEBUG: File:", relative_path)
                    all_files.append(relative_path)

                for dir in dirs:
                    relative_path = os.path.relpath(os.path.join(root, dir), extract_dir)
                    all_folders.append(relative_path)

            print("DEBUG: Total Files:", len(all_files))
            print("DEBUG: Total Folders:", len(all_folders))
            print(f"DEBUG: All Files: {all_files}")
            print(f"DEBUG: All Folders: {all_folders}")
            return len(all_files), len(all_folders), all_files, all_folders

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
        with setup_action_yml("repo_1_regular_build", app_dir="my_app_1", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_1_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files, _ = self.extract_app_build(app_build_name)
            assert folder_count == 7
            assert file_count == 10
            assert "my_app_1/static/appIconAlt.png" in all_files
            assert "my_app_1/default/data/ui/views/assets.xml" in all_files
            assert "my_app_1/default/app.conf" in all_files


    def test_build_repo_root_as_app_dir(self):
        with setup_action_yml("repo_root_as_app_dir", app_dir=".", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_1_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files, _ = self.extract_app_build(app_build_name)
            assert folder_count == 7
            assert file_count == 10
            assert "my_app_1/static/appIconAlt.png" in all_files
            assert "my_app_1/default/data/ui/views/assets.xml" in all_files
            assert "my_app_1/default/app.conf" in all_files


    def test_ucc_build_1_regular(self):
        with setup_action_yml("repo_ucc_1_regular_build", app_dir="my_ta", use_ucc_gen="true", is_app_inspect_check="false"):
            main()

            app_build_name_pattern = "my_app_ucc_1_1_0_1_*"
            app_build_files = glob.glob(app_build_name_pattern)

            if not app_build_files or len(app_build_files) <= 0:
                assert f"No app build with name {app_build_name_pattern} found."

            app_build_name = app_build_files[0]
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_ucc_1/default/app.conf" in all_files
            assert "my_app_ucc_1/appserver/static/js/build/globalConfig.json" in all_files
            assert "my_app_ucc_1/lib/splunklib/client.py" in all_files
            assert "my_app_ucc_1/default/data/ui/views/inputs.xml" in all_files
            assert "my_app_ucc_1/bin/api.py" in all_files
            assert "my_app_ucc_1/bin/my_input.py" in all_files
            assert all("package/" not in s for s in all_files), "'package' folder should not be present in folder structure of the build."
            assert all("my_app_ucc_1/globalConfig.json" not in s for s in all_files), "'globalConfig.json' file shouldn't be in the root of the App."
            assert all("additional_packaging.py" not in s for s in all_files), "'additional_packaging.py' file shouldn't be part of the App build."

            assert "my_app_ucc_1/lib/splunklib/modularinput" in all_folders
            assert "my_app_ucc_1/lib/solnlib" in all_folders
            assert "my_app_ucc_1/appserver/static/js/build" in all_folders
            assert "my_app_ucc_1/lib/splunktaucclib/common" in all_folders


    def test_ucc_build_repo_root_as_app_dir(self):
        with setup_action_yml("repo_ucc_2_repo_root_as_app_dir", app_dir=".", use_ucc_gen="true", is_app_inspect_check="false"):
            main()

            app_build_name_pattern = "my_app_ucc_1_1_0_1_*"
            app_build_files = glob.glob(app_build_name_pattern)

            if not app_build_files or len(app_build_files) <= 0:
                assert f"No app build with name {app_build_name_pattern} found."

            app_build_name = app_build_files[0]
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_ucc_1/default/app.conf" in all_files
            assert "my_app_ucc_1/appserver/static/js/build/globalConfig.json" in all_files
            assert "my_app_ucc_1/lib/splunklib/client.py" in all_files
            assert "my_app_ucc_1/default/data/ui/views/inputs.xml" in all_files
            assert "my_app_ucc_1/bin/api.py" in all_files
            assert "my_app_ucc_1/bin/my_input.py" in all_files
            assert all("package/" not in s for s in all_files), "'package' folder should not be present in folder structure of the build."
            assert all("my_app_ucc_1/globalConfig.json" not in s for s in all_files), "'globalConfig.json' file shouldn't be in the root of the App."
            assert all("additional_packaging.py" not in s for s in all_files), "'additional_packaging.py' file shouldn't be part of the App build."

            assert "my_app_ucc_1/lib/splunklib/modularinput" in all_folders
            assert "my_app_ucc_1/lib/solnlib" in all_folders
            assert "my_app_ucc_1/appserver/static/js/build" in all_folders
            assert "my_app_ucc_1/lib/splunktaucclib/common" in all_folders


    def test_file_permission_check_no_change(self):
        with setup_action_yml("repo_file_permission", app_dir="my_app_2", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_2_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_2/bin/file1.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file1.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file2.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file2.sh") == "rw-r--r--"
            assert "my_app_2/bin/file3.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file3.txt") == "rwxr-xr-x"
            assert "my_app_2/bin/file4.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file4.txt") == "rw-r--r--"


    def test_file_auto_change_permission(self):
        with setup_action_yml("repo_file_permission", app_dir="my_app_2", to_make_permission_changes="true", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_2_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            file_count, folder_count, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_2/bin/file1.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file1.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file2.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file2.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file3.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file3.txt") == "rw-r--r--"
            assert "my_app_2/bin/file4.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file4.txt") == "rw-r--r--"


    def test_file_permission_check_no_change_2(self):
        with setup_action_yml("repo_file_permission_repo_root_as_app_dir", app_dir=".", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_2_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_2/bin/file1.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file1.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file2.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file2.sh") == "rw-r--r--"
            assert "my_app_2/bin/file3.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file3.txt") == "rwxr-xr-x"
            assert "my_app_2/bin/file4.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file4.txt") == "rw-r--r--"


    def test_file_auto_change_permission_2(self):
        with setup_action_yml("repo_file_permission_repo_root_as_app_dir", app_dir=".", to_make_permission_changes="true", is_app_inspect_check="false"):
            main()

            app_build_name = "my_app_2_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_2/bin/file1.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file1.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file2.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file2.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file3.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file3.txt") == "rw-r--r--"
            assert "my_app_2/bin/file4.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file4.txt") == "rw-r--r--"


    def test_file_permission_change_via_user_commands(self):
        with setup_action_yml("repo_file_permission", app_dir="my_app_2", is_app_inspect_check="false"):
            os.environ["SPLUNK_APP_ACTION_1"] = "find . -type f -exec chmod 644 '{}' \\;"
            os.environ["SPLUNK_APP_ACTION_2"] = "find . -type f -name '*.sh' -exec chmod +x '{}' \\;"
            os.environ["SPLUNK_APP_ACTION_3"] = "find . -type d -exec chmod 755 '{}' \\;"

            main()

            os.environ.pop("SPLUNK_APP_ACTION_1")
            os.environ.pop("SPLUNK_APP_ACTION_2")
            os.environ.pop("SPLUNK_APP_ACTION_3")

            app_build_name = "my_app_2_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_2/bin/file1.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file1.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file2.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file2.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file3.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file3.txt") == "rw-r--r--"
            assert "my_app_2/bin/file4.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file4.txt") == "rw-r--r--"


    def test_file_permission_change_via_user_commands_root_dir(self):
        with setup_action_yml("repo_file_permission_repo_root_as_app_dir", app_dir=".", is_app_inspect_check="false"):
            os.environ["SPLUNK_APP_ACTION_1"] = "find . -type f -exec chmod 644 '{}' \\;"
            os.environ["SPLUNK_APP_ACTION_2"] = "find . -type f -name '*.sh' -exec chmod +x '{}' \\;"
            os.environ["SPLUNK_APP_ACTION_3"] = "find . -type d -exec chmod 755 '{}' \\;"

            main()

            os.environ.pop("SPLUNK_APP_ACTION_1")
            os.environ.pop("SPLUNK_APP_ACTION_2")
            os.environ.pop("SPLUNK_APP_ACTION_3")

            app_build_name = "my_app_2_1_1_2_1.tgz"
            assert os.path.isfile(app_build_name)

            _, _, all_files, all_folders = self.extract_app_build(app_build_name)
            assert "my_app_2/bin/file1.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file1.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file2.sh" in all_files
            assert get_file_permissions("my_app_2/bin/file2.sh") == "rwxr-xr-x"
            assert "my_app_2/bin/file3.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file3.txt") == "rw-r--r--"
            assert "my_app_2/bin/file4.txt" in all_files
            assert get_file_permissions("my_app_2/bin/file4.txt") == "rw-r--r--"
