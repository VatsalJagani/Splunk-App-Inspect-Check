# This file is generated and maintained by splunk-app-action (https://github.com/VatsalJagani/splunk-app-action)
# To modify anything create Pull Request on the splunk-app-action GitHub repository.

import os
import json
import logging
import traceback
from urllib.parse import quote_plus

import import_declare_test

from solnlib.modular_input import checkpointer
from splunklib import modularinput as smi
from solnlib import conf_manager
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler

import logger_manager


def get_globalConfig_json_file_path():
    current_dir = os.path.dirname(__file__)
    config_relative_path = os.path.join(current_dir, '..', 'appserver', 'static', 'js', 'build', 'globalConfig.json')
    # Normalize the path to make sure it's correct (e.g., resolving '..' and handling separators)
    return os.path.normpath(config_relative_path)

def get_global_config_json():
    with open(get_globalConfig_json_file_path(), 'r') as f:
        return json.load(f)

def get_addon_name_and_normalized_name():
    gc = get_global_config_json()
    addon_name = gc["meta"]["name"]
    normalized_name = gc["meta"]["restRoot"].lower()
    return addon_name, normalized_name

ADDON_NAME, NORMALIZED_ADDON_NAME = get_addon_name_and_normalized_name()



def str_to_boolean_default_true(value_in_str: str):
    value_in_str = str(value_in_str).lower()
    if value_in_str in ("false", "f", "0", "n", "no"):
        return False
    return True


def str_to_boolean_default_false(value_in_str: str):
    value_in_str = str(value_in_str).lower()
    if value_in_str in ("true", "t", "1", "y", "yes"):
        return True
    return False



