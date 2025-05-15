import os
import requests
from tqdm import tqdm

# CONFIG
ORG_A_DOMAIN = 'https://wolfgroup.backlog.com'
ORG_B_DOMAIN = 'https://fabbi.backlog.com'
API_KEY_A = 'LoIgdvbaMLaHS8fCzTgf8rp33lNgZtsoYUvDLV8e8immQbUOO4IFCxWCwlqvr7YB'
API_KEY_B = 'vSP0S13GnHR1BopcWAff58k2dNitll68OeDvjZkYgv9C7HS98RyfqUVyxDVJdqSe'
PROJECT_KEY_A = 'STYLE'
PROJECT_KEY_B = 'SELF_L'
PRIORITY_ID = 3  # 1: Low, 2: Normal, 3: High
ATTACHMENTS_DIR = 'attachments'

# Ensure attachment folder exists
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# UTILS
def get(url, api_key, params=None):
    headers = {'Authorization': f'Bearer {api_key}'}
    return requests.get(url, headers=headers, params=params)

def post(url, api_key, data=None, files=None):
    headers = {'Authorization': f'Bearer {api_key}'}
    return requests.post(url, headers=headers, data=data, files=files)

def get_project_id(domain, api_key, project_key):
    url = f'{domain}/api/v2/projects/{project_key}'
    r = get(url, api_key)
    r.raise_for_status()
    return r.json()['id']

def get_items(domain, api_key, project_id, item_type):
    url = f'{domain}/api/v2/projects/{project_id}/{item_type}'
    r = get(url, api_key)
    r.raise_for_status()
    return r.json()

def create_item(domain, api_key, project_id, item_type, name):
    url = f'{domain}/api/v2/projects/{project_id}/{item_type}'
    r = post(url, api_key, data={'name': name})
    r.raise_for_status()
    return r.json()

def ensure_item(name, items_b, create_fn):
    for i in items_b:
        if i['name'].strip().lower() == name.strip().lower():
            return i['id']
    new_item = create_fn(name)
    return new_item['id']

# MIGRATION
def download_attachment(domain, api_key, issue_key, attachment):
    url = f"{domain}/api/v2/issues/{issue_key}/attachments/{attachment['id']}"
    file_path = os.path.join(ATTACHMENTS_DIR, f"{issue_key}_{attachment['id']}_{attachment['name']}")
    r = get(url, api_key)
    with open(file_path, 'wb') as f:
        f.write(r.content)
    return file_path

def upload_attachment(domain, api_key, file_path):
    url = f"{domain}/api/v2/space/attachment"
    with open(file_path, 'rb') as f:
        r = post(url, api_key, files={'file': f})
        r.raise_for_status()
        return r.json()[0]['id']

def migrate():
    print('🔄 Đang load thông tin project và metadata...')
    proj_id_a = get_project_id(ORG_A_DOMAIN, API_KEY_A, PROJECT_KEY_A)
    proj_id_b = get_project_id(ORG_B_DOMAIN, API_KEY_B, PROJECT_KEY_B)
    
    print(f'🔄 Project ID A: {proj_id_a}')
    print(f'🔄 Project ID B: {proj_id_b}')

    # Metadata A
    types_a = get_items(ORG_A_DOMAIN, API_KEY_A, proj_id_a, 'issueTypes')
    cats_a = get_items(ORG_A_DOMAIN, API_KEY_A, proj_id_a, 'categories')
    miles_a = get_items(ORG_A_DOMAIN, API_KEY_A, proj_id_a, 'versions')
    stats_a = get(f"{ORG_A_DOMAIN}/api/v2/statuses", API_KEY_A).json()
    print("stats_a", stats_a)
    print("types_a", types_a)
    print("cats_a", cats_a)
    print("miles_a", miles_a)


    return

    # Metadata B
    types_b = get_items(ORG_B_DOMAIN, API_KEY_B, proj_id_b, 'issueTypes')
    cats_b = get_items(ORG_B_DOMAIN, API_KEY_B, proj_id_b, 'categories')
    miles_b = get_items(ORG_B_DOMAIN, API_KEY_B, proj_id_b, 'versions')
    stats_b = get(f"{ORG_B_DOMAIN}/api/v2/statuses", API_KEY_B).json()

    # Build mapping
    type_map = {}
    for t in types_a:
        type_map[t['id']] = ensure_item(t['name'], types_b, lambda name: create_item(ORG_B_DOMAIN, API_KEY_B, proj_id_b, 'issueTypes', name))

    cat_map = {}
    for c in cats_a:
        cat_map[c['id']] = ensure_item(c['name'], cats_b, lambda name: create_item(ORG_B_DOMAIN, API_KEY_B, proj_id_b, 'categories', name))

    mile_map = {}
    for m in miles_a:
        mile_map[m['id']] = ensure_item(m['name'], miles_b, lambda name: create_item(ORG_B_DOMAIN, API_KEY_B, proj_id_b, 'versions', name))

    stat_map = {}
    for s in stats_a:
        stat_map[s['id']] = next((sb['id'] for sb in stats_b if sb['name'].lower() == s['name'].lower()), None)

    print('📦 Lấy danh sách issue từ tổ chức A...')
    issues = get(f"{ORG_A_DOMAIN}/api/v2/issues", API_KEY_A, params={'projectId[]': proj_id_a, 'count': 100}).json()

    for issue in tqdm(issues, desc="Migrating Issues"):
        summary = issue['summary']
        desc = issue.get('description', '')
        type_id_b = type_map.get(issue['issueType']['id'])
        stat_id_b = stat_map.get(issue['status']['id'], None)
        cat_ids = [cat_map[c['id']] for c in issue.get('category', []) if c['id'] in cat_map]
        mile_ids = [mile_map[m['id']] for m in issue.get('milestone', []) if m['id'] in mile_map]

        # Attachments
        atts = get(f"{ORG_A_DOMAIN}/api/v2/issues/{issue['issueKey']}/attachments", API_KEY_A).json()
        att_ids = []
        for att in atts:
            fp = download_attachment(ORG_A_DOMAIN, API_KEY_A, issue['issueKey'], att)
            att_ids.append(upload_attachment(ORG_B_DOMAIN, API_KEY_B, fp))

        # Create issue
        issue_data = {
            'projectId': proj_id_b,
            'summary': summary,
            'description': desc,
            'issueTypeId': type_id_b,
            'priorityId': issue['priority']['id']
        }

        for i in att_ids:
            issue_data.setdefault('attachmentId[]', []).append(i)
        for i in cat_ids:
            issue_data.setdefault('categoryId[]', []).append(i)
        for i in mile_ids:
            issue_data.setdefault('milestoneId[]', []).append(i)

        if stat_id_b:
            issue_data['statusId'] = stat_id_b

        res = post(f"{ORG_B_DOMAIN}/api/v2/issues", API_KEY_B, data=issue_data)
        res.raise_for_status()
        issue_b_key = res.json()['issueKey']

        # Comments
        comments = get(f"{ORG_A_DOMAIN}/api/v2/issues/{issue['issueKey']}/comments", API_KEY_A).json()
        for c in comments:
            content = f"[From {c['createdUser']['name']} at {c['created']}]:\n{c['content']}"
            post(f"{ORG_B_DOMAIN}/api/v2/issues/{issue_b_key}/comments", API_KEY_B, data={'content': content})

    print("✅ Hoàn tất migrate toàn bộ issue.")

if __name__ == '__main__':
    migrate()
