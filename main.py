import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import logging
import os
import sys
import threading
import queue
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

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
        self.last_click_time = 0
        self.click_cooldown = 0.5  # 500ms cooldown between clicks
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
                        combo.set(values[0])
                elif task[0] == "enable_install_button":
                    self.install_button['state'] = tk.NORMAL
                    self.install_button.config(bg='green', fg='white')
                elif task[0] == "disable_install_button":
                    self.install_button['state'] = tk.DISABLED
                    self.install_button.config(bg='gray', fg='white')
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.update_gui)  # Schedule next update

    def browse_directory(self):
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            logging.info("Click ignored due to cooldown")
            return
        self.last_click_time = current_time

        dir_path = filedialog.askdirectory()
        if dir_path:
            self.install_dir = dir_path
            self.dir_label.config(text=f"Install Directory: {dir_path}")
            self.check_install_button()

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
                versions = parts[1:]
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
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            logging.info("Click ignored due to cooldown")
            return
        self.last_click_time = current_time

        sender = event.widget
        threading.Thread(target=self.update_compatibility, args=(sender,), daemon=True).start()

    def update_compatibility(self, sender):
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
        
        self.queue.put(("update_combo", self.inet_combo, ["NONE"] + compatible_options['inet']))
        self.queue.put(("update_combo", self.other_tools_combo, ["NONE"] + compatible_options['other_tools']))

    def update_omnetpp_and_other_tools(self):
        inet_version = self.inet_combo.get()
        if inet_version == "NONE":
            self.populate_dropdowns()
            return
        
        compatible_options = self.get_compatible_options(inet_version)
        
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
                    tool_info = line.split(':')
                    tool = tool_info[0].strip('- ')
                    versions = tool_info[1].strip().split(' / ')
                    for version in versions:
                        other_tools.append(f"{tool}-{version}")
            
            return {
                'omnetpp': omnetpp_versions,
                'inet': inet_versions,
                'other_tools': other_tools
            }
        except Exception as e:
            logging.exception(f"Error getting compatible options for {selected_option}")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Error getting compatible options: {e}"))
            return {'omnetpp': [], 'inet': [], 'other_tools': []}

    def check_install_button(self):
        omnetpp_selected = self.omnetpp_combo.get() != ""
        inet_valid = self.inet_combo.get() in self.inet_combo['values']
        other_tools_valid = self.other_tools_combo.get() in self.other_tools_combo['values']
        
        if omnetpp_selected and inet_valid and other_tools_valid and self.install_dir:
            self.queue.put(("enable_install_button",))
        else:
            self.queue.put(("disable_install_button",))

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

    def install_selected(self):
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            logging.info("Click ignored due to cooldown")
            return
        self.last_click_time = current_time

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
                self.master.after(0, lambda: messagebox.showinfo("Success", "Installation completed successfully!"))
            else:
                self.master.after(0, lambda: messagebox.showerror("Error", "Installation failed. Check the console output for details."))
        except Exception as e:
            logging.exception("Error during installation")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Error during installation: {e}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = OppEnvGUI(root)
    root.mainloop()
