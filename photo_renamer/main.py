import tkinter as tk
from tkinter import filedialog, messagebox
import os
from utils import get_photo_date, rename_with_date

def select_folder():
    folder = filedialog.askdirectory()
    if not folder:
        return

    log_lines = []
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        if not os.path.isfile(path):
            continue

        try:
            new_name = rename_with_date(path, folder)
            if new_name:
                log_lines.append(f"Renamed: {filename} → {new_name}")
            else:
                log_lines.append(f"Skipped: {filename}")
        except Exception as e:
            log_lines.append(f"Error: {filename} → {e}")

    with open("rename_log.txt", "a") as log_file:
        for line in log_lines:
            log_file.write(line + "\n")

    messagebox.showinfo("Done", "Đã xử lý xong. Kiểm tra file rename_log.txt để biết chi tiết.")

# GUI
root = tk.Tk()
root.title("Photo Renamer")
root.geometry("300x150")

label = tk.Label(root, text="Chọn thư mục chứa ảnh để đổi tên:")
label.pack(pady=10)

btn = tk.Button(root, text="Chọn thư mục", command=select_folder)
btn.pack()

root.mainloop()
