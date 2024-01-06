#!/usr/bin/env python3
import requests
import uuid
import string
import random
from urllib.parse import urlencode
from pathlib import Path
import argparse
from calendar import monthrange
from datetime import datetime

REG_URL = 'https://secure.runescape.com/m=account-creation/create_account?theme=oldschool'
PW_CHARS = string.ascii_letters + string.digits + '!"$%^*().#<>\''

class Scrappey:
    def __init__(self, api_key, session=str(uuid.uuid4)):
        self._scrappey_url = f'https://publisher.scrappey.com/api/v1?key={api_key}'
        self._session = session
        self._headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'session': self._session,
            'cmd': 'sessions.create'
        }
        requests.post(self._scrappey_url, headers=self._headers, json=data)

    def __del__(self):
        data = {
            'session': self._session,
            'cmd': 'sessions.destroy'
        }
        requests.post(self._scrappey_url, headers=self._headers, json=data)

    def get(self, url, additional_args=None):
        data = {
            'session': self._session,
            'cmd': 'request.get',
            'url': url
        }
        if additional_args:
            data.update(additional_args)
        response = requests.post(self._scrappey_url, headers=self._headers, json=data)
        return response.json()

    def post(self, url, additional_args=None, post_data=None):
        data = {
            'session': self._session,
            'cmd': 'request.post',
            'url': url
        }
        if post_data:
            data.update({'postData': urlencode(post_data)})
        if additional_args:
            data.update(additional_args)
        response = requests.post(self._scrappey_url, headers=self._headers, json=data)
        return response.json()



def create_account(email, api_key, output_file=None, id=1, total_accounts=1):
    error_count = 0

    email_parts = email.split('@')
    unique_identifier = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
    reg_email = email_parts[0] + '+' + unique_identifier + '@' + email_parts[1]

    reg_pw = ''.join(random.choice(PW_CHARS) for _ in range(16))

    reg_dob_year = random.randint(1970, 2005)
    reg_dob_month = random.randint(1, 12)
    reg_dob_day = random.randint(1, monthrange(reg_dob_year, reg_dob_month)[1])

    scrappey = Scrappey(api_key)
    csrf_selector = {
        'cssSelector': 'input[name="csrf_token"]',
        'customAttribute': 'value'
    }
    registration_data = {
        'theme': 'oldschool',
        'flow': 'web',
        'email1': reg_email,
        'onlyOneEmail': 1,
        'password1': reg_pw,
        'onlyOnePassword': 1,
        'day': reg_dob_day,
        'month': reg_dob_month,
        'year': reg_dob_year,
        'agree_terms': 1,
        'create-submit': 'create'
    }

    print(f'[{id}/{total_accounts}] Attempting to register account "{reg_email}" with password {reg_pw}')
    
    while error_count < 3:
        try:
            csrf_token = scrappey.get(REG_URL, additional_args=csrf_selector)['solution']['cssSelector'][0]
            reg_resp = scrappey.post(REG_URL, post_data={**registration_data, **{'csrf_token': csrf_token}})

            if 'You can now begin your adventure with your new account.' in reg_resp['solution']['response']:
                print(f'[{id}/{total_accounts}] Registered account "{reg_email}" with password {reg_pw}')
                if output_file:
                    date = datetime.today().date()
                    f = open(output_file, 'a')
                    f.write(f'{reg_email},{reg_pw},{reg_dob_year}/{reg_dob_month}/{reg_dob_day},{date.year}/{date.month}/{date.day},')
                    f.close()
                return
        except:
            pass
        
        error_count = error_count + 1
        print(f'[{id}/{total_accounts}] Error while registering account "{reg_email}" with password {reg_pw} ({error_count}/3)')
        
    print(f'[{id}/{total_accounts}] Failed three times when registering account "{reg_email}" with password {reg_pw} - skipping.')
        

def main():
    parser = argparse.ArgumentParser(description='Create RuneScape accounts')
    parser.add_argument('-e', help='Base gmail address for account creation', required=True)
    parser.add_argument('-n', type=int, help='Number of accounts to create', default=1)
    parser.add_argument('-k', help='Scrappey API key', required=True)
    parser.add_argument('-o', help='Output file (.csv)', default=None)
    args = parser.parse_args()

    if args.o:
        if not Path(args.o).is_file():
            f = open(args.o, 'w')
            f.write('email,password,dob,date_registered,ip_address')
            f.close()

    for n in range(args.n):
        create_account(args.e, args.k, output_file=args.o, id=n+1, total_accounts=args.n)

if __name__ == "__main__":
    main()