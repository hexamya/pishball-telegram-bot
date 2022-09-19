from bot.utils.urls import *

import sqlite3
import json
import requests

class Database:
    def __init__(self):
        connection = sqlite3.connect('bot.db', check_same_thread=False)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, name TEXT, username TEXT);")
        cursor.execute("CREATE TABLE IF NOT EXISTS groups(chat_id INTEGER PRIMARY KEY, chat_title TEXT);")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS stats(user_id INTEGER PRIMARY KEY, total_points TEXT, overall_rank TEXT, {', '.join([f'event_{i}_points TEXT, event_{i}_rank TEXT' for i in range(1,39)])});")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS predicts(user_id INTEGER PRIMARY KEY, {', '.join([f'fixture_{i} TEXT' for i in range(1,381)])});")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS points(user_id INTEGER PRIMARY KEY, {', '.join([f'fixture_{i} TEXT' for i in range(1,381)])});")
        connection.commit()
        self.connection = connection

    def set_user(self, **kwargs):
        user_id=kwargs.setdefault('user_id', None)
        name=kwargs.setdefault('name', None)
        username=kwargs.setdefault('username', None)
        name = name.replace("'", "''") if name else None
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"INSERT INTO users(user_id, name, username) VALUES('{user_id}', '{name}', '{username}');")
            cursor.execute(f"INSERT INTO stats(user_id) VALUES('{user_id}');")
            cursor.execute(f"INSERT INTO predicts(user_id) VALUES('{user_id}');")
            cursor.execute(f"INSERT INTO points(user_id) VALUES('{user_id}');")
        except sqlite3.IntegrityError:
            if name and username:
                cursor = self.connection.cursor()
                cursor.execute(f"UPDATE users SET name = '{name}', username = '{username}' WHERE user_id = '{user_id}';")
        finally:
            self.connection.commit()
        
    def set_group(self, chat_id, chat_title):
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"INSERT INTO groups VALUES(?,?);", (chat_id, chat_title))
        except sqlite3.IntegrityError:
            cursor = self.connection.cursor()
            cursor.execute(f"UPDATE groups SET chat_title = '{chat_title}' WHERE chat_id = '{chat_id}';")
        finally:
            self.connection.commit()

    def get_user(self, **kwargs):
        cursor = self.connection.cursor()
        key = next(iter(kwargs))
        value = kwargs[key]
        cursor.execute(f"SELECT * FROM users WHERE {key} = '{value}' COLLATE NOCASE;")
        try:
            user_id, name, username = cursor.fetchone()
            user = {'user_id': user_id, 'name': name, 'username': username}
        except:
            user = None
        finally:
            return user
        
    def get_all_users(self):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM users;")
        try:
            users = cursor.fetchall()
            result = {'users': {}, 'total': len(users)}
            for user in users:
                user_id, name, username = user
                result['users'].update({user_id: {'user_id': user_id, 'name': name, 'username': username}})
        except:
            result = None
        finally:
            return result

    def get_all_groups(self):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM groups;")
        try:
            groups = cursor.fetchall()
            result = {'groups': {}, 'total': len(groups)}
            for group in groups:
                chat_id, chat_title = group
                result['groups'].update({chat_id: {'chat_id': chat_id, 'chat_title': chat_title}})
        except:
            result = None
        finally:
            return result

    def set_predict(self, user_id, fixture, team_h_score, team_a_score):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"UPDATE predicts SET fixture_{fixture} = '{team_h_score}-{team_a_score}' WHERE user_id = '{user_id}';")
            result = True
        except:
            result = False
        finally:
            self.connection.commit()
            return result

    def remove_predict(self, user_id, fixture):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"UPDATE predicts SET fixture_{fixture} = NULL WHERE user_id = '{user_id}';")
            result = True
        except:
            result = False
        finally:
            self.connection.commit()
            return result
            
    def get_predict(self):
        pass

    def get_points(self):
        pass
    
    def get_all_predicts(self):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM predicts;")
        try:
            users = cursor.fetchall()
            result = {user[0]: {fixture+1: predict for fixture, predict in enumerate(user[1:])} for user in users}
        except:
            result = None
        finally:
            return result

    def get_top_predicts(self):
        predicts = self.get_all_predicts()
        fixtures_predicts = {fixture: [user[fixture] for user in predicts.values() if user[fixture]] for fixture in range(1,381)}
        top_predicts = {fixture: sorted(set(predicts), key = lambda predict: predicts.count(predict), reverse=True)[:3] for fixture, predicts in fixtures_predicts.items()}
        return top_predicts
        
    def get_all_stats(self):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM stats;")
        none = lambda row : int(row) if row!=None else row
        try:
            users = cursor.fetchall()
            result = {user[0]: {'user_id':user[0], 'total_points': none(user[1]), 'overall_rank': none(user[2]), 'events': {event: {'points': none(user[event*2+1]), 'rank': none(user[event*2+2])} for event in range(1,39)}} for user in users}
        except:
            result = None
        finally:
            return result
    
    def get_informations(self, user_id):
        none = lambda row : int(row) if row!=None else row
        predicts = self.get_all_predicts()
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM stats WHERE user_id = '{user_id}';")
        stats = cursor.fetchone()
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM points WHERE user_id = '{user_id}';")
        points = cursor.fetchone()
        try:
            fixtures = points[1:]
            data = {'fixtures': {}, 'total_users': len(predicts) ,'total_points': none(stats[1]), 'overall_rank': none(stats[2]), 'events': {event: {'points': none(stats[event*2+1]), 'rank': none(stats[event*2+2])} for event in range(1,39)}}
            for index, point in enumerate(fixtures):
                fixture = index+1
                if point:
                    point, result, goals_h, goals_a, goal_diff = [int(i) for i in list(point)]
                else:
                    point = result = goals_h = goals_a = goal_diff = None
                fixture_points = {
                    'predict': predicts[user_id][fixture],
                    'points': point,
                    'details': {'result': result, 'goals_h': goals_h, 'goals_a': goals_a, 'goal_diff': goal_diff}
                    }
                data['fixtures'].update({fixture: fixture_points})
        except:
            data = None
        finally:
            return data
            
    def get_all_informations(self):
        cursor = self.connection.cursor()
        predicts = self.get_all_predicts()
        stats = self.get_all_stats()
        cursor.execute(f"SELECT * FROM points;")
        try:
            users = cursor.fetchall()
            data = {}
            for user in users:
                user_id, fixtures = user[0], user[1:]
                data[user_id] = {'fixtures': {}, 'total_users': len(users)}
                for index, points in enumerate(fixtures):
                    fixture = index+1
                    if points:
                        points, result, goals_h, goals_a, goal_diff = [int(i) for i in list(points)]
                    else:
                        points = result = goals_h = goals_a = goal_diff = None
                    fixture_points = {
                        'predict': predicts[user_id][fixture],
                        'points': points,
                        'details': {'result': result, 'goals_h': goals_h, 'goals_a': goals_a, 'goal_diff': goal_diff}
                        }
                    data[user_id]['fixtures'].update({fixture: fixture_points})
                data[user_id].update(stats[user_id])
        except:
            data = None
        finally:
            return data

    def update_data(self):
        predicts = self.get_all_predicts()
        
        fixtures = {fixture['id']: fixture for fixture in requests.get(FIXTURES_URL).json()}
        events = {event['id']: event for event in requests.get(STATIC_URL).json()['events']}
        with open(f'events.json', 'w', encoding="utf-8") as fp:
            json.dump(events, fp, ensure_ascii=False, indent=4)
        with open(f'fixtures.json', 'w', encoding="utf-8") as fp:
            json.dump(fixtures, fp, ensure_ascii=False, indent=4)
        
        active_events = {fixture['event'] for fixture in fixtures.values() if fixture['finished_provisional']}
        users = {}
        for user_id, user_fixtures in predicts.items():
            cursor = self.connection.cursor()
            total_points = 0
            events_points = {event: 0 for event in active_events}
            users[user_id] = {'fixtures': {}}
            for fixture_id, predict in user_fixtures.items():
                fixture = fixtures[fixture_id]
                rh, ra = fixture['team_h_score'], fixture['team_a_score']
                if predict and rh!=None:
                    ph, pa = [int(p) for p in predict.split('-')]
                    result = 3 if (rh-ra) * (ph-pa) > 0 or (rh-ra) == (ph-pa) == 0 else 0
                    goals_h = 1 if rh == ph else 0
                    goals_a = 1 if ra == pa else 0
                    goal_diff = 1 if rh-ra == ph-pa else 0
                    points = result+goals_h+goals_a+goal_diff
                    points_details = f"'{points}{result}{goals_h}{goals_a}{goal_diff}'"
                    total_points += points
                    if (event:=fixture['event']) in events_points.keys():
                        events_points[event] += points
                elif rh!=None:
                    points_details = "'00000'"
                    points = 0
                else:
                    points_details = 'NULL'
                    points = None
                cursor.execute(f"UPDATE points SET fixture_{fixture_id} = {points_details} WHERE user_id = '{user_id}';")
                users[user_id]['fixtures'].update({fixture_id: {'points': points}})
            self.connection.commit()
            users[user_id].update({'events': events_points, 'total_points': total_points})

        sorted_total_points = sorted([user['total_points'] for user in users.values()], reverse=True)
        sorted_events_points = {event: sorted([user['events'][event] for user in users.values()], reverse=True) for event in active_events}
        for user_id, user in users.items():
            cursor = self.connection.cursor()
            for event_id, event_points in user['events'].items():
                event_rank = sorted_events_points[event_id].index(event_points)+1
                cursor.execute(f"UPDATE stats SET event_{event_id}_points = '{event_points}', event_{event_id}_rank = '{event_rank}' WHERE user_id = '{user_id}';")
            overall_rank = sorted_total_points.index(user['total_points'])+1
            cursor.execute(f"UPDATE stats SET total_points = '{user['total_points']}', overall_rank = '{overall_rank}' WHERE user_id = '{user_id}';")
            self.connection.commit()