# from evernote.edam.userstore import EDAM_VERSION_MAJOR, EDAM_VERSION_MINOR


CONSUMER_KEY = 'nvbn-1422'
CONSUMER_SECRET = 'c17c0979d0054310'
HOST = 'www.evernote.com'

STATUS_NONE = 0
STATUS_SYNC = 1
STATUS_RATE = 3  # Rate Limit status

DEFAULT_SYNC_DELAY = 30000 * 60
SYNC_STATE_START = 0
SYNC_STATE_NOTEBOOKS_LOCAL = 1
SYNC_STATE_TAGS_LOCAL = 2
SYNC_STATE_NOTES_LOCAL = 3
SYNC_STATE_NOTEBOOKS_REMOTE = 4
SYNC_STATE_TAGS_REMOTE = 5
SYNC_STATE_NOTES_REMOTE = 6
SYNC_STATE_SHARE = 7
SYNC_STATE_STOP_SHARE = 8
SYNC_STATE_FINISH = 9
SYNC_STATE_RATE_LIMITED  = 10
SYNC_MANUAL = -1
SYNC_STATES = (
    SYNC_STATE_START, SYNC_STATE_NOTEBOOKS_LOCAL,
    SYNC_STATE_TAGS_LOCAL, SYNC_STATE_NOTES_LOCAL,
    SYNC_STATE_NOTEBOOKS_REMOTE, SYNC_STATE_TAGS_REMOTE,
    SYNC_STATE_NOTES_REMOTE, SYNC_STATE_FINISH, SYNC_STATE_RATE_LIMITED,
)
DEFAULT_FONT = 'Sans'
DEFAULT_FONT_SIZE = 14
DEFAULT_INDICATOR_LAYOUT = [
    'create_note', 'pin_notes', 'notes', 'all_notes', 'sync',
]

# EDAM_VERSION = EDAM_VERSION_MAJOR + "." + EDAM_VERSION_MINOR
SCHEMA_VERSION = 5
API_VERSION = 6
VERSION = '2.5'
DB_PATH = "~/.everpad/everpad.%s.db" % SCHEMA_VERSION

ACTION_NONE = 0
ACTION_CREATE = 1
ACTION_DELETE = 2
ACTION_CHANGE = 3
ACTION_NOEXSIST = 4
ACTION_CONFLICT = 5
ACTION_DUPLICATE = 6

DISABLED_ACTIONS = (ACTION_DELETE, ACTION_NOEXSIST, ACTION_CONFLICT)

SHARE_NONE = 0
SHARE_NEED_SHARE = 1
SHARE_SHARED = 2
SHARE_NEED_STOP = 3

NONE_ID = 0
NONE_VAL = 0

ORDER_TITLE = 0
ORDER_UPDATED = 1
ORDER_TITLE_DESC = 2
ORDER_UPDATED_DESC = 3

DEFAULT_LIMIT = 100
NOT_PINNDED = -1
