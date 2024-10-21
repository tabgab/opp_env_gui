# OPP_ENV_GUI

OPP_ENV_GUI is a graphical user interface for the opp_env command line tool. It provides an easy-to-use interface for installing OMNeT++, INET, and other tools with compatible versions.

## Features

- Automatically populates dropdown menus with available versions from opp_env.
- Updates compatible versions in other dropdowns based on the selected version in one dropdown.
- Provides visual feedback on compatibility and installation status.
- Allows selection of installation directory.
- Executes opp_env install command with selected options.
- Supports "NONE" option for INET and Other Tools.
- Handles different output formats from the opp_env command.
- Includes error handling and logging for troubleshooting.

## Prerequisites

- Python 3.6 or higher
- opp_env command line tool installed and accessible from the system PATH

## Installation

1. Clone this repository or download the source code.

2. No additional Python packages are required as the application uses Tkinter, which is included in Python's standard library.

## Usage

1. Run the application:

```
python main.py
```

2. Select the versions of OMNeT++, INET, and other tools you want to install from the dropdown menus.
   - OMNeT++ version is required and defaults to the latest version.
   - INET version and Other Tools can be set to "NONE" if not needed.

3. Choose an installation directory by clicking the "Browse" button.

4. Click the "INSTALL SELECTED" button to start the installation process. The button will be enabled only when all selections are valid and an installation directory is specified.

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
