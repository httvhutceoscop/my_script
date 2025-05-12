Để thực hiện yêu cầu của bạn, chúng ta sẽ chia thành các bước sau:

### 1. Xử lý file video:
- Duyệt qua các file trong một thư mục.
- Lấy thông tin ngày quay hoặc ngày tạo video từ metadata (sử dụng thư viện `moviepy` hoặc `ffmpeg`).
- Đổi tên file theo ngày quay hoặc tạo video.
- Nếu file đã tồn tại, thêm hậu tố `_1`, `_2`,...

### 2. Tạo giao diện với Tkinter:
- Cung cấp giao diện cho phép người dùng chọn thư mục và hiển thị log quá trình xử lý.

### 3. Đóng gói ứng dụng:
- Sử dụng `py2app` để đóng gói ứng dụng thành `.app` trên macOS.
- Đảm bảo có icon `.icns` cho ứng dụng.

Dưới đây là một ví dụ chi tiết cho script Python của bạn:

### Cài đặt các thư viện cần thiết:
Bạn sẽ cần các thư viện sau:
```bash
pip install moviepy tk py2app
```

### 1. Script Python để xử lý video

```python
import os
import re
import logging
from moviepy.editor import VideoFileClip
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

# Setup logging
logging.basicConfig(filename="video_rename_log.txt", level=logging.INFO, format='%(asctime)s - %(message)s')

def get_video_creation_date(video_path):
    try:
        video = VideoFileClip(video_path)
        creation_date = datetime.fromtimestamp(os.path.getmtime(video_path)).strftime('%Y-%m-%d')
        return creation_date
    except Exception as e:
        logging.error(f"Error getting date for {video_path}: {e}")
        return None

def rename_video_files(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.mov', '.avi', '.mkv'))]
    
    for file in files:
        file_path = os.path.join(folder_path, file)
        creation_date = get_video_creation_date(file_path)

        if creation_date:
            new_name = f"{creation_date}_{file}"
            new_file_path = os.path.join(folder_path, new_name)

            counter = 1
            while os.path.exists(new_file_path):
                new_name = f"{creation_date}_{counter}_{file}"
                new_file_path = os.path.join(folder_path, new_name)
                counter += 1

            os.rename(file_path, new_file_path)
            logging.info(f"Renamed {file} to {new_name}")
            print(f"Renamed {file} to {new_name}")
        else:
            logging.warning(f"Could not get creation date for {file}")

def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        rename_video_files(folder_path)
        messagebox.showinfo("Success", "Videos renamed successfully.")

def create_gui():
    window = tk.Tk()
    window.title("Video Renamer")
    
    label = tk.Label(window, text="Choose folder with videos to rename:")
    label.pack(padx=10, pady=10)
    
    button = tk.Button(window, text="Browse", command=browse_folder)
    button.pack(padx=10, pady=10)
    
    window.mainloop()

if __name__ == "__main__":
    create_gui()
```

### 2. Cấu hình để đóng gói ứng dụng thành `.app` trên macOS:
Tạo một thư mục project với cấu trúc sau:
```
my_project/
│
├── video_rename.py
├── icon.icns
├── setup.py
└── requirements.txt
```

**`requirements.txt`**:
```
moviepy
tk
py2app
```

**`setup.py`**:
```python
from setuptools import setup

APP = ['video_rename.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['moviepy', 'tkinter'],
    'iconfile': 'icon.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

**`icon.icns`**:
- Tạo icon `.icns` sử dụng công cụ như [Icon Slate](https://iconslate.app) hoặc [Image2icon](https://www.img2icnsapp.com).

### 3. Đóng gói ứng dụng với `py2app`:
- Di chuyển đến thư mục project và chạy lệnh sau:
```bash
python setup.py py2app
```
- Sau khi quá trình hoàn tất, bạn sẽ tìm thấy `.app` trong thư mục `dist`.

### 4. Hướng dẫn đóng gói nhanh:
1. Đảm bảo bạn đã cài đặt tất cả các thư viện trong `requirements.txt` bằng lệnh:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy lệnh đóng gói:
   ```bash
   python setup.py py2app
   ```
3. Sau khi đóng gói thành công, bạn sẽ có file `.app` trong thư mục `dist`. Chạy ứng dụng trực tiếp trên macOS.

### Lưu ý:
- Nếu bạn muốn thay đổi giao diện hoặc tính năng thêm, bạn có thể điều chỉnh code Tkinter theo yêu cầu của mình.
- Đảm bảo rằng bạn đã có `ffmpeg` hoặc `moviepy` cài sẵn để xử lý video, vì chúng giúp trích xuất thông tin ngày tháng của video.