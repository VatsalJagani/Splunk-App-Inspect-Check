
import os
import re
import json

import helpers.github_action_utils as utils
from helpers.file_manager import FullRawFileHandler
from utilities.base_utility import BaseUtility


def _util_generate_input_class_name(input_name):
    # Replace all non-alphanumeric characters (including spaces, hyphens, etc.) with underscores
    input_name = re.sub(r'[^a-zA-Z0-9]', '_', input_name)
    # Split the string by underscores
    words = input_name.split('_')
    # Capitalize the first letter of each word except the first one
    camel_case_name = words[0] + ''.join(word.capitalize() for word in words[1:])
    # Ensure the class name starts with a capital letter
    camel_case_name = camel_case_name[0].upper() + camel_case_name[1:]

    return camel_case_name


def generate_input_handler_file(bin_folder_path, input_name):
    _file_path = os.path.join(bin_folder_path, f'{input_name}_handler.py')

    if os.path.exists(_file_path):
        print(f"Input handler python file for {input_name} already created. ignoring...")
        return False
    else:
        print(f"Creating input handler python file for {input_name}.")

    input_class_name = _util_generate_input_class_name(input_name)

    _content = f"""
from splunklib import modularinput as smi
from ucc_ta_helper import UCCTAInput, UCCTAInputCheckpointer


class {input_class_name}Handler(UCCTAInput):
    def collect(self, input_name: str, normalized_input_name: str, input_details: dict, account_details, checkpointer: UCCTAInputCheckpointer, ew: smi.EventWriter):
        self.write_event("This is my first event. I can possibly be a JSON event as well.")

"""
    with open(_file_path, 'w') as f:
        f.write(_content)

    return _file_path



def get_global_config_json(gc_path):
    with open(gc_path, 'r') as f:
        return json.load(f)


def get_all_input_names(gc):
    if not gc["pages"].get("inputs") or not gc["pages"].get("inputs").get("services"):
        return []
    
    input_list = []
    for i in gc["pages"].get("inputs").get("services"):
        input_list.append(i["name"])
    return input_list



class UCCHelperUtility(BaseUtility):

    def implement_utility(self):
        utils.info("Adding UCCHelperUtility")
        app_dir_path = os.path.dirname(self.app_write_dir)   # additional_packaging.py file has to be in the app_dir folder of the repo instead of in the package folder
        bin_folder_path = os.path.join(self.app_write_dir, "bin")

        files_changed = []


        utils.info("UCC -> ucc_ta_helper.py")
        ucc_ta_helper_file_path = os.path.join(bin_folder_path, 'ucc_ta_helper.py')

        is_updated = FullRawFileHandler(
            os.path.join(os.path.dirname(__file__),
                         'ucc_ta_helper.py'),
            os.path.join(ucc_ta_helper_file_path)
        ).validate_file_content()

        if is_updated:
            files_changed.append(ucc_ta_helper_file_path)


        utils.info("UCC -> additional_packaging.py")
        app_dir_path = os.path.dirname(self.app_write_dir)   # additional_packaging.py file has to be in the app_dir folder of the repo instead of in the package folder
        additional_packaging_file_path = os.path.join(app_dir_path, 'additional_packaging.py')

        if not os.path.exists(app_dir_path):
            os.makedirs(app_dir_path)

        is_updated = FullRawFileHandler(
            os.path.join(os.path.dirname(__file__),
                         'additional_packaging.py'),
            os.path.join(additional_packaging_file_path)
        ).validate_file_content()

        if is_updated:
            files_changed.append(additional_packaging_file_path)


        utils.info("UCC -> Input Handler Files")
        gc_path = os.path.join(app_dir_path, "globalConfig.json")
        gc = get_global_config_json(gc_path)

        # Iterate over all inputs available to create input handler file if not present
        for input_name in get_all_input_names(gc):
            _changed = generate_input_handler_file(bin_folder_path, input_name)
            if _changed:
                files_changed.append(_changed)


        if files_changed:
            utils.info("Change in the file additional_packaging.py or input_handler files.")
            return files_changed
        utils.info("No change in the file additional_packaging.py and input_handler files.")
