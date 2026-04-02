import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
from datetime import datetime

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

class AnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Directory Size Analyzer")
        self.root.geometry("950x650")
        
        self.items = []
        self.filtered_items = []
        self.node_map = {}
        
        self.current_sort_col = "Size"
        self.sort_descending = True
        self.is_dark = False
        
        # Tkinter variables
        self.path_var = tk.StringVar()
        self.filter_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready. Select a directory to begin.")
        
        self.setup_ui()
        self.apply_theme("light")
        
    def setup_ui(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Main structure
        self.top_frame = ttk.Frame(self.root, padding=10)
        self.top_frame.pack(fill=tk.X)
        self.top_frame.columnconfigure(1, weight=1)
        
        # Row 0: Directory Selection
        ttk.Label(self.top_frame, text="Directory:").grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.path_entry = ttk.Entry(self.top_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, padx=(0,5), pady=5, sticky=tk.EW)
        
        ttk.Button(self.top_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=2, padx=(0,5), pady=5)
        self.analyze_btn = ttk.Button(self.top_frame, text="Analyze", command=self.start_analysis)
        self.analyze_btn.grid(row=0, column=3, pady=5)
        
        self.theme_btn = ttk.Button(self.top_frame, text="🌙 Dark", width=8, command=self.toggle_theme)
        self.theme_btn.grid(row=0, column=4, padx=(10,0), pady=5)
        
        # Row 1: Search/Filter
        ttk.Label(self.top_frame, text="Filter (Name/Type):").grid(row=1, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.filter_var.trace_add("write", self.on_filter_changed)
        self.filter_entry = ttk.Entry(self.top_frame, textvariable=self.filter_var)
        self.filter_entry.grid(row=1, column=1, columnspan=4, pady=5, sticky=tk.EW)
        
        # Middle Frame (Treeview)
        self.mid_frame = ttk.Frame(self.root, padding="10 0 10 10")
        self.mid_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Action", "Name", "Type", "Size")
        self.tree = ttk.Treeview(self.mid_frame, columns=columns, show="headings")
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<ButtonRelease-1>", self.on_single_click)
        self.tree.bind("<Motion>", self.on_tree_motion)
        self.tree.bind("<Leave>", lambda e: self.status_var.set("Ready."))
        
        self.tree.heading("Action", text="Copy")
        self.tree.heading("Name", text="Name", command=lambda: self.sort_tree("Name"))
        self.tree.heading("Type", text="Type", command=lambda: self.sort_tree("Type"))
        self.tree.heading("Size", text="Size \u25BC", command=lambda: self.sort_tree("Size"))
        
        self.tree.column("Action", width=50, anchor=tk.CENTER)
        self.tree.column("Name", width=450, anchor=tk.W)
        self.tree.column("Type", width=120, anchor=tk.CENTER)
        self.tree.column("Size", width=120, anchor=tk.E)
        
        self.scrollbar = ttk.Scrollbar(self.mid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom Frame (Status and Actions)
        self.bottom_frame = ttk.Frame(self.root, padding=10)
        self.bottom_frame.pack(fill=tk.X)
        
        ttk.Label(self.bottom_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        ttk.Button(self.bottom_frame, text="Export JSON Report", command=self.export_report).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(self.bottom_frame, text="Open Reports Folder", command=self.open_reports_folder).pack(side=tk.RIGHT)
        
    def copy_and_analyze(self, path, is_dir):
        self.root.clipboard_clear()
        self.root.clipboard_append(path)
        self.root.update() # keep clipboard active
        
        if is_dir:
            self.path_var.set(path)
            self.start_analysis()
        else:
            self.status_var.set("File path copied to clipboard!")
            
    def on_single_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1": # Action column
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    item_data = self.node_map.get(item_id)
                    if item_data:
                        self.copy_and_analyze(item_data['FullPath'], item_data['IsDir'])

    def on_tree_motion(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1":
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    item_data = self.node_map.get(item_id)
                    if item_data:
                        if item_data['IsDir']:
                            self.status_var.set("copy this folders path to clipboard and analyse")
                        else:
                            self.status_var.set("copy this files path to clipboard")
                        return
        self.status_var.set("Ready.")

    def toggle_theme(self):
        new_mode = "light" if self.is_dark else "dark"
        self.apply_theme(new_mode)
        
    def apply_theme(self, mode):
        self.is_dark = (mode == "dark")
        if self.is_dark:
            bg_col = "#2b2b2b"
            fg_col = "#ffffff"
            entry_bg = "#3b3b3b"
            tree_bg = "#333333"
            select_bg = "#005a9e"
            btn_bg = "#555555"
            btn_active = "#666666"
            self.theme_btn.config(text="☀️Light")
        else:
            bg_col = "#f0f0f0"
            fg_col = "#000000"
            entry_bg = "#ffffff"
            tree_bg = "#ffffff"
            select_bg = "#0078d7"
            btn_bg = "#e1e1e1"
            btn_active = "#d1d1d1"
            self.theme_btn.config(text="🌙 Dark")
            
        self.root.configure(bg=bg_col)
        
        self.style.configure(".", background=bg_col, foreground=fg_col, fieldbackground=entry_bg)
        self.style.configure("TButton", background=btn_bg, foreground=fg_col)
        self.style.map("TButton", background=[("active", btn_active)])
        
        self.style.configure("Treeview", background=tree_bg, foreground=fg_col, fieldbackground=tree_bg)
        self.style.configure("Treeview.Heading", background=btn_bg, foreground=fg_col)
        self.style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", "#ffffff")])
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
            
    def start_analysis(self):
        folder = self.path_var.get().strip().strip('"').strip("'")
        if not folder or not os.path.exists(folder) or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please enter a valid directory path.")
            return
            
        self.analyze_btn.config(state=tk.DISABLED)
        self.status_var.set("Analyzing... please wait")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.items = []
        self.filtered_items = []
        self.node_map = {}
        
        threading.Thread(target=self.analyze_directory, args=(folder,), daemon=True).start()
        
    def analyze_directory(self, target_path):
        try:
            dir_contents = os.listdir(target_path)
        except PermissionError:
            self.root.after(0, self.finish_analysis, f"Error: Permission denied for {target_path}")
            return
            
        total_items = len(dir_contents)
        for i, item in enumerate(dir_contents):
            # Display current item name in the status bar
            display_item = item if len(item) < 50 else item[:47] + "..."
            self.root.after(0, self.status_var.set, f"Analyzing {i+1}/{total_items}: {display_item}")
                
            item_path = os.path.join(target_path, item)
            size = 0
            is_dir = os.path.isdir(item_path)
            if is_dir:
                for dirpath, _, filenames in os.walk(item_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            try:
                                size += os.path.getsize(fp)
                            except OSError:
                                pass
            else:
                try:
                    size += os.path.getsize(item_path)
                except OSError:
                    pass
                    
            ext = os.path.splitext(item)[1].lower() if not is_dir else 'Folder'
            if not ext and not is_dir:
                ext = 'File'
                
            self.items.append({
                'Name': item,
                'Type': ext,
                'SizeBytes': size,
                'FormattedSize': format_size(size),
                'FullPath': item_path,
                'IsDir': is_dir
            })
            
        self.filter_var.set("")
        self.filtered_items = list(self.items)
        self.sort_data()
        
        self.root.after(0, self.populate_tree)
        self.root.after(0, self.finish_analysis, f"Analysis complete. Found {len(self.items)} items.")
        
    def on_filter_changed(self, *args):
        query = self.filter_var.get().lower()
        if not query:
            self.filtered_items = list(self.items)
        else:
            self.filtered_items = [
                item for item in self.items 
                if query in item['Name'].lower() or query in item['Type'].lower()
            ]
        self.sort_data()
        self.populate_tree()

    def sort_tree(self, col):
        if col == "Action": return
        if self.current_sort_col == col:
            self.sort_descending = not self.sort_descending
        else:
            self.current_sort_col = col
            self.sort_descending = True if col == "Size" else False
            
        self.sort_data()
        self.populate_tree()
        
        for c in ("Name", "Type", "Size"):
            arrow = ""
            if c == col:
                arrow = " \u25BC" if self.sort_descending else " \u25B2"
            self.tree.heading(c, text=c + arrow)

    def sort_data(self):
        if not self.filtered_items:
            return
            
        col = self.current_sort_col
        if col == "Name":
            self.filtered_items.sort(key=lambda x: x['Name'].lower(), reverse=self.sort_descending)
        elif col == "Type":
            self.filtered_items.sort(key=lambda x: x['Type'].lower(), reverse=self.sort_descending)
        elif col == "Size":
            self.filtered_items.sort(key=lambda x: x['SizeBytes'], reverse=self.sort_descending)

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.node_map = {}
        for item in self.filtered_items:
            display_name = ("\U0001F4C1 " if item['IsDir'] else "\U0001F4C4 ") + item['Name']
            action_icon = "📋"
            node_id = self.tree.insert("", tk.END, values=(action_icon, display_name, item['Type'], item['FormattedSize']))
            self.node_map[node_id] = item
            
    def finish_analysis(self, msg):
        self.status_var.set(msg)
        self.analyze_btn.config(state=tk.NORMAL)
        
    def on_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1": return # Do not trigger folder open if double clicking copy
            
        item_id = self.tree.selection()
        if not item_id:
            return
        
        item_data = self.node_map.get(item_id[0])
        if not item_data:
            return
            
        full_path = item_data['FullPath']
        is_dir = item_data['IsDir']
        
        try:
            if is_dir:
                os.startfile(full_path)
            else:
                subprocess.run(['explorer', '/select,', os.path.normpath(full_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file/folder: {e}")

    def export_report(self):
        if not self.items:
            messagebox.showinfo("Info", "Nothing to export. Please analyze a directory first.")
            return
            
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        raw_path = os.path.normpath(self.path_var.get().strip().strip('"').strip("'"))
        _, path_tail = os.path.splitdrive(raw_path)
        parts = [p for p in path_tail.split(os.sep) if p]
        
        if not parts:
            folder_part = "root"
        else:
            folder_part = "-".join(parts[-4:]).lower() # e.g. desktop-game-counterstrike-videos
            
        # Clean string from special characters except dashes
        folder_part = "".join(x for x in folder_part if x.isalnum() or x == "-")
            
        timestamp = datetime.now().strftime("%H%M%S") # short timestamp
        filename = f"report_{folder_part}_{timestamp}.json"
        
        report_path = os.path.join(reports_dir, filename)
        
        to_export = []
        for item in self.filtered_items:
            to_export.append({
                'Name': item['Name'],
                'Type': item['Type'],
                'SizeBytes': item['SizeBytes'],
                'FormattedSize': item['FormattedSize'],
                'FullPath': item['FullPath']
            })
            
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(to_export, f, indent=4)
            
        messagebox.showinfo("Export Successful", f"Report saved to:\n{report_path}")

    def open_reports_folder(self):
        reports_dir = os.path.join(os.getcwd(), "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
        os.startfile(reports_dir)

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalyzerApp(root)
    root.mainloop()
