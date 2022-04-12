import vk_config
from schedule import Schedule
from vk_api.vk_api import VkApi
from vk_api.utils import get_random_id

def vk_notifier(cat, dates, notify_subscribers=[]):
    res = False
    vk_session = VkApi(token=vk_config.access_token, version=vk_config.api_version)
    for elem in notify_subscribers:
        peer_id = elem['peer_id']
        name = elem['name']
        for date in dates:
            schedule = Schedule.get_schedule(cat, name, date)
            if schedule:
                vk_session.method('messages.send', {'random_id': get_random_id(), 'message': Schedule.named_schedule_to_string(schedule), 'peer_id': peer_id, })
                res = True
    return True if res else False