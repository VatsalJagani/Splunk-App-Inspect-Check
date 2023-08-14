
import os

import helper_github_action as utils
from helper_file_handler import FullRawFileHandler
from utilities.base_utility import BaseUtility


class CommonJSUtilitiesFile(BaseUtility):

    def implement_utility(self):
        utils.info("Adding CommonJSUtilitiesFile")

        folder_path = os.path.join(
            utils.CommonDirPaths.APP_DIR, 'appserver', 'static')
        file_path = os.path.join(
            folder_path, 'splunk_common_js_v_utilities.js')

        os.chdir(utils.CommonDirPaths.APP_DIR)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        is_updated = FullRawFileHandler(
            os.path.join(os.path.dirname(__file__),
                         'splunk_common_js_v_utilities.js'),
            os.path.join(file_path)
        ).validate_file_content()

        if is_updated:
            utils.info("Change in the file splunk_common_js_v_utilities.js")
            return file_path
        utils.info("No change in the file splunk_common_js_v_utilities.js")
