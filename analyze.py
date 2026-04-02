import os
import json

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

def main():
    target_path = input("Please paste the directory path you want to analyze: ").strip().strip('"').strip("'")
    
    if not os.path.exists(target_path):
        print(f"Error: The path '{target_path}' does not exist.")
        return

    if not os.path.isdir(target_path):
        print(f"Error: The path '{target_path}' is not a directory.")
        return

    print(f"Analyzing '{target_path}'...")
    
    items = []
    
    try:
        dir_contents = os.listdir(target_path)
    except PermissionError:
         print(f"Error: Permission denied to access '{target_path}'.")
         return
         
    for item in dir_contents:
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
            
        items.append({
            'Name': item,
            'Type': ext,
            'SizeBytes': size,
            'FormattedSize': format_size(size)
        })

    items.sort(key=lambda x: x['SizeBytes'], reverse=True)
    
    report_name = f'folder_report.json'
    with open(report_name, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=4)

    print(f"Report saved to {report_name}")

if __name__ == "__main__":
    main()
