Dưới đây là hướng dẫn tạo **project Python hoàn chỉnh** đáp ứng toàn bộ yêu cầu của bạn:

---

## 🎯 Tính năng chính:
1. Duyệt file ảnh từ một thư mục được chọn bằng giao diện Tkinter.
2. Lấy ngày chụp từ **EXIF**; nếu không có, lấy ngày tạo file.
3. Đổi tên file thành `YYYY-MM-DD[_1][_2]` nếu trùng tên.
4. Ghi log chi tiết vào `rename_log.txt`.
5. Giao diện thân thiện chạy được trên macOS.
6. Có thể đóng gói thành `.app` với icon `.icns`.

---

## 📁 Cấu trúc thư mục project

```
photo_renamer/
│
├── icon.icns
├── main.py
├── utils.py
├── README.md
├── requirements.txt
└── rename_log.txt
```

---

## 📜 File `main.py`: giao diện & xử lý chính

```python
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
```

---

## 📦 File `utils.py`: xử lý EXIF, rename

```python
from PIL import Image
from PIL.ExifTags import TAGS
import os
import datetime

def get_photo_date(file_path):
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if not exif_data:
            return None
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag)
            if decoded == "DateTimeOriginal":
                date_str = value.split(" ")[0].replace(":", "-")
                return date_str
    except Exception:
        pass

    # Fallback: dùng ngày tạo file
    timestamp = os.path.getctime(file_path)
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

def rename_with_date(file_path, folder_path):
    ext = os.path.splitext(file_path)[1]
    original_name = os.path.basename(file_path)

    date_str = get_photo_date(file_path)
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
```

---

## 📝 `requirements.txt`

```
Pillow
```

---

## 🧭 File `README.md` – Hướng dẫn đóng gói macOS `.app`

```markdown
# Photo Renamer (macOS)

## Mô tả
Ứng dụng đổi tên file ảnh dựa trên ngày chụp (EXIF), có GUI dùng Tkinter.

## Yêu cầu
- Python 3.x
- pip install -r requirements.txt
- macOS (để đóng gói app)

## Chạy thử
```bash
python3 main.py
```

## Đóng gói thành `.app` trên macOS

### Bước 1: Cài PyInstaller
```bash
pip install pyinstaller
```

### Bước 2: Đóng gói
```bash
pyinstaller --windowed --icon=icon.icns --name "PhotoRenamer" main.py
```

Kết quả nằm trong thư mục:
```
dist/PhotoRenamer.app
```

### Ghi chú:
- Bạn cần có file `icon.icns` để gán icon. Có thể tạo từ PNG bằng:
```bash
sips -s format icns youricon.png --out icon.icns
```

```

---

## 🧪 Kiểm thử
- Đảm bảo test với các file có/không có EXIF.
- Kiểm thử trường hợp file đã tồn tại → `_1`, `_2`.

---

Bạn có muốn mình tạo project ZIP sẵn để bạn chỉ cần tải về dùng thử?

========

Tôi đã tạo một file hình ảnh icon đơn giản với văn bản "MyApp". Bạn có thể tải file `icon.png` từ [đây](sandbox:/mnt/data/icon.png).

Nếu bạn muốn chuyển đổi file này thành `icon.icns`, bạn có thể sử dụng các bước mà tôi đã hướng dẫn trước đó, hoặc nếu bạn cần tôi làm điều này cho bạn, hãy cho tôi biết!



======


Dường như trên môi trường này không hỗ trợ công cụ `iconutil` để chuyển đổi trực tiếp thành `.icns`. Tuy nhiên, bạn có thể tự làm việc này trên máy tính của mình.

### 🛠 Cách làm trên máy Mac:
1. **Cài đặt iconset**: Tải file `icon.png` từ [đây](sandbox:/mnt/data/icon.png).
2. **Tạo iconset và file `.icns`**:
   - Mở Terminal và làm theo các bước tôi đã hướng dẫn trước:
   ```bash
   mkdir icon.iconset
   sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
   sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
   sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
   sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
   sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
   cp icon.png              icon.iconset/icon_512x512@2x.png
   iconutil -c icns icon.iconset
   ```
3. Sau khi thực hiện, bạn sẽ có file `.icns`.

Nếu bạn gặp bất kỳ vấn đề nào, hãy cho tôi biết để tôi hỗ trợ thêm!