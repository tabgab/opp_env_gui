import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import logging
import os
import sys
import threading

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class OppEnvGUI:
    def __init__(self, master):
        self.master = master
        master.title("OPP_ENV_GUI")
        master.geometry("600x400")

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

        # Install button
        self.install_button = tk.Button(master, text="INSTALL SELECTED", command=self.install_selected, state=tk.DISABLED)
        self.install_button.pack(pady=10)

        self.install_dir = ""
        self.populate_dropdowns()

        # Bind events
        self.omnetpp_combo.bind("<<ComboboxSelected>>", self.update_compatibility)
        self.inet_combo.bind("<<ComboboxSelected>>", self.update_compatibility)
        self.other_tools_combo.bind("<<ComboboxSelected>>", self.update_compatibility)

    def browse_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.install_dir = dir_path
            self.dir_label.config(text=f"Install Directory: {dir_path}")
            self.check_install_button()

    def populate_dropdowns(self):
        options = self.get_opp_env_options()
        
        # Populate OMNeT++ versions
        self.omnetpp_combo['values'] = options['omnetpp']
        if options['omnetpp']:
            self.omnetpp_combo.set(options['omnetpp'][0])
        
        # Populate INET versions
        self.inet_combo['values'] = ["NONE"] + options['inet']
        self.inet_combo.set("NONE")
        
        # Populate other tools
        self.other_tools_combo['values'] = ["NONE"] + options['other_tools']
        self.other_tools_combo.set("NONE")

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
                versions = parts[1:]
                if tool == 'omnetpp':
                    omnetpp_versions = versions
                elif tool == 'inet':
                    inet_versions = versions
                else:
                    other_tools.append(tool)
            
            logging.info(f"Categorized versions: omnetpp={omnetpp_versions}, inet={inet_versions}, other={other_tools}")
            
            return {
                'omnetpp': omnetpp_versions,
                'inet': inet_versions,
                'other_tools': other_tools
            }
        except Exception as e:
            logging.exception("Error in get_opp_env_options")
            messagebox.showerror("Error", f"Error getting opp_env options: {e}")
            return {'omnetpp': [], 'inet': [], 'other_tools': []}

    def update_compatibility(self, event):
        sender = event.widget
        if sender == self.omnetpp_combo:
            self.update_inet_and_other_tools()
        elif sender == self.inet_combo:
            self.update_omnetpp_and_other_tools()
        else:  # other_tools_combo
            self.update_omnetpp_and_inet()
        
        self.check_install_button()

    def update_inet_and_other_tools(self):
        omnetpp_version = self.omnetpp_combo.get()
        compatible_options = self.get_compatible_options(omnetpp_version)
        
        self.update_combo_items(self.inet_combo, compatible_options['inet'])
        self.update_combo_items(self.other_tools_combo, compatible_options['other_tools'])

    def update_omnetpp_and_other_tools(self):
        inet_version = self.inet_combo.get()
        if inet_version == "NONE":
            self.populate_dropdowns()
            return
        
        compatible_options = self.get_compatible_options(inet_version)
        
        self.update_combo_items(self.omnetpp_combo, compatible_options['omnetpp'])
        self.update_combo_items(self.other_tools_combo, compatible_options['other_tools'])

    def update_omnetpp_and_inet(self):
        other_tool = self.other_tools_combo.get()
        if other_tool == "NONE":
            self.populate_dropdowns()
            return
        
        compatible_options = self.get_compatible_options(other_tool)
        
        self.update_combo_items(self.omnetpp_combo, compatible_options['omnetpp'])
        self.update_combo_items(self.inet_combo, compatible_options['inet'])

    def get_compatible_options(self, selected_option):
        try:
            result = subprocess.run(['opp_env', 'info', selected_option], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            omnetpp_versions = []
            inet_versions = []
            other_tools = []
            
            for line in lines:
                if line.startswith('- omnetpp:'):
                    omnetpp_versions = line.split(':')[1].strip().split(' / ')
                elif line.startswith('- inet:'):
                    inet_versions = line.split(':')[1].strip().split(' / ')
                elif line.startswith('- '):
                    other_tools.append(line.split(':')[0].strip('- '))
            
            return {
                'omnetpp': omnetpp_versions,
                'inet': inet_versions,
                'other_tools': other_tools
            }
        except Exception as e:
            logging.exception(f"Error getting compatible options for {selected_option}")
            messagebox.showerror("Error", f"Error getting compatible options: {e}")
            return {'omnetpp': [], 'inet': [], 'other_tools': []}

    def update_combo_items(self, combo, items):
        current_value = combo.get()
        combo['values'] = ["NONE"] + items if combo != self.omnetpp_combo else items
        
        if current_value in combo['values']:
            combo.set(current_value)
        elif combo == self.omnetpp_combo and items:
            combo.set(items[0])
        else:
            combo.set("NONE")

    def check_install_button(self):
        omnetpp_selected = self.omnetpp_combo.get() != ""
        inet_valid = self.inet_combo.get() in self.inet_combo['values']
        other_tools_valid = self.other_tools_combo.get() in self.other_tools_combo['values']
        
        if omnetpp_selected and inet_valid and other_tools_valid and self.install_dir:
            self.install_button['state'] = tk.NORMAL
            self.install_button.config(bg='green', fg='white')
        else:
            self.install_button['state'] = tk.DISABLED
            self.install_button.config(bg='gray', fg='white')

    def change_directory(self):
        if not self.install_dir:
            messagebox.showwarning("Warning", "No installation directory specified. Please select a directory.")
            return False
        try:
            os.chdir(self.install_dir)
            logging.info(f"Changed directory to: {self.install_dir}")
            return True
        except Exception as e:
            logging.exception(f"Error changing directory to {self.install_dir}")
            messagebox.showerror("Error", f"Failed to change directory: {e}")
            return False

    def update_console(self, process):
        for line in iter(process.stdout.readline, ''):
            sys.stdout.write(line)
            sys.stdout.flush()

    def install_selected(self):
        if not self.change_directory():
            return

        omnetpp_version = f"omnetpp-{self.omnetpp_combo.get()}"
        inet_version = self.inet_combo.get()
        other_tool = self.other_tools_combo.get()

        command = ['opp_env', 'install', omnetpp_version]
        
        if inet_version != "NONE":
            command.append(inet_version)
        
        if other_tool != "NONE":
            command.append(other_tool)

        logging.info(f"Executing command: {' '.join(command)}")

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            
            threading.Thread(target=self.update_console, args=(process,), daemon=True).start()
            
            return_code = process.wait()
            
            if return_code == 0:
                messagebox.showinfo("Success", "Installation completed successfully!")
            else:
                messagebox.showerror("Error", "Installation failed. Check the console output for details.")
        except Exception as e:
            logging.exception("Error during installation")
            messagebox.showerror("Error", f"Error during installation: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OppEnvGUI(root)
    root.mainloop()
