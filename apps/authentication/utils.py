import hashlib
import uuid


def create_tracking_code_with_uuid():
    encoded_text = str(uuid.uuid4()).encode('utf-8')
    md5_hash = hashlib.md5(encoded_text).hexdigest()
    return md5_hash[:15]
