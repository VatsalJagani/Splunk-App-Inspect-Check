# splunk-app-action
* Github Action to automatically generate Splunk App and Add-on builds, run app-inspect checks (with the App-Inspect/Splunkbase API) on commit/push etc on GitHub repo. It also performs Splunk cloud checks.
* It also has capability to generate build based on UCC Generator (`ucc-gen`) function [Splunk Add-on UCC Framework](https://splunk.github.io/addonfactory-ucc-generator/) for Add-ons.
* It has some common utilities needed for Splunk Apps and Add-ons.
* It also works in Private Repositories on GitHub.



## Flow Diagram (What does this GitHub action do?)

```mermaid
graph TD
  A[Start] --> B([Push to GitHub])
  B --> C>Action Triggered]

  C --> D{Use UCC Gen?}
  D --> |Yes| E([ucc-gen build])
  E --> F([Optionally: Run User Defined Commands])

  D --> |No| F
  F --> G([Generate build with tar command])

  G --> H([App Inspect Check])
  H --> |Yes| I(Build Successful)
  H --> |No| J(Build Failed - App-Inspect Errors)

  I --> K{Is Add App Utilities?}
  J --> K

  K --> |Yes| L([Adding App Utilities])
  L --> M{Any changes to code?}
  M --> |Yes| N([Pull Request Created])
  M --> |No| O([Build Artifacts Created])
  N --> O

  K --> |No| O
```



## Capabilities & Usage

* You can get more information about GitHub workflow files [here](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions). As this document will not go in detail about it.


### Generate Splunk App/Add-on Build artifact
* The action automatically generates build artifact from GitHub repo.

```
- uses: VatsalJagani/splunk-app-action@v4
  with:
    app_dir: "my_app"
```
    * Here even app_dir is optional parameter if you want to generate the build.
    * See details about the inputs options under the `Inputs` section.


* Supports multiple Apps/Add-ons in single repository.
    ```
    - uses: VatsalJagani/splunk-app-action@v4
      with:
        app_dir: "my_splunk_app"

    - uses: VatsalJagani/splunk-app-action@v4
      with:
        app_dir: "my_splunk_add-on"
    ```

* Supports Add-on build with **UCC Add-on Generator**
    * With `ucc-gen build` command.
    * Reference - [https://splunk.github.io/addonfactory-ucc-generator/](https://splunk.github.io/addonfactory-ucc-generator/)
    * The `app_dir` folder must have a sub-folder named `package`, and a file named `globalConfig.json` for this to work.
    * You need to use `ucc-gen init` command locally first to initial the Add-on/Repository before using this or `ucc-gen build` command. See [documentation of UCC Framework](https://splunk.github.io/addonfactory-ucc-generator/quickstart/).
    ```
    - uses: VatsalJagani/splunk-app-action@3
      with:
        app_dir: "TA_my_addon"
        use_ucc_gen: true
    ```

* **NOTE* - <ins>If you have executable files in your App other than `.sh` then explicitly add `to_make_permission_changes: false` for splunk-app-action earlier than `v4`. From version `v4` the default value has been changed to `false` so you don't have to explicitly add but do not enable it. Otherwise you lose the executable permissions on those executable files.</ins>


* #### Avoid File and Folder Permission Issue on Your App Build
    * **NOTE** - This might break your App.
        * Avoid this parameter if your App has executable files other than `.sh` and `.exe`.
        * Alternatively you can use `Running User Defined Commands Before Generating the final App Build` section here to see how you can assign right permission for your App/Add-on.
    * You can add `to_make_permission_changes: true` parameter to fix the issues with file and folder permissions to avoid App-inspect check automatically.
        ```
        - uses: VatsalJagani/splunk-app-action4
          with:
            app_dir: "my_app"
            to_make_permission_changes: true
            splunkbase_username: ${{ secrets.SPLUNKBASE_USERNAME }}
            splunkbase_password: ${{ secrets.SPLUNKBASE_PASSWORD }}
        ```
    * We will run below commands to avoid App inspect checks related to file and folder permissions.
        ```
        find my_app -type f -exec chmod 644 '{}' \;
        find my_app -type f -name '*.sh' -exec chmod 755 '{}' \;
           ... we run the same command for following other file extensions: .exe, .bat, .msi, .cmd
           ... Keep note that Linux executables are generally without extension, in that case avoid this parameter.
        find my_app -type d -exec chmod 755 '{}' \;
        ```


* #### Running User Defined Commands Before Generating the final App Build
    * **NOTE** - Read the `Upgrade Guide from v3 to v4` if you are migrating from splunk-app-action version before `v4`.

    * If you wish to run the user defined linux commands before generating the App build, set the environment variables `SPLUNK_APP_ACTION_<n>`.
        ```
        - uses: VatsalJagani/splunk-app-action@v4
          env:
            SPLUNK_APP_ACTION_1: "find . -type f -exec chmod 644 '{}' \\;"
            SPLUNK_APP_ACTION_2: "find . -type f -name '*.sh' -exec chmod +x '{}' \\;"
            SPLUNK_APP_ACTION_3: "find . -type d -exec chmod 755 '{}' \\;"
          with:
            app_dir: "my_app"
        ```
        * Above use-case is very common as if your App/Add-on has shell scripts in bin directory and you want to make sure it has executable permission.
        * Run the command in the context of your App's root directory. (Assume current working directory is your App's root directory.)
        * Maximum 100 commands can be executed. So from `SPLUNK_APP_ACTION_1` to `SPLUNK_APP_ACTION_99`.
        * The command will be executed in incremented order from `SPLUNK_APP_ACTION_1` to `SPLUNK_APP_ACTION_99`.

    * It allows you to run command before building the App build.
        * This could be useful if you wish to remove some files that you don't want in the build, change permission of some files before running the rest of the app build or app-inspect check.
        ```
        - uses: VatsalJagani/splunk-app-action4
          env:
            SPLUNK_APP_ACTION_1: "rm -rf extra_test_folder"
          with:
            app_dir: "my_app"
        ```
        * The above example would remove unwanted tests folder going into the final App build.
        * Run the command in the context of your App's root directory. (Assume current working directory is your App's root directory.)


### Run App-Inspect (with Splunkbase API)
* It runs app-inspect with Splunkbase API.
    * Past Story: I've tried to use CLI version of the App-inspect check, I've also tried to use GitHub action with CLI version from Splunk, but all fails as they are always way behind the Splunkbase API. Hence you end up failing the checks when you try to upload a new version of Splunkbase.
* This is the automation of Splunkbase API or postman version of App-inspect checks.
* Fails the GitHub workflow if there is failure or error in App-inspect check or Cloud checks.

* It will generate the `reports in HTML format` and put it as `GitHub artifact`. You will find them under `Actions` tab in your repository.

* It also performs Splunk Cloud checks and SSAI checks for Splunk Cloud

* It requires to set inputs: splunkbase_username and splunkbase_password.

```
- uses: VatsalJagani/splunk-app-action4
  with:
    app_dir: "my_app"
    splunkbase_username: ${{ secrets.SPLUNKBASE_USERNAME }}
    splunkbase_password: ${{ secrets.SPLUNKBASE_PASSWORD }}
```


### Utilities
* Following are utilities provided by the splunk-app-action.
* Utilities make code changes in your repositories and create PR for you to view and merge if you deem ok.
* In order to do that all utilities require common input called `my_github_token`.


#### `whats_in_the_app` - Utility that adds information about the App inside the README.md file
* The splunk-app-action has utility which automatically adds information about the App, like how many alerts does it have, how many dashboards does it have, etc inside the App's README.md file.
```
- uses: VatsalJagani/splunk-app-action4
  with:
    app_dir: "my_app"
    app_utilities: "whats_in_the_app"
    my_github_token: ${{ secrets.MY_GITHUB_TOKEN }}
```

#### `logger` - Add Python Logger
* Auto adds python logger manager, including python file necessary, props.conf to assign right sourcetype for it under the internal logs.

```
- uses: VatsalJagani/splunk-app-action4
  with:
    app_dir: "my_app"
    app_utilities: "logger"
    my_github_token: ${{ secrets.MY_GITHUB_TOKEN }}
    logger_log_files_prefix: "my_app"
    logger_sourcetype: "my_app:logs"
```

#### `splunk_python_sdk` - Add Splunklib or Splunk SDK for Python and Auto Upgrades It
* This utility adds the splunklib or Splunk SDK for Python to the App and auto upgrades it whenever new version is available.

Example-1
```
- uses: VatsalJagani/splunk-app-action@v4
  with:
    app_dir: "my_app"
    app_utilities: "splunk_python_sdk"
    my_github_token: ${{ secrets.MY_GITHUB_TOKEN }}
```

Example-2
```
- uses: VatsalJagani/splunk-app-action@v4
  with:
    app_dir: "my_app"
    app_utilities: "splunk_python_sdk"
    my_github_token: ${{ secrets.MY_GITHUB_TOKEN }}
    splunk_python_sdk_install_path: "bin/lib"
```


#### `common_js_utilities` - Add Common JavaScript Utilities File
* This utility adds a JavaScript file that contains commonly used functionality for a JavaScript code for a Splunk App.

```
- uses: VatsalJagani/splunk-app-action@v4
  with:
    app_dir: "my_app"
    app_utilities: "common_js_utilities"
    my_github_token: ${{ secrets.MY_GITHUB_TOKEN }}
```

#### `ucc_additional_packaging` - Add additional_packaging.py file for UCC built Add-on
* This utility adds additional_packaging.py file that contains code to better generate input handler python file to easily re-generate code on change, rather than making manual changes.

```
- uses: VatsalJagani/splunk-app-action@v4
  with:
    app_dir: "."
    use_ucc_gen: true
    app_utilities: "ucc_additional_packaging"
    my_github_token: ${{ secrets.MY_GITHUB_TOKEN }}
```

* The input file in which you need to write code is `<Input_Name>_handler.py`. And it would start with below content and you need to copy into your `package/bin` folder and write code into it to collect the data and ingest into Splunk.

```
from splunklib import modularinput as smi


def validate_input(input_script: smi.Script, definition: smi.ValidationDefinition):
    return


def stream_events(input_script: smi.Script, inputs: smi.InputDefinition, event_writer: smi.EventWriter):
    return
```

* Update the content in `validate_input` and `stream_events`.
    * `validate_input` is optional.
    * `stream_events` function is compulsory to collect and ingest the events into Splunk.



## Inputs

#### app_dir
* description: "Provide app directory inside your repository. Do not provide the value if the repo's root directory itself if app directory."
* required: false
* default: ".", meaning root folder of the repository.

#### to_make_permission_changes
* description: "Whether to apply file and folder permission changes according to Splunk App Inspect expectation before generating the build."
* Before you add this parameter, read the instruction from [Avoid File and Folder Permission Issue on Your App Build](#avoid-file-and-folder-permission-issue-on-your-app-build) section.
* required: false
* default: false

#### use_ucc_gen
* description: "Use ucc-gen command to generate the build for Add-on. The 'app_dir' folder must have a sub-folder named 'package', and a file named 'globalConfig.json' for this to work."
* required: false
* default: false

#### is_app_inspect_check
* description: "Whether to perform the Splunk app-inspect checks or not. This would include cloud-inspect checks as well."
* required: false
* default: true

#### splunkbase_username
* description: "Username required to call the Splunkbase API for App-Inspect. Required when is_app_inspect_check is set to true."
* required: false

#### splunkbase_password
* description: "Password required to call the Splunkbase API for App-Inspect. Required when is_app_inspect_check is set to true. Strongly recommend to use via GitHub secrets only and specify like `{{secrets.MY_SPLUNK_PASSWORD}}`."
* required: false

#### app_utilities
* description: "Add comma separated list of utilities to use. You need to enable read and write permission for workflow to create Pull Requests. Valid options: whats_in_the_app, logger, splunk_python_sdk, common_js_utilities, ucc_additional_packaging"
* required: false
* default: "" (meaning no utilities)

#### my_github_token
* description: "GitHub Secret Token to automatically create Pull request. (Make sure to put it in the Repo secret on GitHub as `MY_GITHUB_TOKEN` and then use it like `{{ secrets.MY_GITHUB_TOKEN }}`. Do not write it in plain text.) Only required if app_utilities is being used."
* required: false

#### logger_log_files_prefix
* description: "Log files prefix. Only required for logger utility."
* required: false

#### logger_sourcetype
* description: "Sourcetype for the internal app logs. Required only for logger utility."
* required: false

#### splunk_python_sdk_install_path
* description: "Path where you would like to install splunk-python-sdk (splunklib). Path is relative to App's root folder."
* required: false
* default: "bin"

#### is_remove_pyc_from_splunklib_dir
* description: "Remove `.pyc` files and `__pycache__` directory from splunk-python-sdk (splunklib) installation path before generating Pull Request. Do not turn this off unless you are facing any issues explicitly."
* required: false
* default: true





## Troubleshooting
* You see below error on GitHub workflow with action.

    ```
    Unable to push changes into the branch=splunk_app_action_bbe00a4a32a796cc84b73b09abc09922
    ```

    * Enable GitHub workflow to create pull request.
    * Go to your Repo `Setting` > `Actions` > `General`.
        * ![Workflow Permission 1](/images/workflow_permission_for_pr_1.png)
    * Enable read and write permission under `Workflow permissions`.
        * ![Workflow Permission 2](/images/workflow_permission_for_pr_2.png)


## See Examples Here
* [Splunk Apps and Add-ons Dependents on Splunk App Action](https://github.com/VatsalJagani/splunk-app-action/network/dependents)


## Release Notes

### v4.1
* Added `splunk_python_sdk_install_path` parameter for `splunk_python_sdk` utility. Default value is still `bin` folder, but now user can change based on their needs.
* Avoid `.pyc` files and `__pycache__` files getting into `splunk_python_sdk` installation folder and getting into Pull Request by default. You can turn this off with `is_remove_pyc_from_splunklib_dir` parameter.


### v4
* Run the user-defined commands in the context of your App's root directory instead of Repo's root directory. Refer to `Running User Defined Commands Before Generating the final App Build` for more details.

* `to_make_permission_changes` parameter's default value has been changed to `false`. Refer to `Avoid File and Folder Permission Issue on Your App Build` for more details.
    * Automatic file permission changes now also add executable permissions to following file extensions, `.msi`, `.exe`, `.cmd`, `.bat`, along with `.sh`.

* The input parameters `is_generate_build` and `app_build_path` has been removed.


### Upgrade Guide from v3 to v4
* From `v4` of the `splunk-app-action`, your user-defined custom command (Refer to `Running User Defined Commands Before Generating the final App Build` section) would run in a context of your App's folder instead of root folder.
    * So you need to change the code from this:
        ```
        - uses: VatsalJagani/splunk-app-action@v4
          env:
            SPLUNK_APP_ACTION_1: "rm -rf my_app/extra_test_folder"
            SPLUNK_APP_ACTION_2: "cat 'abc,123' >> my_app/lookups/my_custom_lookup.csv"
          with:
            app_dir: "my_app"
        ```
        * to
        ```
        - uses: VatsalJagani/splunk-app-action4
          env:
            SPLUNK_APP_ACTION_1: "rm -rf extra_test_folder"
            SPLUNK_APP_ACTION_2: "cat 'abc,123' >> lookups/my_custom_lookup.csv"
          with:
            app_dir: "my_app"
        ```
        * because this command would now run in context of your App's directory.

* `to_make_permission_changes` - default value has been changed to `false` from `true`. This means if you were to apply file and folder permission changes automatically, you have to explicitly add this parameter to your workflow. Refer to `Avoid File and Folder Permission Issue on Your App Build` for more details.

* The input parameters `is_generate_build` and `app_build_path` has been removed from GitHub action from `v4` onwards, hence if you are using them then migrate the action config properly before version update.


### v3
* use_ucc_gen parameter added to support UCC build Add-on support. (It uses `ucc-gen build` command to generate the build dynamically on the GitHub action directly.)
* Added new utility `ucc_additional_packaging` for better way to generate proper Python Input handler file structure.
* Better way to Auto detect App package id, App version number and App build number.
* Better naming convention for App and Add-on build names.
* Run App utilities on current branch instead of on default branch for better support and easier to deal with in codebase.
* Automatically delete unwanted files from the build to avoid App inspect check issues.


### v2
* Fix Splunk App Inspect Failure due to file permission issue. The App/Add-on build process automatically fixes that.
* App utilities added: `whats_in_the_app` (information to be added to README file about no. of alerts, dashboards, etc), `logger` (Python logger file and props.conf configs for the internal logs), `splunk_python_sdk` (Automatically upgrade Splunklib Python SDK), `common_js_utilities` (Common JS utilities file)


### v1
* GitHub App action created for Splunk Apps.
* It can generate App and Add-ons's Builds.
* It can automatically run Splunk App Inspect.


## Contribute
* If you are developer and want to contribute to this project, please submit a Pull Request.
* If you find a bug or have a request for enhancement, create a Github Issue in this project.
* If you wish to share Feedback or success story, please add comment in [this issue](https://github.com/VatsalJagani/splunk-app-action/issues/19).
