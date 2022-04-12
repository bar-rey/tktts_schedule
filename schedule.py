import requests
import csv
import json
import os
import datetime

class Schedule:
    # основная директория
    main_directory = "static/schedule/"
    # каталоги для расписаний и списков
    schedules_catalogue = "schedules/"
    lists_catalogue = "lists/"
    # название преподавателей и групп
    teachers_name = "teachers"
    groups_name = "groups"
    # названия листов электронной таблицы
    teachers_sheet_name="преподаватели"
    groups_sheet_name="группы"
    # директории преподавателей
    teachers_directory = main_directory + "teachers/"
    teachers_schedules_directory = teachers_directory + schedules_catalogue
    teachers_lists_directory = teachers_directory + lists_catalogue
    # директории групп
    groups_directory = main_directory + "groups/"
    groups_schedules_directory = groups_directory + schedules_catalogue
    groups_lists_directory = groups_directory + lists_catalogue
    
    @staticmethod
    def get_spreadsheet_id(url):
        '''
        поиск идентификатора электронной таблицы;
        пример: https://docs.google.com/spreadsheets/d/ИДЕНТИФИКАТОР/чтоугодно.../
        '''
        id = ""
        f = False
        for i in url.split("/"):
            if f: 
                id = i
                break
            if i == "d": f = True
        return id

    @staticmethod
    def download_page(url, path):
        '''
        сохранение любой веб-страницы
        '''
        with open(path, mode="wb") as f:
            f.write(requests.get(url).content)

    @staticmethod
    def download_spreadsheet(url, sheets, format, directory=""):
        '''
        загрузка электронной таблицы;
        пример: https://docs.google.com/spreadsheets/d/ИДЕНТИФИКАТОР/gviz/tq?tqx=out:ФОРМАТ&sheet=ЛИСТ
        '''
        id = Schedule.get_spreadsheet_id(url)
        paths={}
        for sheet in sheets:
            path=f"{directory}{sheet}.{format}"
            paths[sheet] = path
            Schedule.download_page(url=f"https://docs.google.com/spreadsheets/d/{id}/gviz/tq?tqx=out:{format}&sheet={sheet}", path=path)
        return paths
        
    @staticmethod
    def read_csv(path):
        '''
        чтение csv файла
        '''
        with open(path, mode="r", encoding="utf-8") as f:
            return tuple([row for row in csv.reader(f, delimiter=",", quotechar='"')])
    
    @staticmethod
    def fix_teacher_schedule(schedule):
        ''' 
        исправление расписания преподавателей; 
        первый столбец в листе "преподаватели" имеет некорректный формат
        '''
        schedule[0].pop(0)
        schedule[0].insert(0, "дата")
        schedule[0].insert(1, "день недели")
        schedule[0].insert(2, "номер пары")
        for row in range(1, len(schedule)):
            lst = schedule[row][0].split(" ")
            schedule[row].pop(0)
            schedule[row].insert(0, lst[0])
            schedule[row].insert(1, lst[2])
            schedule[row].insert(2, lst[3])
        return schedule

    @staticmethod
    def find_longest_row(rows):
        ''' поиск самой длинной строки в таблице '''
        longest = -1
        for row in rows:
            length = 0
            for elem in row: 
                if elem == "": break
                length += 1
            if length > longest: longest = length
        return longest
    
    @staticmethod
    def jsonify_schedule(schedule, directory):
        '''
        сохранение расписания групп/преподавателей в формате json;
        сохранение списка групп/преподавателей в формате json
        '''
        number_of_dates = (len(schedule) - 1) / 6 # количество дат в расписании (-заголовки, делить на кол-во пар)
        dates = []
        start_row = 1
        start_column = 3
        end_column = Schedule.find_longest_row(schedule)
        while number_of_dates > 0:
            date = ""
            objects_list = []
            objects_schedule = []
            end_row = start_row + 6
            dates.append(schedule[start_row][0])    # в столбце 0 находится расписание
            for column in range(start_column, end_column):
                obj_name = schedule[0][column]
                objects_list.append(obj_name)
                obj_schedule = []
                for row in range(start_row, end_row):
                    date = schedule[row][0]
                    lesson = "Нет" if schedule[row][column]=="" else schedule[row][column]
                    obj_schedule.append({"date": date, "day": schedule[row][1], "number": schedule[row][2], "lesson": lesson})
                objects_schedule.append({"name": obj_name, "schedule": obj_schedule})
            with open(f"{directory}{Schedule.schedules_catalogue}{date}.json", mode="w", encoding="utf-8") as f:     # расписание преподавателей (или групп)
                json.dump(objects_schedule, f, ensure_ascii=False, indent=4)
            with open(f"{directory}{Schedule.lists_catalogue}{date}.json", mode="w", encoding="utf-8") as f:   # список преподавателей (или групп)
                json.dump(objects_list, f, ensure_ascii=False, indent=4)
            number_of_dates -= 1
            start_row += 6
        return dates if dates else None

    @staticmethod
    def named_schedule_to_string(raw_schedule):
        '''
        преобразование расписания из get_named_schedule в читаемый вид
        '''
        if raw_schedule:
            res_schedule = f"{raw_schedule[0]['date']}, {raw_schedule[0]['day']}"
            for obj in raw_schedule:
                res_schedule += f"\n{obj['number']}. {obj['lesson']}"
            return res_schedule
        return None

    @staticmethod
    def add_schedule(url):
        '''
        добавление расписания
        '''
        if (url.startswith("https://docs.google.com/spreadsheets/d/") or url.startswith("http://docs.google.com/spreadsheets/d/")) and requests.get(url).status_code == 200:
            # загрузка электронной таблицы
            paths=Schedule.download_spreadsheet(url, (Schedule.teachers_sheet_name, Schedule.groups_sheet_name), "csv", Schedule.main_directory)
            # лист преподавателей
            read_schedule = Schedule.read_csv(paths[Schedule.teachers_sheet_name])
            Schedule.jsonify_schedule(schedule=Schedule.fix_teacher_schedule(read_schedule), directory=Schedule.teachers_directory)
            # лист групп
            read_schedule = Schedule.read_csv(path=paths[Schedule.groups_sheet_name])
            Schedule.jsonify_schedule(schedule=read_schedule, directory=Schedule.groups_directory)
            return True
        return None

    @staticmethod
    def load_json(path):
        '''
        чтение файла json
        '''
        if os.path.exists(path):
            with open(path, mode="r", encoding="utf-8") as json_file:
                return json.load(json_file)
        return None

    @staticmethod
    def get_named_schedule(full_schedule, name):   # name - преподаватель или группа
        '''
        получить расписание определённой группы/преподавателя из общего расписания
        '''
        if full_schedule:
            name = name.lower()
            schedule = []
            for s in full_schedule:
                if s['name'].lower() == name:
                    schedule=s["schedule"]
                    break
            if schedule: return schedule
        return None

    @staticmethod
    def date_to_string_converter(date):
        '''
        преобразования объекта класса date в строку;
        возвращаемая строка имеет формат дд.мм.гггг
        '''
        month = str(date.month)
        if len(month) == 1:
            month = "0" + month
        day = str(date.day)
        if len(day) == 1:
            day = "0" + day
        return f"{day}.{month}.{date.year}"

    @staticmethod
    def get_schedule(cat, name, date):
        '''
        получение расписания группы/групп/преподавателя/преподавателей за определённую дату
        '''
        if cat==Schedule.teachers_name: path=f"{Schedule.teachers_schedules_directory}{date}.json"
        elif cat==Schedule.groups_name: path=f"{Schedule.groups_schedules_directory}{date}.json"
        else: path=""
        if path!="":
            res=Schedule.load_json(path) if name=="all" else Schedule.get_named_schedule(Schedule.load_json(path), name)
            if res: return res
        return None

    @staticmethod
    def list_dir(directory, cut_format=True):
        '''
        список файлов в директории;
        удаление формата файлов
        '''
        if os.path.exists(directory):
            lst=os.listdir(directory)
            if cut_format:
                for i in range(len(lst)):
                    lst[i] = lst[i].rsplit('.', 1)[0]
            if lst: return lst
        return None

    @staticmethod
    def get_available_dates():
        '''
        получение дат доступных(датируемых не раньше сегодня) расписаний;
        даты возвращаются в формате дд.мм.гггг
        '''
        dirs = {Schedule.teachers_name: Schedule.teachers_schedules_directory, Schedule.groups_name: Schedule.groups_schedules_directory}
        dates = {}
        for obj, dir in dirs.items():
            rdates = Schedule.list_dir(dir)
            if rdates:
                fdates = []
                for rdate in rdates:
                    tmp = rdate.split(".")
                    day = tmp[0]
                    if day[0] == "0": day = day[1]
                    day = int(day)
                    month = int(tmp[1])
                    year = int(tmp[2])
                    schedule_date = datetime.date(year, month, day)
                    current_date = datetime.date.today()
                    if schedule_date >= current_date: fdates.append(rdate)
                dates[obj] = fdates if fdates else None
            else: dates[obj] = None
        return dates

    @staticmethod
    def get_list(cat, date=""):
        '''
        получение списка преподавателей/групп
        '''
        if date and date!="":
            if cat==Schedule.teachers_name: path=f"{Schedule.teachers_lists_directory}{date}.json"
            elif cat==Schedule.groups_name: path=f"{Schedule.groups_lists_directory}{date}.json"
            else: path=""
            if path!="":
                res = Schedule.load_json(path=path)
                if res: return res
        return None

if __name__ == "__main__":
    pass