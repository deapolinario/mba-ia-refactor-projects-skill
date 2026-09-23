from datetime import datetime, timezone
import re
import uuid
from config import Config

# v2.2: VALID_STATUSES/VALID_ROLES removidos daqui — centralizados em
# Config.VALID_TASK_STATUSES/Config.VALID_ROLES (eram definidos aqui mas
# nunca importados; código duplicava as listas hardcoded em outros arquivos)
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'

def utcnow():
    """Substitui datetime.utcnow() (deprecated desde Python 3.12). Retorna
    datetime 'naive' (sem tzinfo) de propósito: as colunas db.DateTime e os
    valores de due_date parseados por parse_date() também são naive, então
    devolver um aware aqui quebraria comparações (`due_date < utcnow()`)
    com TypeError. O valor continua sendo UTC — só sem o tzinfo explícito."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None

def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email))

def sanitize_string(s):
    if s:
        return s.strip()
    return s

def generate_id():
    return str(uuid.uuid4())

def log_action(action, details=None):
    timestamp = utcnow()
    print(f"[{timestamp}] ACTION: {action}")
    if details:
        print(f"  DETAILS: {details}")

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_string, '%d/%m/%Y')
        except ValueError:
            return None

def is_valid_color(color):
    return bool(color) and len(color) == 7 and color[0] == '#'

def process_task_data(data, existing_task=None):
    result = {}

    if 'title' in data:
        title = data['title']
        if title:
            title = title.strip()
            if MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH:
                result['title'] = title
            else:
                return None, f'Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres'
        else:
            return None, 'Título não pode ser vazio'

    if 'description' in data:
        result['description'] = data['description']

    if 'status' in data:
        if data['status'] in Config.VALID_TASK_STATUSES:
            result['status'] = data['status']
        else:
            return None, 'Status inválido'

    if 'priority' in data:
        try:
            p = int(data['priority'])
        except (ValueError, TypeError):
            return None, 'Prioridade inválida'
        if Config.MIN_PRIORITY <= p <= Config.MAX_PRIORITY:
            result['priority'] = p
        else:
            return None, f'Prioridade deve ser entre {Config.MIN_PRIORITY} e {Config.MAX_PRIORITY}'

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if parsed:
                result['due_date'] = parsed
            else:
                return None, 'Data inválida'
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        if type(tags) == list:
            result['tags'] = ','.join(tags)
        else:
            result['tags'] = tags

    return result, None
