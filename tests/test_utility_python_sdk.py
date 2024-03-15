import os
from unittest.mock import patch
from .helper import get_temp_directory, stdout_capture

from utilities.splunk_sdk_python import SplunkPythonSDKUtility
from helpers import github_action_utils as utils


def test_splunk_sdk_utility_installed_new():
    with get_temp_directory() as temp_dir:
        sdk_utility = SplunkPythonSDKUtility("nothing", temp_dir)
        result = sdk_utility.implement_utility()

        # Validate the result
        folder_path = os.path.join(temp_dir, 'bin')
        splunklib_dir = os.path.join(folder_path, 'splunklib')
        init_file = os.path.join(splunklib_dir, '__init__.py')

        print(f"init_file={init_file}")

        assert result == init_file
        assert os.path.exists(init_file)


def test_splunk_sdk_utility_upgraded_existing():
    with get_temp_directory() as temp_dir:
        # Prepare the temporary directory
        folder_path = os.path.join(temp_dir, 'bin')
        os.makedirs(folder_path)
        splunklib_dir = os.path.join(folder_path, 'splunklib')
        os.makedirs(splunklib_dir)
        init_file = os.path.join(splunklib_dir, '__init__.py')
        with open(init_file, 'w') as f:
            f.write('__version_info__ = "1.0.0"')

        # Initialize SplunkPythonSDKUtility instance
        sdk_utility = SplunkPythonSDKUtility("nothing", temp_dir)

        with stdout_capture() as captured_stdout:
            # Call implement_utility function
            result = sdk_utility.implement_utility()
            
            # Get the captured stdout
            output = captured_stdout.getvalue()
            assert 'New splunklib version' in output.strip()

        # Validate the result
        assert os.path.exists(init_file)
        assert result == init_file


def test_splunk_sdk_utility_skipped_due_to_existing_and_same_version():
    with get_temp_directory() as temp_dir:
        # Prepare the temporary directory
        folder_path = os.path.join(temp_dir, 'bin')
        os.makedirs(folder_path)
        splunklib_dir = os.path.join(folder_path, 'splunklib')
        os.makedirs(splunklib_dir)
        init_file = os.path.join(splunklib_dir, '__init__.py')
        with open(init_file, 'w') as f:
            f.write('__version_info__ = "1.2.3"')

        with patch.object(SplunkPythonSDKUtility, '_get_splunklib_version', return_value="1.2.3"):
            # Initialize SplunkPythonSDKUtility instance
            sdk_utility = SplunkPythonSDKUtility("nothing", temp_dir)
            # Call implement_utility function
            result = sdk_utility.implement_utility()

        # Validate the result
        assert not os.path.exists(os.path.join(folder_path, 'splunk-sdk'))
        assert result is None


def test_splunk_sdk_utility_error_upgrading_existing():
    with get_temp_directory() as temp_dir:
        # Prepare the temporary directory
        folder_path = os.path.join(temp_dir, 'bin')
        os.makedirs(folder_path)
        splunklib_dir = os.path.join(folder_path, 'splunklib')
        os.makedirs(splunklib_dir)
        init_file = os.path.join(splunklib_dir, '__init__.py')
        with open(init_file, 'w') as f:
            f.write('__version_info__ = "1.0.0"')

        # Initialize SplunkPythonSDKUtility instance
        sdk_utility = SplunkPythonSDKUtility("nothing", temp_dir)

        # Call implement_utility function with failing upgrade
        with patch.object(SplunkPythonSDKUtility, '_get_splunklib_version', return_value="2.2.2"):
            with patch.object(utils, 'execute_system_command', return_value=(1, '')):
                result = sdk_utility.implement_utility()

        # Validate the result
        assert result is None
