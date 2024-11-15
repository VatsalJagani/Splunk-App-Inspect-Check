# This file is generated and maintained by splunk-app-action (https://github.com/VatsalJagani/splunk-app-action)
# To modify anything create Pull Request on the splunk-app-action GitHub repository.

import os
import re
import configparser


def get_all_stanzas(config_file_path):
    """
    Retrieves all stanzas (sections) from a configuration file.

    Args:
        config_file_path (str): Path to the configuration file.

    Returns:
        list: A list of stanza (section) names.

    Raises:
        configparser.Error: If there's an error parsing the configuration file.
    """
    try:
        config = configparser.ConfigParser()
        config.read(config_file_path)

        return config.sections()

    except configparser.Error as e:
        raise ValueError(f"Error parsing configuration file '{config_file_path}': {e}")


def get_all_input_names(addon_name):
    """
    Get all Input names from Add-on
    """
    return get_all_stanzas(os.path.join('output', addon_name, 'default', 'inputs.conf'))


def _util_generate_input_class_name(input_name):
    # Replace all non-alphanumeric characters (including spaces, hyphens, etc.) with underscores
    input_name = re.sub(r'[^a-zA-Z0-9]', '_', input_name)
    # Split the string by underscores
    words = input_name.split('_')
    # Capitalize the first letter of each word except the first one
    camel_case_name = words[0] + ''.join(word.capitalize() for word in words[1:])
    # Ensure the class name starts with a capital letter
    camel_case_name = camel_case_name[0].upper() + camel_case_name[1:]

    return f"{camel_case_name}Handler"


def modify_original_input_py_file(addon_name, input_name):
    file_path = os.path.join('output', addon_name, 'bin', f'{input_name}.py')
    with open(file_path, "r") as f:
        file_content = f.read()

    input_class_name = _util_generate_input_class_name(input_name)

    input_class_import_statement = f"from {input_name}_handler import {input_class_name}"

    if input_class_import_statement not in file_content:
        # Only add import if not present already
        file_content = re.sub(
            r"^(import\s+import_declare_test.*)$",
            r"\1\n" + input_class_import_statement,
            file_content,
            flags=re.MULTILINE
        )

    # Update validate_input method
    pattern_validate_input_fun = r"def validate_input[\w\W]*return\n"
    replacement_content_validate_input_fun = f"def validate_input(self, definition: smi.ValidationDefinition):\n        {input_class_name}(self).validate_input(definition)\n\n"

    file_content = re.sub(pattern_validate_input_fun, replacement_content_validate_input_fun, file_content)

    # Update stream_events method
    pattern_stream_events_fun = r"def stream_events[\w\W]*(?:\n\n)"
    replacement_content_stream_events_fun = f"def stream_events(self, inputs: smi.InputDefinition, event_writer: smi.EventWriter):\n        {input_class_name}(self).stream_events(inputs, event_writer)\n\n\n"

    file_content = re.sub(pattern_stream_events_fun, replacement_content_stream_events_fun, file_content)

    with open(file_path, "w") as f:
        f.write(file_content)


def additional_packaging(addon_name):
    print("Running additional_packaging.py for better inputs python handler file generation.")

    # Iterate over all inputs available
    for i in get_all_input_names(addon_name):
        print(f"Processing Input={i}")
        modify_original_input_py_file(addon_name, i)
