#!/usr/bin/env python3

import requests
import os
from jinja2 import Template
from datetime import datetime

AUTH_TOKEN = os.environ['AUTH_TOKEN']
API_URL = 'https://api.gotinder.com'


def api_request(path):
    return requests.get(f'{API_URL}{path}', headers={'X-Auth-Token': AUTH_TOKEN}).json()


def get_matches():
    return api_request('/v2/matches?locale=pl&count=100&message=1&is_tinder_u=false')['data']['matches']


def get_messages(match_id, page_token=None):
    page_part = f'&page_token={page_token}' if page_token else ''
    return api_request(f'/v2/matches/{match_id}/messages?count=100{page_part}')['data']


def get_user_profile():
    return api_request('/v2/profile?locale=pl&include=account%2Cboost%2Ccontact_cards%2Cemail_settings%2Cinstagram%2Clikes%2Cnotifications%2Cplus_control%2Cproducts%2Cpurchase%2Creadreceipts%2Cswipenote%2Cspotify%2Csuper_likes%2Ctinder_u%2Ctravel%2Ctutorials%2Cuser')['data']['user']


def export_messages(match_id):
    messages = []
    page_token = None
    while True:
        data = get_messages(match_id, page_token)
        messages += data['messages']
        if 'next_page_token' not in data:
            return messages
        else:
            page_token = data['next_page_token']


def read_html_template():
    with open('template.html') as f:
        return f.read()


def generate_html(messages, user, match_user, output_path):
    template = Template(read_html_template())

    users = {user['_id']: user['name'], match_user['_id']: match_user['name']}
    avatars = {user['_id']: user['photos'][0]['url'],
               match_user['_id']: match_user['photos'][0]['url']}

    prepared_messages = [{'left': user['_id'] == m['from'], 'name': users[m['from']], 'timestamp': m['timestamp'], 'content': m['message'], 'display_date': datetime.fromtimestamp(
        m['timestamp']/1000).strftime("%m/%d/%Y %H:%M:%S"), 'avatar_url': avatars[m['from']]} for m in sorted(messages, key=lambda x: x['timestamp'])]

    with open(output_path, 'w') as f:
        f.write(template.render(msgs=prepared_messages,
                                user=user, match_user=match_user))


if __name__ == '__main__':
    matches = [(data['id'], data['person']) for data in get_matches()]
    print('Found following matches with message history:')
    for i, m in enumerate(matches):
        print(f'{i+1}. {m[1]["name"]}')
    match_no = int(input('Input number of match to export: ')) - 1
    match = matches[match_no]
    messages = export_messages(match[0])
    generate_html(messages, get_user_profile(), match[1], 'output.html')
