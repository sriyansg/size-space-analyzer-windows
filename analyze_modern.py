import os
import json
import threading
import subprocess
from datetime import datetime
import customtkinter as ctk

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

class ModernAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Directory Analyzer")
        self.geometry("950x650")
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.items = []
        self.filtered_items = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # 1. Top Bar
        top_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(top_frame, text="Directory:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        
        self.path_var = ctk.StringVar()
        self.path_entry = ctk.CTkEntry(top_frame, textvariable=self.path_var, width=400, placeholder_text="Enter or browse directory path...")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.browse_btn = ctk.CTkButton(top_frame, text="Browse...", command=self.browse_folder, width=100)
        self.browse_btn.pack(side="left", padx=(0, 10))
        
        self.analyze_btn = ctk.CTkButton(top_frame, text="Analyze", command=self.start_analysis, width=100, fg_color="#2b8256", hover_color="#206341")
        self.analyze_btn.pack(side="left", padx=(0, 10))
        
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(top_frame, values=["System", "Light", "Dark"],
                                                             command=self.change_appearance_mode_event, width=100)
        self.appearance_mode_optionemenu.pack(side="left")
        
        # 2. Search / Filter Bar
        mid_frame1 = ctk.CTkFrame(self, fg_color="transparent")
        mid_frame1.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(mid_frame1, text="Filter:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        
        self.filter_var = ctk.StringVar()
        self.filter_var.trace_add("write", self.on_filter_changed)
        self.filter_entry = ctk.CTkEntry(mid_frame1, textvariable=self.filter_var, placeholder_text="Type to filter results by name or type...")
        self.filter_entry.pack(side="left", fill="x", expand=True)

        # 3. Main Data Area
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray25"), height=30)
        header_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Name", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="Action", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=(10, 15))
        ctk.CTkLabel(header_frame, text="Size", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=10)
        ctk.CTkLabel(header_frame, text="Type", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=80)
        
        self.rows_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True)

        # 4. Bottom action bar
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.status_var = ctk.StringVar(value="Ready to analyze.")
        ctk.CTkLabel(bottom_frame, textvariable=self.status_var, text_color="gray").pack(side="left")
        
        self.open_report_btn = ctk.CTkButton(bottom_frame, text="Open Reports Folder", command=self.open_reports_folder, fg_color="transparent", border_width=1, text_color=("black", "white"))
        self.open_report_btn.pack(side="right", padx=(10, 0))
        
        self.export_btn = ctk.CTkButton(bottom_frame, text="Export JSON Report", command=self.export_report)
        self.export_btn.pack(side="right")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def browse_folder(self):
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
            
    def start_analysis(self):
        folder = self.path_var.get().strip().strip('"').strip("'")
        if not folder or not os.path.exists(folder) or not os.path.isdir(folder):
            self.status_var.set("Error: Please enter a valid directory path.")
            return
            
        self.analyze_btn.configure(state="disabled")
        self.status_var.set("Analyzing... please wait")
        
        for widget in self.rows_container.winfo_children():
            widget.destroy()
            
        self.items = []
        self.filtered_items = []
        
        threading.Thread(target=self.analyze_directory, args=(folder,), daemon=True).start()
        
    def analyze_directory(self, target_path):
        try:
            dir_contents = os.listdir(target_path)
        except PermissionError:
            self.after(0, self.finish_analysis, f"Error: Permission denied for {target_path}")
            return
            
        total_items = len(dir_contents)
        
        for i, item in enumerate(dir_contents):
            display_item = item if len(item) < 50 else item[:47] + "..."
            self.after(0, self.status_var.set, f"Analyzing {i+1}/{total_items}: {display_item}")
                
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
            
        self.items.sort(key=lambda x: x['SizeBytes'], reverse=True)
        self.after(0, self.filter_var.set, "")
        self.after(0, self.finish_analysis, f"Analysis complete. Found {len(self.items)} items.")
        
    def on_filter_changed(self, *args):
        query = self.filter_var.get().lower()
        if not query:
            self.filtered_items = list(self.items)
        else:
            self.filtered_items = [
                item for item in self.items 
                if query in item['Name'].lower() or query in item['Type'].lower()
            ]
        self.populate_list()

    def populate_list(self):
        for widget in self.rows_container.winfo_children():
            widget.destroy()
            
        for i, item in enumerate(self.filtered_items):
            bg_color = "transparent" if i % 2 == 0 else ("gray90", "gray15")
            
            row = ctk.CTkFrame(self.rows_container, fg_color=bg_color, corner_radius=0)
            row.pack(fill="x", pady=1)
            
            icon = "📁" if item['IsDir'] else "📄"
            name_label = ctk.CTkLabel(row, text=f"{icon} {item['Name']}", anchor="w", cursor="hand2")
            name_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            name_label.bind("<Button-1>", lambda e, path=item['FullPath'], isdir=item['IsDir']: self.open_item(path, isdir))
            
            # Copy & Analyze Action Button
            copy_btn = ctk.CTkButton(row, text="📋", width=30, height=24, fg_color="transparent", hover_color=("#e0e0e0", "#444444"), text_color=("black", "white"))
            copy_btn.pack(side="right", padx=(5, 10))
            
            # Hover tooltips via status bar
            tooltip_txt = "copy this folders path to clipboard and analyse" if item['IsDir'] else "copy this files path to clipboard"
            copy_btn.bind("<Enter>", lambda e, txt=tooltip_txt: self.status_var.set(txt))
            copy_btn.bind("<Leave>", lambda e: self.status_var.set("Ready."))
            
            # Click action
            copy_btn.configure(command=lambda path=item['FullPath'], isdir=item['IsDir']: self.copy_and_analyze(path, isdir))
            
            size_label = ctk.CTkLabel(row, text=item['FormattedSize'], width=80, anchor="e")
            size_label.pack(side="right", padx=10)
            
            type_label = ctk.CTkLabel(row, text=item['Type'], width=80, anchor="center")
            type_label.pack(side="right", padx=(10, 40))

    def copy_and_analyze(self, path, is_dir):
        self.clipboard_clear()
        self.clipboard_append(path)
        self.update()
        
        if is_dir:
            self.path_var.set(path)
            self.start_analysis()
        else:
            self.status_var.set("File path copied to clipboard!")

    def open_item(self, path, is_dir):
        try:
            if is_dir:
                os.startfile(path)
            else:
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
        except Exception as e:
            print(f"Could not open: {e}")

    def finish_analysis(self, msg):
        self.status_var.set(msg)
        self.analyze_btn.configure(state="normal")
        
    def export_report(self):
        if not self.items:
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
            
        folder_part = "".join(x for x in folder_part if x.isalnum() or x == "-")
            
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"report_modern_{folder_part}_{timestamp}.json"
        report_path = os.path.join(reports_dir, filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.filtered_items, f, indent=4)
            
        self.status_var.set(f"JSON Exported: {filename}")

    def open_reports_folder(self):
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        os.startfile(reports_dir)

if __name__ == "__main__":
    app = ModernAnalyzerApp()
    app.mainloop()
