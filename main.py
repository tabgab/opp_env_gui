import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import logging
import os
import sys
import threading
import queue
import re
import webbrowser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def check_opp_env():
    try:
        subprocess.run(['opp_env', '--version'], capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def show_opp_env_error():
    error_window = tk.Tk()
    error_window.title("Error: opp_env not found")
    error_window.geometry("400x150")

    message = "Could not find opp_env, this tool needs opp_env to be installed on your system to function."
    tk.Label(error_window, text=message, wraplength=350, justify="center").pack(pady=20)

    def exit_program():
        error_window.destroy()
        sys.exit()

    def visit_github():
        webbrowser.open("https://github.com/omnetpp/opp_env")
        exit_program()

    button_frame = tk.Frame(error_window)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Exit", command=exit_program).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="Visit opp_env Github Page", command=visit_github).pack(side=tk.LEFT, padx=10)

    error_window.mainloop()

class OppEnvGUI:
    def __init__(self, master):
        self.master = master
        master.title("OPP_ENV_GUI")
        master.geometry("600x450")

        # OMNeT++ version dropdown
        ttk.Label(master, text="OMNeT++ Version:").pack(pady=5)
        self.omnetpp_combo = ttk.Combobox(master, state="readonly")
        self.omnetpp_combo.pack(pady=5)

        # INET version dropdown
        ttk.Label(master, text="INET Version:").pack(pady=5)
        self.inet_combo = ttk.Combobox(master, state="readonly")
        self.inet_combo.pack(pady=5)

        # Other tools dropdown
        ttk.Label(master, text="Other Tools:").pack(pady=5)
        self.other_tools_combo = ttk.Combobox(master, state="readonly")
        self.other_tools_combo.pack(pady=5)

        # Install directory selection
        self.dir_frame = ttk.Frame(master)
        self.dir_frame.pack(pady=10)
        self.dir_label = ttk.Label(self.dir_frame, text="Install Directory:")
        self.dir_label.pack(side=tk.LEFT)
        self.dir_button = ttk.Button(self.dir_frame, text="Browse", command=self.browse_directory)
        self.dir_button.pack(side=tk.LEFT)

        # Button frame
        self.button_frame = ttk.Frame(master)
        self.button_frame.pack(pady=10)

        # Install button
        self.install_button = tk.Button(self.button_frame, text="INSTALL SELECTED", command=self.install_selected, state=tk.NORMAL)
        self.install_button.pack(side=tk.LEFT, padx=5)

        # Reset button
        self.reset_button = tk.Button(self.button_frame, text="RESET", command=self.reset_dropdowns)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.install_dir = ""
        self.queue = queue.Queue()

        # Bind events
        self.omnetpp_combo.bind("<<ComboboxSelected>>", self.handle_combo_selection)
        self.inet_combo.bind("<<ComboboxSelected>>", self.handle_combo_selection)
        self.other_tools_combo.bind("<<ComboboxSelected>>", self.handle_combo_selection)

        # Start periodic GUI update
        self.update_gui()

        # Populate dropdowns in a separate thread
        threading.Thread(target=self.populate_dropdowns, daemon=True).start()

    def update_gui(self):
        try:
            while not self.queue.empty():
                task = self.queue.get_nowait()
                if task[0] == "update_combo":
                    combo, values = task[1], task[2]
                    combo['values'] = values
                    if values:
                        if combo == self.omnetpp_combo:
                            combo.set(self.get_latest_version(values))
                        else:
                            combo.set("NONE")
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.update_gui)  # Schedule next update

    def get_latest_version(self, versions):
        def version_key(v):
            parts = re.findall(r'\d+', v)
            return tuple(map(int, parts)) if parts else (-1,)

        return max(versions, key=version_key)

    def browse_directory(self):
        logging.info("Browse directory button clicked")
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.install_dir = dir_path
            self.dir_label.config(text=f"Install Directory: {dir_path}")

    def populate_dropdowns(self):
        options = self.get_opp_env_options()
        
        self.queue.put(("update_combo", self.omnetpp_combo, options['omnetpp']))
        self.queue.put(("update_combo", self.inet_combo, ["NONE"] + options['inet']))
        self.queue.put(("update_combo", self.other_tools_combo, ["NONE"] + options['other_tools']))

    def get_opp_env_options(self):
        try:
            logging.info("Executing 'opp_env list' command")
            result = subprocess.run(['opp_env', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error executing 'opp_env list': {result.stderr}")
                raise Exception(f"Error executing 'opp_env list': {result.stderr}")
            
            logging.info(f"Raw output from opp_env list: {result.stdout}")
            
            lines = result.stdout.strip().split('\n')
            
            omnetpp_versions = []
            inet_versions = []
            other_tools = []

            for line in lines:
                parts = line.split()
                if len(parts) < 2:
                    continue
                tool = parts[0]
                versions = [v for v in parts[1:] if v != 'git']
                if tool == 'omnetpp':
                    omnetpp_versions = versions
                elif tool == 'inet':
                    inet_versions = versions
                else:
                    for version in versions:
                        other_tools.append(f"{tool}-{version}")
            
            logging.info(f"Categorized versions: omnetpp={omnetpp_versions}, inet={inet_versions}, other={other_tools}")
            
            return {
                'omnetpp': omnetpp_versions,
                'inet': inet_versions,
                'other_tools': other_tools
            }
        except Exception as e:
            logging.exception("Error in get_opp_env_options")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Error getting opp_env options: {e}"))
            return {'omnetpp': [], 'inet': [], 'other_tools': []}

    def handle_combo_selection(self, event):
        logging.info(f"Combo selection changed: {event.widget}")
        self.update_compatibility(event.widget)

    def update_compatibility(self, sender):
        if sender == self.omnetpp_combo:
            self.update_inet_and_other_tools()
        elif sender == self.inet_combo:
            self.update_omnetpp_and_other_tools()
        else:  # other_tools_combo
            self.update_omnetpp_and_inet()

    def update_inet_and_other_tools(self):
        omnetpp_version = f"omnetpp-{self.omnetpp_combo.get()}"
        compatible_options = self.get_compatible_options(omnetpp_version)
        
        self.queue.put(("update_combo", self.inet_combo, ["NONE"] + compatible_options['inet']))
        self.queue.put(("update_combo", self.other_tools_combo, ["NONE"] + compatible_options['other_tools']))

    def update_omnetpp_and_other_tools(self):
        inet_version = self.inet_combo.get()
        if inet_version == "NONE":
            self.populate_dropdowns()
            return
        
        compatible_options = self.get_compatible_options(f"inet-{inet_version}")
        
        self.queue.put(("update_combo", self.omnetpp_combo, compatible_options['omnetpp']))
        self.queue.put(("update_combo", self.other_tools_combo, ["NONE"] + compatible_options['other_tools']))

    def update_omnetpp_and_inet(self):
        other_tool = self.other_tools_combo.get()
        if other_tool == "NONE":
            self.populate_dropdowns()
            return
        
        compatible_options = self.get_compatible_options(other_tool)
        
        self.queue.put(("update_combo", self.omnetpp_combo, compatible_options['omnetpp']))
        self.queue.put(("update_combo", self.inet_combo, ["NONE"] + compatible_options['inet']))

    def get_compatible_options(self, selected_option):
        try:
            result = subprocess.run(['opp_env', 'info', selected_option], capture_output=True, text=True)
            print(f"Output of 'opp_env info {selected_option}':")
            print(result.stdout)
            sys.stdout.flush()

            lines = result.stdout.split('\n')
            
            omnetpp_versions = []
            inet_versions = []
            other_tools = []
            
            requires_section = False
            for line in lines:
                if line.startswith("Requires:"):
                    requires_section = True
                    continue
                if requires_section:
                    if line.startswith("- omnetpp:"):
                        omnetpp_versions = [v for v in line.split(':')[1].strip().split(' / ') if v != 'git']
                    elif line.startswith("- inet:"):
                        inet_versions = [v for v in line.split(':')[1].strip().split(' / ') if v != 'git']
                    elif line.startswith("- "):
                        tool_info = line.split(':')
                        tool = tool_info[0].strip('- ')
                        versions = [v for v in tool_info[1].strip().split(' / ') if v != 'git']
                        for version in versions:
                            other_tools.append(f"{tool}-{version}")
                    else:
                        break  # End of Requires section
            
            return {
                'omnetpp': omnetpp_versions,
                'inet': inet_versions,
                'other_tools': other_tools
            }
        except Exception as e:
            logging.exception(f"Error getting compatible options for {selected_option}")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Error getting compatible options: {e}"))
            return {'omnetpp': [], 'inet': [], 'other_tools': []}

    def change_directory(self):
        if not self.install_dir:
            self.master.after(0, lambda: messagebox.showwarning("Warning", "No installation directory specified. Please select a directory."))
            return False
        try:
            os.chdir(self.install_dir)
            logging.info(f"Changed directory to: {self.install_dir}")
            return True
        except Exception as e:
            logging.exception(f"Error changing directory to {self.install_dir}")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Failed to change directory: {e}"))
            return False

    def update_console(self, process):
        for line in iter(process.stdout.readline, ''):
            sys.stdout.write(line)
            sys.stdout.flush()

    def initialize_opp_env(self):
        logging.info("Initializing opp_env")
        try:
            result = subprocess.run(['opp_env', 'init'], capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error executing 'opp_env init': {result.stderr}")
                raise Exception(f"Error executing 'opp_env init': {result.stderr}")
            logging.info("opp_env initialized successfully")
            return True
        except Exception as e:
            logging.exception("Error during opp_env initialization")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Error during opp_env initialization: {e}"))
            return False

    def install_selected(self):
        logging.info("Install button clicked")
        if not self.install_dir:
            messagebox.showwarning("Warning", "Please select an installation directory.")
            return

        omnetpp_version = self.omnetpp_combo.get()
        if not omnetpp_version:
            messagebox.showwarning("Warning", "Please select an OMNeT++ version.")
            return

        if not self.change_directory():
            return

        if not self.initialize_opp_env():
            return

        command = ['opp_env', 'install', f"omnetpp-{omnetpp_version}"]
        
        inet_version = self.inet_combo.get()
        if inet_version != "NONE":
            command.append(f"inet-{inet_version}")
        
        other_tool = self.other_tools_combo.get()
        if other_tool != "NONE":
            command.append(other_tool)

        logging.info(f"Executing command: {' '.join(command)}")

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            
            threading.Thread(target=self.update_console, args=(process,), daemon=True).start()
            
            return_code = process.wait()
            
            if return_code == 0:
                self.master.after(0, lambda: messagebox.showinfo("Success", "Installation completed successfully!"))
            else:
                self.master.after(0, lambda: messagebox.showerror("Error", "Installation failed. Check the console output for details."))
        except Exception as e:
            logging.exception("Error during installation")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Error during installation: {e}"))

    def reset_dropdowns(self):
        logging.info("Reset button clicked")
        self.populate_dropdowns()
        self.install_dir = ""
        self.dir_label.config(text="Install Directory:")

if __name__ == "__main__":
    if not check_opp_env():
        show_opp_env_error()
    else:
        root = tk.Tk()
        app = OppEnvGUI(root)
        root.mainloop()
