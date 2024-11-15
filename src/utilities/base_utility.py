
import os
import shutil
from helpers.git_manager import GitHubPR, get_file_hash, get_multi_files_hash, get_folder_hash
import helpers.github_action_utils as utils
from helpers.global_variables import GlobalVariables


class BaseUtility:
    def __init__(self, app_read_dir, app_write_dir) -> None:
        self.app_read_dir = app_read_dir
        self.app_write_dir = app_write_dir


    def remove_pycache(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".pyc"):
                    os.remove(os.path.join(root, file))
            for dir in dirs:
                if dir == "__pycache__":
                    shutil.rmtree(os.path.join(root, dir))


    def add(self):
        with GitHubPR(self.app_write_dir) as github:
            files_or_folders_updated = self.implement_utility()
            hash = None

            if not files_or_folders_updated:
                utils.info(f"Utility={type(self).__name__} has no change.")
                return

            if type(files_or_folders_updated) == list:
                hash = get_multi_files_hash(files_or_folders_updated)

            else:
                if os.path.isfile(files_or_folders_updated):
                    hash = get_file_hash(files_or_folders_updated)
                elif os.path.isdir(files_or_folders_updated):
                    hash = get_folder_hash(files_or_folders_updated)
                else:
                    utils.error("File to generate hash is invalid.")

            remove_pyc_before_commit = utils.str_to_boolean_default_true(
                utils.get_input('remove_pyc_before_commit'))
            utils.info(f"remove_pyc_before_commit: {remove_pyc_before_commit}")

            # Removing .pyc and __pycache__
            if remove_pyc_before_commit:
                self.remove_pycache(GlobalVariables.ORIGINAL_APP_DIR_PATH)

            if hash:
                utils.debug("Committing and creating PR for the code change.")
                github.commit_and_pr(hash=hash)
            else:
                utils.error(
                    "Unable to get hash to generate PR for app utility.")


    def implement_utility(self):
        raise NotImplementedError(
            "The implement_utility function must be implemented in the child class.")
