import os
import requests
import re

ENT_URL = "https://drive.google.com/drive/folders/18mGMAZRZ6R3G6p1q6cLOzId72NeEkPZb"


def print_banner():
    print("🚀 Backlog Migrator Started")


def get(url, api_key, params=None):
    if params is None:
        params = {}
    params['apiKey'] = api_key
    return requests.get(url, params=params)


def post(url, api_key, data=None, headers=None, files=None):
    if headers is None:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if data is None:
        data = {}
    params = {"apiKey": api_key}

    if files:
        headers = {"Content-Type": "multipart/form-data"}
        response = requests.post(url, params=params, data=data, files=files)
    else:
        response = requests.post(
            url, params=params, data=data, headers=headers)
    # response.raise_for_status()
    return response


def patch(url, api_key, data=None):
    if data is None:
        data = {}
    params = {"apiKey": api_key}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.patch(url, params=params, data=data, headers=headers)
    # response.raise_for_status()
    return response


def download_attachment(domain, api_key, issue_key, new_issue_key, att):
    url = f"{domain}/api/v2/issues/{issue_key}/attachments/{att['id']}"
    r = get(url, api_key)
    if r.status_code != 200:
        print(f"❌ Error downloading attachment: {r.status_code}, {r.text}")
        return None

    os.makedirs(f"./backlog_migrator/data/{new_issue_key}", exist_ok=True)

    filename = f"./backlog_migrator/data/{new_issue_key}/{att['name']}"
    with open(filename, 'wb') as f:
        f.write(r.content)
    return filename


def upload_attachment(url, api_key, filepath):
    with open(filepath, 'rb') as f:
        files = {'file': f}
        r = post(url, api_key, files=files)
        if r.status_code != 200:
            print(f"❌ Error uploading attachment: {r.status_code}, {r.text}")
            return None
    return r.json()['id']


def add_comment_listing_attachments(url, api_key, attachment_info):
    """
    Tạo comment chứa danh sách file đính kèm đã migrate từ org A.
    """
    lines = ["These attachments were migrated from the original issue on org A:"]
    for item in attachment_info:
        att_name = item['name']

        if item.get('download_url'):
            lines.append(
                f"- {att_name} (original download: {item['download_url']})")
        else:
            lines.append(f"- {att_name}")

    lines.append("\nPlease upload these files manually if needed.")
    data = {'content': '\n'.join(lines)}

    response = post(url, api_key=api_key, data=data)
    if response.status_code != 201:
        print(
            f"❌ Error add comment listing attachments: {response.status_code}, {response.text}")
        return None
    return response


def replace_image_link(text, file_url_mapping):
    def replacer(match):
        file_name = match.group(1)
        # Kiểm tra điều kiện file_name, ví dụ kiểm tra có trong danh sách file_url_mapping
        if file_name in file_url_mapping:
            url = file_url_mapping[file_name]
            return f"[{file_name}]({url})"
        else:
            return match.group(0)  # không thay thế nếu không thoả điều kiện

    # Regex để bắt chuỗi ![image][$file_name]
    pattern = r"!\[image\]\[\$(.*?)\]"
    return re.sub(pattern, replacer, text)
