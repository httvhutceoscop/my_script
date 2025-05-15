# migrate_attachment.py

import os
import requests
from urllib.parse import urljoin

def download_attachment(attachment_url, file_name, download_dir, headers):
    os.makedirs(download_dir, exist_ok=True)
    local_path = os.path.join(download_dir, file_name)
    response = requests.get(attachment_url, headers=headers, stream=True)
    response.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_path

def add_comment_listing_attachments(backlog_url_b, issue_key_b, api_key_b, attachment_info):
    """
    Tạo comment chứa danh sách file đính kèm đã migrate từ org A.
    """
    url = f"{backlog_url_b}/api/v2/issues/{issue_key_b}/comments"
    params = {'apiKey': api_key_b}

    lines = ["These attachments were migrated from the original issue on org A:"]
    for item in attachment_info:
        if item.get('download_url'):
            lines.append(f"- {item['name']} (original download: {item['download_url']})")
        else:
            lines.append(f"- {item['name']}")

    lines.append("\nPlease upload these files manually if needed.")
    data = {'content': '\n'.join(lines)}

    response = requests.post(url, params=params, data=data)
    response.raise_for_status()
    return response.json()

def migrate_attachments_for_issue(source_issue, issue_key_b, api_key_a, api_key_b,
                                   backlog_url_a, backlog_url_b, download_dir='./attachments'):
    headers_a = {'Authorization': f'Bearer {api_key_a}'}
    attachment_info_list = []

    for attachment in source_issue.get("attachments", []):
        attachment_id = attachment['id']
        attachment_name = attachment['name']
        download_url = f"{backlog_url_a}/api/v2/issues/{source_issue['issueKey']}/attachments/{attachment_id}"

        print(f"⬇️  Downloading: {attachment_name}")
        try:
            file_path = download_attachment(download_url, attachment_name, download_dir, headers_a)
            attachment_info_list.append({
                'name': attachment_name,
                'download_url': download_url
            })
        except Exception as e:
            print(f"⚠️  Failed to download {attachment_name}: {e}")
            attachment_info_list.append({
                'name': attachment_name,
                'download_url': None
            })

    if attachment_info_list:
        print(f"💬 Creating comment listing {len(attachment_info_list)} attachment(s)...")
        add_comment_listing_attachments(backlog_url_b, issue_key_b, api_key_b, attachment_info_list)
        print(f"✔ Attachments listed in comment on issue {issue_key_b}")