def get_ucc_ta_settings(session_key: str):
    try:
        settings_cfm = conf_manager.ConfManager(
            session_key,
            ADDON_NAME,
            realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-{NORMALIZED_ADDON_NAME}_settings")

        ucc_ta_settings = settings_cfm.get_conf(
            f"{NORMALIZED_ADDON_NAME}_settings")
        return ucc_ta_settings
    except:
        return None


def get_ucc_ta_log_level(session_key: str):
    try:
        logging_details = get_ucc_ta_settings(session_key).get("logging")

        log_level = logging_details.get('loglevel') if (
            logging_details.get('loglevel')) else 'INFO'

        return log_level
    except:
        return logging.INFO



def get_ucc_ta_account_details(session_key: str, account_name: str):
    cfm = conf_manager.ConfManager(
        session_key,
        ADDON_NAME,
        realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-{NORMALIZED_ADDON_NAME}_account",
    )
    account_conf_file = cfm.get_conf(f"{NORMALIZED_ADDON_NAME}_account")
    return account_conf_file.get(account_name)



def get_proxy_settings(session_key):
    """
    This function fetches proxy settings
    :param session_key: session key for particular modular input
    :return : proxy settings
    """
    ta_settings = get_ucc_ta_settings(session_key)

    if "proxy" in ta_settings and ta_settings["proxy"]:
        proxy_settings = None
        proxy_stanza = {}
        for key, value in ta_settings["proxy"].items():
            proxy_stanza[key] = value

        if int(proxy_stanza.get("proxy_enabled", 0)) == 0:
            return proxy_settings

        proxy_port = proxy_stanza.get('proxy_port')
        proxy_url = proxy_stanza.get('proxy_url')
        proxy_type = proxy_stanza.get('proxy_type')
        proxy_username = proxy_stanza.get('proxy_username', '')
        proxy_password = proxy_stanza.get('proxy_password', '')

        if proxy_username and proxy_password:
            proxy_username = quote_plus(proxy_username)
            proxy_password = quote_plus(proxy_password)
            proxy_uri = "%s://%s:%s@%s:%s" % (proxy_type, proxy_username,
                                            proxy_password, proxy_url, proxy_port)
        else:
            proxy_uri = "%s://%s:%s" % (proxy_type, proxy_url, proxy_port)

        proxy_settings = {
            "http": proxy_uri,
            "https": proxy_uri
        }
        return proxy_settings

    else:
        return None



class UCCTAInputCheckpointer:
    def __init__(self, session_key, logger, input_name) -> None:
        self.session_key = session_key
        self.logger = logger
        self.input_name = input_name

    def get(self):
        try:
            ck = checkpointer.KVStoreCheckpointer(
                self.input_name, self.session_key, ADDON_NAME)
            return ck.get(self.input_name)
        except Exception as exception:
            self.logger.error("Error occurred while fetching checkpoint, error={}".format(exception))

    def update(self, new_val):
        try:
            ck = checkpointer.KVStoreCheckpointer(
                self.input_name, self.session_key, ADDON_NAME)
            return ck.update(self.input_name, new_val)
        except Exception as exception:
            self.logger.exception("Error occurred while updating the checkpoint, error={}".format(exception))

    def delete(self):
        try:
            ck = checkpointer.KVStoreCheckpointer(
                self.input_name, self.session_key, ADDON_NAME)
            return ck.delete(self.input_name)
        except Exception as exception:
            self.logger.exception("Error occurred while deleting the checkpoint, error={}".format(exception))



class UCCTACustomInputRestHandler(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)

    def handleEdit(self, confInfo):
        AdminExternalHandler.handleEdit(self, confInfo)

    def handleCreate(self, confInfo):
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleRemove(self, confInfo):
        # Deleting the checkpoint to avoid issue when user tries to delete the input but then tries to recreate the input with the same name

        session_key = self.getSessionKey()
        log_level = get_ucc_ta_log_level(session_key)
        input_name = self.callerArgs.id
        if input_name:
            logger = logger_manager.setup_logging(input_name, log_level)

            input_checkpointer = UCCTAInputCheckpointer(self.getSessionKey(), logger, input_name)
            last_checkpoint = input_checkpointer.get()

            if last_checkpoint:
                logger.info(f"Deleting the checkpoint for input={input_name} with last found checkpoint was {last_checkpoint}")
                input_checkpointer.delete()
                logger.info(f"Deleted the input checkpoint for input={input_name}")
            else:
                logger.info(f"No checkpoint present for input={input_name}")

            AdminExternalHandler.handleRemove(self, confInfo)

        else:
            logger = logger_manager.setup_logging("delete_input_error", log_level)
            err_msg = "Unable to find the input name in the handler."
            logger.error(err_msg)
            raise Exception(err_msg)



class UCCTAInput:
    '''
    Attributes accessible as class attributes
        - logger
        - session_key
        - ucc_ta_settings
        - proxy_settings

        - write_event() - keeps changing based on the input being processed
    '''
    def __init__(self, input_script: smi.Script, definition: smi.ValidationDefinition = None) -> None:
        self.input_script = input_script

        if input_script._input_definition:
            self.session_key = input_script._input_definition.metadata["session_key"]
        else:
            self.session_key = definition.metadata["session_key"]

        self.log_level = get_ucc_ta_log_level(self.session_key)
        self.ucc_ta_settings = get_ucc_ta_settings(self.session_key)

        self.logger = logger_manager.setup_logging("generic_input", self.log_level)

        self.proxy_settings = get_proxy_settings(self.session_key)
        if self.proxy_settings:
            self.logger.info("Using proxy settings configured by user.")
        else:
            self.logger.info("No proxy configured.")


    def validate_input(self, definition: smi.ValidationDefinition):
        self.logger.warning("You can override validate_input(input_script: smi.Script, definition: smi.ValidationDefinition) function into the subclass of VJ_UCC_TA_Input to validate the input in UCC built Add-on.")
        return


    def stream_events(self, inputs: smi.InputDefinition, event_writer: smi.EventWriter):
        for input_name, input_details in inputs.inputs.items():
            normalized_input_name = input_name.split("/")[-1]

            logger = logger_manager.setup_logging(normalized_input_name, self.log_level)
            logger.info(f"Logger initiated. Logging level = {self.log_level}")

            try:
                logger.info(f'Modular input "{normalized_input_name}" started.')

                logger.debug(f"input_name={input_name}, input_item={input_details}")

                account_name = input_details.get('account')
                account_details = get_ucc_ta_account_details(self.session_key, account_name)

                input_checkpointer = UCCTAInputCheckpointer(self.session_key, logger, normalized_input_name)

                # Create event writer for this Input
                def write_event(data, timestamp=None, index=None, sourcetype=None, source=None):
                    _index = index if index else input_details.get("index")
                    _sourcetype = sourcetype if sourcetype else input_details.get("sourcetype")
                    _source = source if source else input_details.get("source")

                    if type(data) is dict:
                        data = json.dumps(data)

                    event_writer.write_event(
                        smi.Event(
                            time=timestamp,
                            data=data,
                            index=_index,
                            sourcetype=_sourcetype,
                            source=_source
                        )
                    )
                self.write_event = write_event
                # write_event function will be re-created for every input
                # so it has all the necessary parameters, so user don't have to pass the parameters

                self.collect(input_name, normalized_input_name, input_details, account_details, input_checkpointer, event_writer)
                logger.info(f'Modular input "{normalized_input_name}" ended.')

            except Exception as e:
                logger.error(
                    f'Exception raised while ingesting data for input="{normalized_input_name}" {e}. Traceback: {traceback.format_exc()}'
                )


    def collect(self, input_name, normalized_input_name, input_details, account_details, checkpointer: UCCTAInputCheckpointer, ew: smi.EventWriter):
        self.logger.error("This collect() function should not be called.")
        raise Exception("collect method has not been implemented.")
