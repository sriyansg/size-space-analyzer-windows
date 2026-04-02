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
        self.root.geometry("900x650")
        
        self.items = []
        self.filtered_items = []
        self.node_map = {}
        
        self.current_sort_col = "Size"
        self.sort_descending = True
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top Frame (Controls)
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)
        top_frame.columnconfigure(1, weight=1)
        
        # Row 0: Directory Selection
        ttk.Label(top_frame, text="Directory:").grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(top_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, padx=(0,5), pady=5, sticky=tk.EW)
        
        ttk.Button(top_frame, text="Browse...", command=self.browse_folder).grid(row=0, column=2, padx=(0,5), pady=5)
        self.analyze_btn = ttk.Button(top_frame, text="Analyze", command=self.start_analysis)
        self.analyze_btn.grid(row=0, column=3, pady=5)
        
        # Row 1: Search/Filter
        ttk.Label(top_frame, text="Filter (Name/Type):").grid(row=1, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self.on_filter_changed)
        self.filter_entry = ttk.Entry(top_frame, textvariable=self.filter_var)
        self.filter_entry.grid(row=1, column=1, columnspan=3, pady=5, sticky=tk.EW)
        
        # Middle Frame (Treeview)
        mid_frame = ttk.Frame(self.root, padding="10 0 10 10")
        mid_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Name", "Type", "Size")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings")
        
        # Double click to open folder/file
        self.tree.bind("<Double-1>", self.on_double_click)
        
        self.tree.heading("Name", text="Name", command=lambda: self.sort_tree("Name"))
        self.tree.heading("Type", text="Type", command=lambda: self.sort_tree("Type"))
        self.tree.heading("Size", text="Size \u25BC", command=lambda: self.sort_tree("Size"))
        
        self.tree.column("Name", width=500, anchor=tk.W)
        self.tree.column("Type", width=120, anchor=tk.CENTER)
        self.tree.column("Size", width=120, anchor=tk.E)
        
        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom Frame (Status and Actions)
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready. Select a directory to begin.")
        ttk.Label(bottom_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        ttk.Button(bottom_frame, text="Export JSON Report", command=self.export_report).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(bottom_frame, text="Open Reports Folder", command=self.open_reports_folder).pack(side=tk.RIGHT)
        
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
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.items = []
        self.filtered_items = []
        self.node_map = {}
        
        # Run in a background thread to prevent UI freezing
        threading.Thread(target=self.analyze_directory, args=(folder,), daemon=True).start()
        
    def analyze_directory(self, target_path):
        try:
            dir_contents = os.listdir(target_path)
        except PermissionError:
            self.root.after(0, self.finish_analysis, f"Error: Permission denied for {target_path}")
            return
            
        total_items = len(dir_contents)
        
        for i, item in enumerate(dir_contents):
            # Update status occasionally
            if i % 10 == 0:
                self.root.after(0, self.status_var.set, f"Analyzing {i}/{total_items} items...")
                
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
            
        # Initial display setup
        self.filter_var.set("") # Clear filter after a fresh load
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
        if self.current_sort_col == col:
            self.sort_descending = not self.sort_descending
        else:
            self.current_sort_col = col
            self.sort_descending = True if col == "Size" else False
            
        self.sort_data()
        self.populate_tree()
        
        # Update arrows in headings
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
        # Clear current tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.node_map = {}
        for item in self.filtered_items:
            # We pad the Name with folder emoji if it's a directory
            display_name = ("\U0001F4C1 " if item['IsDir'] else "\U0001F4C4 ") + item['Name']
            node_id = self.tree.insert("", tk.END, values=(display_name, item['Type'], item['FormattedSize']))
            self.node_map[node_id] = item
            
    def finish_analysis(self, msg):
        self.status_var.set(msg)
        self.analyze_btn.config(state=tk.NORMAL)
        
    def on_double_click(self, event):
        item_id = self.tree.selection()
        if not item_id:
            return
        
        # Get actual data from map
        item_data = self.node_map.get(item_id[0])
        if not item_data:
            return
            
        full_path = item_data['FullPath']
        is_dir = item_data['IsDir']
        
        try:
            if is_dir:
                # Open directory in Windows explorer
                os.startfile(full_path)
            else:
                # Open containing folder pointing directly at the file
                subprocess.run(['explorer', '/select,', os.path.normpath(full_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file/folder: {e}")

    def export_report(self):
        if not self.items:
            messagebox.showinfo("Info", "Nothing to export. Please analyze a directory first.")
            return
            
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        folder_name = os.path.basename(os.path.normpath(self.path_var.get().strip().strip('"').strip("'")))
        if not folder_name:
            folder_name = "root"
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{folder_name}_{timestamp}.json"
        
        # Replace problematic characters
        filename = "".join(x for x in filename if x.isalnum() or x in "._- ")
        
        report_path = os.path.join(reports_dir, filename)
        
        # We export the filtered items to JSON (so if user shrinks list via search, it exports just that)
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
            
        messagebox.showinfo("Export Successful", f"Report saved format as JSON successfully to:\n{report_path}")

    def open_reports_folder(self):
        reports_dir = os.path.join(os.getcwd(), "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
        os.startfile(reports_dir)

if __name__ == "__main__":
    root = tk.Tk()
    
    # Try to make Windows use a modern aesthetic theme if possible
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")
        
    app = AnalyzerApp(root)
    root.mainloop()
