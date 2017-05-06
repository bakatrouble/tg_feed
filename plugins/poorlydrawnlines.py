import requests

from message_types import PhotoMessage


def get_updates(last_id):
    result = []
    media: list = requests.get('http://www.poorlydrawnlines.com/wp-json/wp/v2/media').json()
    for m in reversed(media):
        if m['id'] > last_id:
            result.append(PhotoMessage(m['title']['rendered'],
                                       requests.get(m['source_url']).content))
            last_id = m['id']
    return last_id, result
