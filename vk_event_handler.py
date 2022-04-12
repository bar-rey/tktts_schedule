import vk_config
from vk_api.vk_api import VkApi
from vk_api.utils import get_random_id
from vk_notifier import vk_notifier
from datetime import date
from schedule import Schedule

class VkEventHandler():
    def __init__(self, event, dbase):
        self.name = "иска"
        self.dbase = dbase
        self.event = event
        self.secret_key = vk_config.secret_key
        self.confirmation_token = vk_config.confirmation_token
        self.vk_session = VkApi(token=vk_config.access_token, version=vk_config.api_version)
        self.conversation_commands = {"расписание", "подписать", "отписаться", "помощь"}
        self.personal_commands = {"расписание", "рассылка", "помощь"}

    def __message_send(self, text, peer_id):
        self.vk_session.method('messages.send', {'random_id':get_random_id(), 'message':text, 'peer_id': peer_id, })

    def __get_named_schedule(self, name, date):
        raw_schedule = Schedule.get_schedule("groups", name, date)
        return Schedule.named_schedule_to_string(raw_schedule)

    def __get_subscribed_name_by_peer_id(self, peer_id):
        name = ""
        subs = self.dbase.getSubscribers()
        if subs:
            for sub in subs:
                if sub["peer_id"] == peer_id: name = sub["name"]
        return name if name else None

    def __get_schedule_answer(self, name, date):
        schedule = self.__get_named_schedule(name, date)
        return schedule if schedule else f"Расписание для '{name}' на {date} не найдено"

    def __get_add_schedule_answer(self, url):
        res = Schedule.add_schedule(url, vk_notify_subscribers=self.dbase.getSubscribers())
        if res: return "Расписание успешно добавлено"
        elif res is None: return "Неправильная ссылка"
        else: return "Что-то пошло не так"

    def __get_groups_notify_answer(self, date):
        subs = self.dbase.getSubscribers()
        if subs:
            return f"Рассылка расписания за {date} проведена успешно" \
            if vk_notifier("groups", {date,}, subs) else "Рассылка не удалась"
        else:
            return "Никто не подписан на рассылку"

    def __get_subscribe_answer(self, peer_id, name):
        if self.dbase.addSubscriber(peer_id, name):
            return f"Данная беседа теперь подписана на рассылку о расписании '{name}'"
        else:
            return "Данная беседа уже подписана на рассылку расписания"

    def __get_unsubscribe_answer(self, peer_id):
        if self.dbase.removeSubscriber(peer_id):
            return "Данная беседа больше не подписана на рассылку расписания"
        else:
            return "Данная беседа не была подписана на рассылку расписания"

    def create_answer(self):
        if 'secret' not in self.event.keys():
            return 'not vk'
        if self.event['secret'] != self.secret_key:
            return 'access denied'
        if self.event['type'] == 'confirmation':
            return self.confirmation_token
        elif self.event['type'] == 'message_new':
            peer_id = self.event["object"]["peer_id"]
            text_words = self.event["object"]["text"].strip().split(" ")
            if text_words:
                message_from_conversation = peer_id - 2000000000 >= 0
                if message_from_conversation:
                    if text_words[0].lower() == self.name.lower() and len(text_words) >= 2:
                        command = text_words[1]
                        if command in self.conversation_commands:
                            if command == "расписание":
                                name = self.__get_subscribed_name_by_peer_id(peer_id)
                                if name:
                                    if len(text_words)==2 or (len(text_words)==3 and text_words[2]=="сегодня"):
                                        self.__message_send(self.__get_schedule_answer(name, Schedule.date_to_string_converter(date.today())), peer_id)
                                    elif len(text_words)==3:
                                        self.__message_send(self.__get_schedule_answer(name, date=text_words[2]), peer_id)
                                else:
                                    self.__message_send("Необходимо привязать название вашей группы к беседе", peer_id)
                            elif command == "подписать":
                                if len(text_words) == 3:
                                    self.__message_send(self.__get_subscribe_answer(peer_id, name=text_words[2]), peer_id)
                                else:
                                    self.__message_send("Не указано название группы", peer_id)
                            elif command == "отписаться":
                                self.__message_send(self.__get_unsubscribe_answer(peer_id), peer_id)
                            elif command == "помощь":
                                self.__message_send("Обращаясь к боту, необходимо указывать его имя ({0}).\n\
Доступные команды (угловые скобки необходимо опустить):\n\
подписать <группа> <-- подписать вашу беседу на получение расписания какой-либо группы,\n\
отписаться <-- отписаться от получения расписания,\n\
расписание <-- получить расписание подписанной группы, датируемое сегодняшним днём,\n\
расписание <сегодня> <-- получить расписание подписанной группы, датируемое сегодняшним днём,\n\
расписание <дата (дд.мм.гггг)> <-- получить расписание подписанной группы за определённую дату.".format(self.name), peer_id)
                else:
                    user = self.dbase.getUserByVkId(peer_id)
                    if user and user['role'] in {'moderator', 'administrator'}:
                        command = text_words[0]
                        if command in self.personal_commands:
                            if command == "расписание":
                                if len(text_words) == 2:
                                    self.__message_send(self.__get_add_schedule_answer(url=text_words[1]), peer_id)
                                else:
                                    self.__message_send("Отсутствует ссылка на расписание", peer_id)
                            elif command == "рассылка":
                                if len(text_words)==1 or (len(text_words)==2 and text_words[1]=="сегодня"):
                                    self.__message_send(self.__get_groups_notify_answer(Schedule.date_to_string_converter(date.today())), peer_id)
                                elif len(text_words)==2:
                                    self.__message_send(self.__get_groups_notify_answer(date=text_words[1]), peer_id)
                            elif command == "помощь":
                                self.__message_send("Доступные команды (угловые скобки необходимо опустить):\n\
расписание <ссылка на гугл документ> <-- добавить расписание,\n\
рассылка <-- рассылка расписания, датируемого сегодняшним днём,\n\
рассылка <сегодня> <-- рассылка расписания, датируемого сегодняшним днём,\n\
рассылка <дата (дд.мм.гггг)> <-- рассылка расписания за определённую дату.", peer_id)
        return 'ok'