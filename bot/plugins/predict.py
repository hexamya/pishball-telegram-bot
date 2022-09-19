import requests
import json
import pytz
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDateTime
from telegram import InlineKeyboardButton
from bot.utils import *
from .utils import *

class Predict:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id
        with open(f'events.json', 'r', encoding="utf-8") as fp:
            self.events = {int(id): event for id, event in json.load(fp).items()}
        with open(f'fixtures.json', 'r', encoding="utf-8") as fp:
            self.fixtures = {int(id): fixture for id, fixture in json.load(fp).items()}
        self.db.set_user(user_id=self.user_id)

    def deadline(self, **kwargs):
        fixture = kwargs.setdefault('fixture', None)
        event = self.fixtures[fixture]['event'] if fixture else kwargs['event']
        now = pytz.timezone("UTC").localize(datetime.utcnow(), is_dst=True)
        deadline_time = pytz.timezone("UTC").localize(datetime.strptime(self.events[event]['deadline_time'], '%Y-%m-%dT%H:%M:%SZ'), is_dst=True)
        over = deadline_time < now
        countdown = deadline_time - now
        deadline_jtime = JalaliDateTime(deadline_time).astimezone(pytz.timezone("Asia/Tehran"))
        deadline_jtime.locale = "fa"
        text = f"🔒 <b>آخرین مهلت ثبت پیش بینی:</b>\n{deadline_jtime.strftime('%A %d %B ساعت %H:%M')}\n⏳ <b>زمان باقی مانده:</b>\n{persianize(countdown.days)} روز {persianize(countdown.seconds//3600)} ساعت {persianize(countdown.seconds%3600//60)} دقیقه"
        return {'text': text, 'time': deadline_time, 'over': over}

    def set_predict(self, fixture, team_h_score, team_a_score):
        if (not self.deadline(fixture=fixture)['over']):
            self.db.set_predict(self.user_id, fixture, team_h_score, team_a_score)
            return {'error': None}
        else:
            return {'error': 'deadline is over'}

    def remove_predict(self, fixture):
        if not self.deadline(fixture=fixture)['over']:
            self.db.remove_predict(self.user_id, fixture)
            return {'error': None}
        else:
            return {'error': 'deadline is over'}
    
    def get_points(self):
        for event in self.events.values():
            if event['is_current']:
                active_event = event['id']
                break
            
        none = lambda x : x if x else '-'
        informations = self.db.get_informations(self.user_id)
        text = persianize(f"🏆 <b>مسابقات پیشبال</b>\n\n🎯 <b>امتیاز کل</b>: {none(informations['total_points'])}\n🎖 <b>‌رتبه‌ی کل</b>: {none(informations['overall_rank'])}\n\n✖️ <b>عملکرد هفتگی</b>:\n" + '\n'.join([f"هفته‌ی {num2fa[id]}:\n🎯 <b>امتیاز</b>: {none(informations['events'][id]['points'])} 🎖 <b>رتبه</b>: {none(informations['events'][id]['rank'])}" for id in range(1,active_event+1)]) + f"\n\n👥 <b>شرکت کنندگان:</b> {none(informations['total_users'])}")
        
        return text
        
    def get_fixture(self, fixture_id, team_h=None, team_a=None, fixture=None, submit=None):
        if submit==True:
            if team_h!=None and team_a!=None:
                ok = self.set_predict(fixture_id, team_h, team_a)
                result = {'answer': 'پیش بینی شما با موفقیت ثبت شد!' if ok else ok}
            else:
                result = {'answer': 'لطفا ابتدا تعداد گل هر تیم را انتخاب کنید.'}
        elif submit==False:
            ok = self.remove_predict(fixture_id)
            result = {'answer': 'پیش بینی شما حذف شد!' if ok else ok}
        elif submit=='help':
            result = {'answer': 'برای ثبت پیش بینی تعداد گل هر تیم را انتخاب و در پایان دکمه سبز ثبت را بزنید.'}
        else:
            result = {'answer': None}
        if (submit in [True, False]) or (not fixture):
            fixture = self.fixtures[int(fixture_id)]
            informations = self.db.get_informations(self.user_id)
            top_predicts = self.db.get_top_predicts()
            event_fixtures = [f['id'] for f in self.fixtures.values()]
            fixture = {
                'id': fixture['id'],
                'event': fixture['event'],
                'team_h': fixture['team_h'],
                'team_h_difficulty': fdrcolor[fixture['team_h_difficulty']],
                'team_a': fixture['team_a'],
                'team_a_difficulty': fdrcolor[fixture['team_a_difficulty']],
                'kickoff_time': fixture['kickoff_time'],
                'finished': fixture['finished_provisional'],
                'deadline': self.deadline(fixture=fixture['id']),
                'real_result': f"{fixture['team_h_score'] if fixture['team_h_score']!=None else ''} {{}} {fixture['team_a_score'] if fixture['team_a_score']!=None else ''}",
                'prediction': informations['fixtures'][fixture['id']],
                'total_points': informations['total_points'],
                'overall_rank': informations['overall_rank'],
                'event_stats': informations['events'][fixture['event']],
                'scoreboard': f"{id2fa[fixture['team_h']]} {{}} {id2fa[fixture['team_a']]}",
                'next': event_fixtures[index] if (index:=event_fixtures.index(fixture['id'])+1) != len(event_fixtures) else None,
                'prev': event_fixtures[index] if (index:=event_fixtures.index(fixture['id'])-1) != -1 else None
            }
            top_predicts_text = '⬆️ پرتکرارترین پیش‌بینی‌ها:\n' + ('\n'.join([fixture['scoreboard'].format(predict) for predict in top_predicts[fixture['id']]]) if top_predicts[fixture['id']] else 'هیچی')
            jkickoff_time = JalaliDateTime(pytz.timezone("UTC").localize(datetime.strptime(fixture['kickoff_time'], '%Y-%m-%dT%H:%M:%SZ'), is_dst=True)).astimezone(pytz.timezone("Asia/Tehran"))
            jkickoff_time.locale = "fa"
            kickoff_time_text = jkickoff_time.strftime('%A %d %B ساعت %H:%M')
            body = f"\n🔘 پیش بینی بازی\n✖️ هفته‌ی {num2fa[fixture['event']]}\n🏠{fixture['team_h_difficulty']} {fixture['scoreboard'].format(fixture['real_result'].format('-'))} {fixture['team_a_difficulty']}✈️\n🗓 {kickoff_time_text}\n\n{top_predicts_text}\n\n{'🧮 پیش‌بینی شما: '+fixture['scoreboard'].format(fixture['prediction']['predict']) if fixture['prediction']['predict'] else 'شما پیش بینی این بازی را ثبت نکرده‌اید!'}\n"
            points = f"\n{'✅' if fixture['prediction']['details']['result'] else '❌'} نتیجه\n{'✅' if fixture['prediction']['details']['goals_h'] else '❌'} گل زده‌ی میزبان\n{'✅' if fixture['prediction']['details']['goals_a'] else '❌'} گل زده‌ی میهمان\n{'✅' if fixture['prediction']['details']['goal_diff'] else '❌'} تفاضل گل\n🎯 امتیاز شما از این بازی: {fixture['prediction']['points']} امتیاز"
            text = body + (points if fixture['prediction']['points']!=None else fixture['deadline']['text'] if not fixture['deadline']['over'] else '🔓 مهلت ثبت پیش‌بینی به پایان رسیده است.')
            fixture['text'] = persianize(text)
            
        buttons = [[InlineKeyboardButton(f"{id2emo[fixture['team_h']]} تعداد گل {id2fa[fixture['team_h']]}{': '+persianize(team_h) if team_h!= None else ''}", callback_data=('predict', fixture['id'], team_h, team_a, fixture, 'help'))]] + [[InlineKeyboardButton(f"{'✔️' if i==team_h else ''} {persianize(i)}", callback_data=('predict', fixture['id'], i, team_a, fixture, None)) for i in range(0,5)]] + [[InlineKeyboardButton(f"{'✔️' if i==team_h else ''} {persianize(i)}", callback_data=('predict', fixture['id'], i, team_a, fixture, None)) for i in range(5,10)]] + [[InlineKeyboardButton(f"{id2emo[fixture['team_a']]} تعداد گل {id2fa[fixture['team_a']]}{': '+persianize(team_a) if team_a!= None else ''}", callback_data=('predict', fixture['id'], team_h, team_a, fixture, 'help'))]] + [[InlineKeyboardButton(f"{'✔️' if i==team_a else ''} {persianize(i)}", callback_data=('predict', fixture['id'], team_h, i, fixture, None)) for i in range(0,5)]] + [[InlineKeyboardButton(f"{'✔️' if i==team_a else ''} {persianize(i)}", callback_data=('predict', fixture['id'], team_h, i, fixture, None)) for i in range(5,10)],[InlineKeyboardButton('✅ ثبت', callback_data=('predict', fixture['id'], team_h, team_a, fixture, True)), InlineKeyboardButton('❌ حذف', callback_data=('predict', fixture['id'], team_h, team_a, fixture, False))]] if (not fixture['deadline']['over']) else []
        if fixture['prediction']['points']!=None:
            data = {'entry': fixture['id'], 'title': fixture['scoreboard'].format(fixture['real_result'].format('-'))}
            buttons += [[InlineKeyboardButton("🔝 بهترین پیش‌بینی‌های این بازی 🔝",callback_data=('fixture_table', 0, data))]]
        buttons += [[InlineKeyboardButton('بازی قبلی ⬅️', callback_data=('predict', fixture['prev'], None, None, None, None)),InlineKeyboardButton('🔙 بازگشت', callback_data=('move', 'this', fixture['event'])),InlineKeyboardButton('➡️ بازی بعدی', callback_data=('predict', fixture['next'], None, None, None, None))]]
        result.update({'buttons': buttons, 'fixture': fixture})
        return result

    def get_fixtures(self, active_event=None):
        if active_event:
            active_event = self.events[int(active_event)]
        else:
            for event in self.events.values():
                if (event['is_current'] and not event['finished']) or event['is_next']:
                    active_event = event
                    break
        texts = []
        buttons = []
        informations = self.db.get_informations(self.user_id)
        for id in [*range(active_event['id'],39),*range(1,active_event['id'])]:
            event_fixtures = [fixture for fixture in self.fixtures.values() if fixture['event'] == id]
            events_buttons = []
            for fixture in event_fixtures:
                predict = informations['fixtures'][fixture['id']]['predict']
                team_h = f"{id2emo[fixture['team_h']]} {id2fa[fixture['team_h']]} {fixture['team_h_score'] if fixture['team_h_score']!=None else ''}"
                team_a = f"{fixture['team_a_score'] if fixture['team_a_score']!=None else ''} {id2fa[fixture['team_a']]} {id2emo[fixture['team_a']]}"
                events_buttons.append([InlineKeyboardButton(persianize(f"{team_h} ({predict if predict else ' - '}) {team_a}"), callback_data=('predict', fixture['id'], None, None, None, None))])
            none = lambda x : x if x else '-'
            deadline = self.deadline(event=id)
            texts.append(persianize(f"🏆 <b>پیش بینی مسابقات لیگ برتر</b>\n\n🎯 <b>امتیاز</b> | کل: {none(informations['total_points'])} هفته: {none(informations['events'][id]['points'])}\n🎖 <b>رتبه</b> | کل: {none(informations['overall_rank'])} هفته: {none(informations['events'][id]['rank'])}\n👥 <b>شرکت کنندگان:</b> {none(informations['total_users'])}\n\n🔘 <b>هفته‌‌ی {num2fa[id]}:</b>\n{deadline['text'] if not deadline['over'] else '🔓 مهلت ثبت پیش‌بینی به پایان رسیده است!'}"))
            if deadline['over']:
                data = {'entry': id}
                events_buttons.append([InlineKeyboardButton("🎖 بهترین‌های این هفته 🎖",callback_data=('event_table', 0, data))])
            events_buttons.append([InlineKeyboardButton('هفته‌ی قبلی ⬅️', callback_data=('move', 'prev', active_event['id'])), InlineKeyboardButton('➡️ هفته‌ی بعدی', callback_data=('move', 'next', active_event['id']))])
            buttons.append(events_buttons)
        return {'texts': texts, 'buttons': buttons}
        
    def get_table(self, page=0):
        informations = self.db.get_all_stats()
        users = self.db.get_all_users()['users']
        informations = {k : v for k, v in informations.items() if v['total_points']!=None}
        table = [v | {'name': c_html(users[k]['name']), 'username': users[k]['username']} for k, v in sorted(informations.items(), key= lambda item : item[1]['total_points'], reverse=True)]
        table_text = [f"{'------------------------------'+chr(10) if user['user_id']==self.user_id else ''}#{user['overall_rank']:02} | {user['total_points']:02} | <b>{user['name'] if user['name']!='None' else user['user_id']}</b>{chr(10)+'------------------------------' if user['user_id']==self.user_id else ''}" for user in table]
        pages = len(table)//25+1
        result = ['🏆 <b>جدول فصل لیگ پیشبال:</b>\n\n'+'\n'.join(table_text[x:x+25])+f'\n\n<b>[صفحه‌ی {i+1}/{pages}]</b>' for i,x in enumerate(range(0, len(table), 25))]
        if page == 'me':
            page = [result_page for result_page, result_text in enumerate(result) if '------------------------------' in result_text]
            page = page[0] if page else 0

        return {'page': page, 'pages': pages, 'text': result[page]}
        
    def get_event_table(self, data, page=0):
        event = data['entry']
        informations = self.db.get_all_stats()
        users = self.db.get_all_users()['users']
        informations = {k : {'user_id': k} | v['events'][event] for k, v in informations.items() if v['events'][event]['points']!=None}
        table = [v | {'name': c_html(users[k]['name']), 'username': users[k]['username']} for k, v in sorted(informations.items(), key= lambda item : item[1]['rank'])]
        table_text = [f"{'------------------------------'+chr(10) if user['user_id']==self.user_id else ''}#{user['rank']:02} | {user['points']:02} | <b>{user['name'] if user['name']!='None' else user['user_id']}</b>{chr(10)+'------------------------------' if user['user_id']==self.user_id else ''}" for user in table]
        pages = data['pages'] = len(table)//25+1
        result = [f'🏅 <b>جدول هفته‌ی {num2fa[event]} لیگ پیشبال:</b>\n\n'+'\n'.join(table_text[x:x+25])+f'\n\n<b>[صفحه‌ی {i+1}/{pages}]</b>' for i,x in enumerate(range(0, len(table), 25))]
        if page == 'me':
            me = True
            page = [result_page for result_page, result_text in enumerate(result) if '------------------------------' in result_text]
            page = page[0] if page else 0
        else:
            me = False
        
        buttons = [[InlineKeyboardButton('<<<', callback_data=('event_table', page-1 if page !=0 else pages-1, data)), InlineKeyboardButton('جایگاه من' if not me else 'نفرات برتر', callback_data=('event_table', 0 if me else 'me', data)),InlineKeyboardButton('>>>', callback_data=('event_table', page+1 if page+1!=pages else 0, data))],[InlineKeyboardButton('🔙 بازگشت', callback_data=('move', 'this', event))]]
        
        return {'page': page, 'pages': pages, 'text': result[page], 'buttons': buttons, 'data': data}
        
    def get_fixture_table(self, data, page=0):
        fixture = data['entry']
        title = data['title']
        informations = self.db.get_all_informations()
        users = self.db.get_all_users()['users']
        informations = {k : v['fixtures'][fixture] for k, v in informations.items() if v['fixtures'][fixture]['predict']!=None}
        table = [v | {'user_id': k,'name': c_html(users[k]['name']), 'username': users[k]['username']} for k, v in sorted(informations.items(), key= lambda item : item[1]['points'], reverse=True)]
        table_text = [f"{'--------------------'+chr(10) if user['user_id']==self.user_id else ''}#{index+1:02} | {user['predict']} | {user['points']:02} | <b>{user['name'] if user['name']!='None' else user['user_id']}</b>{chr(10)+'--------------------' if user['user_id']==self.user_id else ''}" for index,user in enumerate(table)]
        pages = len(table)//25+1
        result = [f'🔘 {title}\n🏆 <b>بهترین پیش‌بینی‌های بازی:</b>\n\n'+'\n'.join(table_text[x:x+25])+f'\n\n<b>[صفحه‌ی {i+1}/{pages}]</b>' for i,x in enumerate(range(0, len(table), 25))]
        if page == 'me':
            me = True
            page = [result_page for result_page, result_text in enumerate(result) if '------------------------------' in result_text]
            page = page[0] if page else 0
        else:
            me = False

        buttons = [[InlineKeyboardButton('<<<', callback_data=('fixture_table', page-1 if page !=0 else pages-1, data)), InlineKeyboardButton('جایگاه من' if not me else 'نفرات برتر', callback_data=('fixture_table', 0 if me else 'me', data)),InlineKeyboardButton('>>>', callback_data=('fixture_table', page+1 if page+1!=pages else 0, data))],[InlineKeyboardButton('🔙 بازگشت', callback_data=('predict', data['entry'], None, None, None, None))]]
        
        return {'page': page, 'pages': pages, 'text': result[page], 'buttons': buttons, 'data': data}
