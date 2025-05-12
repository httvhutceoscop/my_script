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
