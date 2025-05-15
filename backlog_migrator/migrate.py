from backlog_migrator.utils.helpers import print_banner
from backlog_migrator.api.issues import migrate_issues

def migrate_all():
    print_banner()
    migrate_issues()
