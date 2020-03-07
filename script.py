import datetime
import json
import os
import re
import sys
import traceback
from getpass import getpass

import pytz
import requests
from ics import Calendar, Event, DisplayAlarm
from ics.parse import ContentLine
from lxml import etree


class ScheduleGenerator:
    semester = ''
    first_day_of_semester = ''
    raw_schedule_json = None
    processed_schedule_json = None
    session = requests.Session()
    class_time = []
    trigger_time = None
    '''
    if trigger time is relative, 
        it means the value of "TRIGGER" attribute of "VALARM"
        will be set as an offset to the begin time of next class.
    if trigger time is NOT relative, 
        it means the value of "TRIGGER" attribute of "VALARM"
        will be set as an absolute time, indicating the end time of previous class.
    '''
    is_relative_trigger_time = True
    is_reminder_needed = True
    calender = Calendar()

    def login(self):
        username = input('Please input username: ')
        password = getpass('Password(would not be shown on screen): ')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/80.0.3987.114 Safari/537.36 '
        }
        url = "http://ehall.szu.edu.cn/appShow?appId=4770397878132218"
        try:
            print('Fetching login page...')
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            login_url = response.url
            response = response.text
        except Exception as inst:
            print(inst)
            print("Failed to pick up detail in login page.")
            sys.exit(-1)

        response = etree.HTML(response)
        # Get random name-value pair in login page
        gName = response.xpath('//input[@type="hidden"]/@name')
        gValue = response.xpath('//input[@type="hidden"]/@value')
        gPair = {}
        for i in range(len(gName)):
            gPair[gName[i]] = gValue[i]

        data = {
            'username': username,
            'password': password,
            'lt': gPair['lt'],
            'dllt': gPair['dllt'],
            'execution': gPair['execution'],
            '_eventId': gPair['_eventId'],
            'rmShown': gPair['rmShown']
        }

        # Login through Central Authentication Service
        print("Logging in...")
        self.session.post(login_url, headers=headers, data=data)

    def get_schedule_json(self):
        schedule_api_url = 'http://ehall.szu.edu.cn/jwapp/sys/wdkb/modules/xskcb/xskcb.do'
        data = {
            'XNXQDM': self.semester
        }
        print("Fetching schedule data in JSON format...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/72.72.7272.000 Safari/537.36 ', 'Connection': 'keep-alive', 'Pragma': 'no'
                                                                                                               '-cache',
                   'Cache-Control': 'no-cache', 'Accept': 'application/json, text/javascript, */*; q=0.01',
                   'Origin': 'http://ehall.szu.edu.cn', 'X-Requested-With': 'XMLHttpRequest',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Accept-Encoding': 'gzip, '
                                                                                                          'deflate '
                   }
        result = self.session.post(schedule_api_url, data, headers=headers, cookies=self.session.cookies)
        result.raise_for_status()
        self.raw_schedule_json = result.json()

    '''
    Transform JSON response from Ehall to a user-friendly format
    '''

    def process_json(self):
        result = {
            'size': 0,
            'courses': []
        }
        size = self.raw_schedule_json['datas']['xskcb']['totalSize']
        result['size'] = size
        for course in self.raw_schedule_json['datas']['xskcb']['rows']:
            r = re.compile('\\d+')
            week_bound = r.findall(course['ZCMC'])
            item = {
                'name': course['KCM'],
                'classroom': course['JASMC'],
                'instructor': course['SKJS'],
                'begin_class': int(course['KSJC']),
                'end_class': int(course['JSJC']),
                'weekday': int(course['SKXQ']),
                'period': course['ZCMC'],
                'begin_week': int(week_bound[0]),
                'end_week': int(week_bound[1]),
                'week_mask': course['SKZC']
            }
            result['courses'].append(item)
        self.processed_schedule_json = result

    def set_semester(self):
        self.semester = input('Please input semester(e.g. 2019-2020-2): ')

    def set_first_day_of_semester(self):
        date = input('Please set the Monday date of the first week (e.g. 20200302): ')
        self.first_day_of_semester = datetime.datetime.strptime(
            date,
            '%Y%m%d'
        )
        print('First day of semester set as', self.first_day_of_semester.strftime('%Y-%m-%d'))

    def load_class_timetable(self):
        filenames = ['transition_period.json', 'new.json']
        chosen = False
        filename = ''
        while not chosen:
            choice = int(input(
                'Please choose a suitable class timetable:\n'
                '[0] Transition period timetable(applicable in 2019-2020-2 semester)\n'
                '[1] New timetable(applicable after 2019-2020-2 semester)\n'
            ))
            if choice in [0, 1]:
                filename = filenames[choice]
                chosen = True
            else:
                print('Wrong input, please try again.')
        path = os.getcwd().replace(os.sep, '/') + '/class_timetable/' + filename
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.class_time = data['class']
            print('Load class time successfully')
        except FileNotFoundError:
            print('Load class time failed')
            traceback.print_exc()
            exit(-1)

    '''
    Given a specific week and weekday as an offset,
    construct a date from first_day_of_semester.
    '''

    def _construct_date(self, week, weekday):
        date = self.first_day_of_semester \
               + datetime.timedelta(days=7.0 * (week - 1)) \
               + datetime.timedelta(days=weekday - 1)
        date = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
        return date

    '''
    Construct a string in format "YYYY-mm-ddTHH:mm".
    time_point given in format "HHmm".
    '''

    def _construct_datetime(self, date, time_point: str) -> datetime:
        return date + datetime.timedelta(hours=int(time_point[:2]), minutes=int(time_point[2:]))

    def set_trigger_time(self):
        choice = int(input("Please set the time when reminder appears:\n"
                           "[0] Do not remind\n"
                           "[1] 10 minutes before next class begins\n"
                           "[2] 20 minutes before next class begins\n"
                           "[3] Customize the time before class begins\n"
                           "[4] At the end of previous class\n"
                           ))
        if choice == 0:
            self.is_reminder_needed = False
            self.trigger_time = None
        elif choice == 1:
            # timedelta should be negative value
            self.trigger_time = datetime.timedelta(minutes=-10)
        elif choice == 2:
            self.trigger_time = datetime.timedelta(minutes=-20)
        elif choice == 3:
            value = int(input("Please input the time(in minute):"))
            self.trigger_time = datetime.timedelta(minutes=-value)
        elif choice == 4:
            self.is_relative_trigger_time = False
        else:
            self.is_reminder_needed = False
            print('Reminder time is not set. No reminder will appear.')

    def create_ics(self):
        print('Please wait a moment...')
        self.calender.extra.append(
            ContentLine(name='METHOD', value='PUBLISH')
        )
        for course in self.processed_schedule_json['courses']:
            week = 1
            # begin_week, week and weekday start at 1
            date = self._construct_date(course['begin_week'], course['weekday'])
            end_date = self._construct_date(course['end_week'], course['weekday'])
            while date <= end_date:
                if course['week_mask'][week - 1] == '1':
                    e = Event()
                    e.name = course['name']
                    e.location = course['classroom']
                    e.description = '课程提醒'
                    e.created = datetime.datetime.utcnow()
                    e.begin = self._construct_datetime(date,
                                                       self.class_time[course['begin_class'] - 1]['begin_time'])
                    e.end = self._construct_datetime(date, self.class_time[course['end_class'] - 1]['end_time'])
                    if self.is_reminder_needed:
                        if self.is_relative_trigger_time and self.trigger_time:
                            alarm = DisplayAlarm(trigger=self.trigger_time, display_text='课程提醒')
                        elif not self.is_relative_trigger_time:
                            # set trigger as the end time of *previous* class
                            # For the first class of day, reminder time is at
                            # the night of previous day
                            if course['begin_class'] == 1:
                                trigger_time = self._construct_datetime \
                                    (date - datetime.timedelta(days=1),
                                     self.class_time[course['begin_class'] - 1 - 1]['end_time'])
                            else:
                                trigger_time = self._construct_datetime \
                                    (date,
                                     self.class_time[course['begin_class'] - 1 - 1]['end_time'])
                            alarm = DisplayAlarm(trigger=trigger_time, display_text='课程提醒')
                        e.alarms.append(alarm)
                    self.calender.events.add(e)
                date = date + datetime.timedelta(days=7.0)
                week = week + 1

    def save_ics(self):
        try:
            with open('schedule.ics', 'w', encoding='utf8', newline='') as ics:
                ics.writelines(self.calender)
            print('Save ics file as "schedule.ics" successfully!')
        except:
            print('Save ics file failed: Unexpected error')
            traceback.print_exc()


if __name__ == "__main__":
    schedule_generator = ScheduleGenerator()
    schedule_generator.set_semester()
    schedule_generator.set_first_day_of_semester()
    schedule_generator.load_class_timetable()
    schedule_generator.login()
    schedule_generator.get_schedule_json()
    schedule_generator.process_json()
    schedule_generator.set_trigger_time()
    schedule_generator.create_ics()
    schedule_generator.save_ics()
