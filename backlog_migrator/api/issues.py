from datetime import datetime
import os
from tqdm import tqdm
from backlog_migrator.utils.helpers import get, post, patch, download_attachment, add_comment_listing_attachments
# from migrate_attachment import migrate_attachments_for_issue

# CONFIG
ORG_A_DOMAIN = 'https://xx.backlog.com'
ORG_B_DOMAIN = 'https://yy.backlog.com'
API_KEY_A = ''
API_KEY_B = ''
PROJECT_KEY_A = 'xx'
PROJECT_KEY_B = 'yy'
ATTACHMENTS_DIR = 'attachments'

HOST_A = f"{ORG_A_DOMAIN}/api/v2"
HOST_B = f"{ORG_B_DOMAIN}/api/v2"
DRIVE_BACKLOG_ATTACHMENT_URL = "https://drive.google.com/drive/folders/18mGMAZRZ6R3G6p1q6cLOzId72NeEkPZb"
# END CONFIG


def migrate_issues():
    print("🔄 Bắt đầu migrate issues...")
    os.makedirs("./backlog_migrator/data", exist_ok=True)

    proj_a = get(
        f"{HOST_A}/projects/{PROJECT_KEY_A}", API_KEY_A).json()
    proj_b = get(
        f"{HOST_B}/projects/{PROJECT_KEY_B}", API_KEY_B).json()
    proj_id_b = proj_b['id']
    # print("project_a:", proj_a)
    # print("project_b:", proj_b)
    # print("project_id_b:", proj_id_b)

    def sync_items(type_):
        a_list = get(
            f"{HOST_A}/projects/{PROJECT_KEY_A}/{type_}", API_KEY_A).json()
        b_list = get(
            f"{HOST_B}/projects/{PROJECT_KEY_B}/{type_}", API_KEY_B).json()
        print(f"a_list ({type_}):", a_list)
        # print(f"b_list ({type_}):", b_list)
        b_name_id = {i['name']: i['id'] for i in b_list}
        # print(f"b_name_id ({type_}):", b_name_id)

        id_map = {}
        for i in a_list:
            print(f"Processing {type_}:", i)
            if i['name'] in b_name_id:
                print(f"Updating {type_}:", i['name'])
                id_map[i['id']] = b_name_id[i['name']]

                data = {
                    "name": i['name'],
                }

                if type_ in ["issueTypes", "statuses"]:
                    data['color'] = i['color']

                if type_ == "issueTypes":
                    data.update({
                        "templateSummary": i['templateSummary'],
                        "templateDescription": i['templateDescription']
                    })

                res = patch(
                    f"{HOST_B}/projects/{PROJECT_KEY_B}/{type_}/{b_name_id[i['name']]}", API_KEY_B, data=data)
                if res.status_code == 200:
                    print("✅ Cập nhật thành công!")
                else:
                    print("❌ Lỗi:", res.status_code, res.text)
            else:
                print(f"Creating {type_}:", i['name'])
                # Create new item in Org B
                data = {
                    'name': i['name'],
                }

                if type_ in ["issueTypes", "statuses"]:
                    data['color'] = i['color']

                if type_ == "issueTypes":
                    data.update({
                        "displayOrder": i['displayOrder'],
                        "templateSummary": i['templateSummary'],
                        "templateDescription": i['templateDescription']
                    })

                if type_ == "versions":
                    # Chuyển về định dạng yyyy-MM-dd
                    start_date = datetime.fromisoformat(
                        i['startDate'].replace("Z", "")).strftime("%Y-%m-%d")
                    release_due_date = datetime.fromisoformat(
                        i['releaseDueDate'].replace("Z", "")).strftime("%Y-%m-%d")

                    data.update({
                        "description": i['description'],
                        "startDate": start_date,
                        "releaseDueDate": release_due_date
                    })

                res = post(
                    f"{HOST_B}/projects/{PROJECT_KEY_B}/{type_}", API_KEY_B, data=data)
                if res.status_code == 200:
                    print("✅ Create thành công!")
                else:
                    print("❌ Lỗi:", res.status_code, res.text)

                new_id = res.json()['id']
                id_map[i['id']] = new_id
        return id_map

    type_map = sync_items("issueTypes")
    stat_map = sync_items("statuses")
    cat_map = sync_items("categories")
    mile_map = sync_items("versions")

    issues = []
    offset = 0
    while True:
        res = get(f"{HOST_A}/issues", API_KEY_A,
                  params={"projectId[]": proj_a['id'], "count": 100, "offset": offset})
        batch = res.json()
        if not batch:
            break
        issues.extend(batch)
        offset += 100

    len_issues = len(issues)
    print(f"🔄 Đã tìm thấy {len_issues} issues trong project {proj_a['name']}")

    issue_map = {i['id']: i for i in issues}
    parent_issues = [i for i in issues if not i.get('parentIssueId')]
    child_issues = [i for i in issues if i.get('parentIssueId')]
    print(
        f"🔄 Đã tìm thấy {len(parent_issues)} parent issues và {len(child_issues)} child issues")

    key_to_new_id = {}

    def create_issue(issue, parent_id=None):
        desc = issue.get('description') or ''
        data = {
            "projectId": proj_id_b,
            "summary": issue["summary"],
            "description": desc,
            "issueTypeId": type_map[issue["issueType"]["id"]],
            "priorityId": issue["priority"]["id"]
        }
        if parent_id:
            data["parentIssueId"] = parent_id
        if issue.get("category"):
            for c in issue["category"]:
                if c["id"] in cat_map:
                    data.setdefault("categoryId[]", []).append(
                        cat_map[c["id"]])
        if issue.get("milestone"):
            for m in issue["milestone"]:
                if m["id"] in mile_map:
                    data.setdefault("milestoneId[]", []).append(
                        mile_map[m["id"]])

        print(f"Creating issue: {issue['issueKey']}")

        new_issue = None
        new_issue_key = None
        res = post(f"{HOST_B}/issues", API_KEY_B, data=data)
        if res.status_code == 201:
            print("✅ Create issue thành công!")
            new_issue = res.json()
            new_issue_key = new_issue['issueKey']
            key_to_new_id[issue['issueKey']] = new_issue['id']
        else:
            print("❌ Lỗi:", res.status_code, res.text)
            return

        # Attachment
        attachment_info_list = []
        atts = get(
            f"{HOST_A}/issues/{issue['issueKey']}/attachments", API_KEY_A).json()
        for att in atts:
            fpath = download_attachment(
                ORG_A_DOMAIN, API_KEY_A, issue['issueKey'], new_issue_key, att)
            print(f"Downloaded attachment: {fpath}")
            attachment_id = att['id']
            attachment_name = att['name']
            download_url = f"{HOST_A}/issues/{issue['issueKey']}/attachments/{attachment_id}"
            attachment_info_list.append({
                'name': attachment_name,
                'download_url': download_url
            })
            url = f"{HOST_B}/issues/{new_issue_key}/comments"
            res = add_comment_listing_attachments(
                url, API_KEY_B, attachment_info_list)
            print(
                f"Creating comment listing {len(attachment_info_list)} attachment(s)...", res.json())

        # Comment
        comments = get(
            f"{HOST_A}/issues/{issue['issueKey']}/comments", API_KEY_A).json()
        for c in comments:
            content = f"[{c['createdUser']['name']} - {c['created']}]:\n{c['content']}\nRef: [{new_issue_key}]({DRIVE_BACKLOG_ATTACHMENT_URL})"
            post(
                f"{HOST_B}/issues/{new_issue_key}/comments", API_KEY_B, data={"content": content})

    for i in tqdm(parent_issues, desc="Parent Issues"):
        create_issue(i)
        break

    return

    for i in tqdm(child_issues, desc="Sub-Tasks"):
        parent_key = issue_map[i["parentIssueId"]]["issueKey"]
        parent_id = key_to_new_id.get(parent_key)
        if parent_id:
            create_issue(i, parent_id=parent_id)
