import datetime
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Setup logging
logging.basicConfig(filename="rename_log.log",
                    level=logging.INFO, format='%(asctime)s - %(message)s')


def get_file_creation_date(file_path):
    try:
        creation_date = datetime.datetime.fromtimestamp(
            os.path.getmtime(file_path)).strftime('%Y-%m-%d')
        return creation_date
    except Exception as e:
        logging.error(f"Error getting date for {file_path}: {e}")
        return None


def rename_with_date(file_path, folder_path):
    ext = os.path.splitext(file_path)[1]
    original_name = os.path.basename(file_path)

    date_str = get_file_creation_date(file_path)
    if not date_str:
        return None

    base_name = date_str
    new_name = f"{base_name}{ext}"
    i = 1
    while os.path.exists(os.path.join(folder_path, new_name)):
        new_name = f"{base_name}_{i}{ext}"
        i += 1

    new_path = os.path.join(folder_path, new_name)
    os.rename(file_path, new_path)
    return new_name


def select_folder():
    folder = filedialog.askdirectory()
    if not folder:
        return

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        if filename.startswith(".") or filename.endswith(".DS_Store"):
            continue
        if not os.path.isfile(path):
            continue

        logging.info(f"Original path: {path}")

        try:
            new_name = rename_with_date(path, folder)
            if new_name:
                logging.info(f"Renamed: {filename} → {new_name}")
            else:
                logging.info(f"Skipped: {filename}")
        except Exception as e:
            logging.error(f"Error: {filename} → {e}")

    messagebox.showinfo(
        "Done", "Đã xử lý xong. Kiểm tra file rename_log.txt để biết chi tiết.")


# GUI
root = tk.Tk()
root.title("Renamer Tool")
root.geometry("300x150")

label = tk.Label(root, text="Chọn thư mục chứa files để đổi tên:")
label.pack(pady=10)

btn = tk.Button(root, text="Chọn thư mục", command=select_folder)
btn.pack()

root.mainloop()
