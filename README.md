# OPP_ENV_GUI

OPP_ENV_GUI is a graphical user interface for the opp_env command line tool. 
It provides an easy-to-use interface for installing OMNeT++, INET, and other tools with compatible versions.

## Features

- Automatically populates dropdown menus with available versions from opp_env.
- Updates compatible versions in other dropdowns based on the selected version in one dropdown.
- Allows selection of installation directory.
- Executes opp_env install command with selected options.
- Supports "NONE" option for INET and Other Tools.
- Handles different output formats from the opp_env command.
- Includes error handling and logging for troubleshooting.
- Provides warning messages if trying to install without all necessary selections.
- Use the Reset button to go back to the beginning of the selection process, and have access to all
  possible dropdown options.

## Prerequisites

- Python 3.6 or higher
- opp_env command line tool installed and accessible from the system PATH

## Installation

1. Clone this repository or download the source code.

2. No additional Python packages are required as the application uses Tkinter, which is included in Python's standard library.

## Usage

1. Run the application:

```
python opp_env_gui.py
```

2. Select the versions of OMNeT++, INET, and other tools you want to install from the dropdown menus.
   - OMNeT++ version is required.
   - INET version and Other Tools can be set to "NONE" if not needed.
   - If the user chooses smething from the Other Tools dropdown, the other options will be adjusted automatically, as needed.
     While the most recent release of the requirements will be selected automatically, any still valid options may be selected manually.

3. Choose an installation directory by clicking the "Browse" button.

4. Click the "INSTALL SELECTED" button to start the installation process. The button is always enabled, but the application will show warning messages if:
   - No installation directory is selected.
   - No OMNeT++ version is selected.

## Troubleshooting

If you encounter any issues:

1. Ensure that opp_env is properly installed and accessible from the command line.
2. Check that you have the necessary permissions to install in the selected directory.
3. Review the error messages displayed by the application for more information.
4. Check the debug logs, which are printed to the console, for more detailed information about the application's operation and any errors encountered.

## Debug Logging

The application includes debug logging to help diagnose issues. To view the debug logs:

1. Run the application from a terminal or command prompt.
2. The debug logs will be printed to the console, providing detailed information about the application's operation, including the raw output from opp_env commands and any errors encountered.

## Contributing

Contributions to improve OPP_ENV_GUI are welcome. Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is open source and available under the [MIT License](LICENSE).
