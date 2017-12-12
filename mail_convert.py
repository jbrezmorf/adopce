#!/usr/bin/python3

# Reads raw mail from stdin. Parse its first part from HTML to test. 
# Retrives the transaction data.

import sys
import email
import os
import re
import binascii
from html.parser import HTMLParser

import os
script_path = os.path.dirname(os.path.realpath(__file__))

mail_file = os.path.join(script_path, "adopce-data", "adopce-mails")
admin_mail='jbrezmorf@gmail.com'
mbrm=os.path.join(script_path, "mbrm")


vs_ropuchy = {
"9696969696":"cmelak",
"2727272727":"plz",
"3333333333":"janek",
"7171717171":"komar",
"2323232323":"puma",
"1616161616":"netopejr",
"7979797979":"leco",
"1515151515":"skippy",
"7878787878":"drak",
"4242424242":"zrak"
}

# read mails into dict

with open(mail_file, "r") as f:
    emails={}
    for line in f:
        name, mail, *rest = line.split()
        emails[name] = mail

def report_error(msg):
    command = "echo \"{}\" | mail -s \' ADOPCE ERRROR \' {} ".format(msg, admin_mail)    
    os.system(command)    
    raise Exception(command)


def get_token(content, regexp):
    # regexp shoud have just one group
    matches = re.search(regexp+r"(.*)$", content, re.DOTALL)
    assert matches.lastindex == 2
    return matches.group(1), matches.group(2)

class TextHTML(HTMLParser):
    def __init__(self):
        self.content = []
        super().__init__()

    def handle_data(self, data):

        def to_utf(match):
            char = match.group(1) + match.group(2)
            #print("char: ", char)
            return binascii.unhexlify(char).decode()
        #print("\nData: ", data)
        data = re.sub(r"=\r",'',data)
        single_line =''.join(data.split("\n"))
        #print(data.split("\n"))
        #print("line: ", single_line)
        single_line = re.sub(r'=([\dA-Fa-f][\dA-Fa-f])=([\dA-Fa-f][\dA-Fa-f])', to_utf, single_line)
        single_line = re.sub(r'=09', '', single_line)
        self.content.append(single_line)


def html_to_text(body):
    th =TextHTML()
    th.feed(body)
    return th.content

def parse_file(content):
    mail = email.message_from_string(content)
    body = mail.get_payload()
    if mail.is_multipart():
        body = body[0].get_payload()
    body = re.sub(r"<!-->", '', body)
    content = '\n'.join(html_to_text(body))
    print("------------------")
    print(content)
    print("------------------")

    PP='No msg'
    date, content = get_token(content, r"Datum a čas\s*(\d*\. \d*\. \d* \d*:\d*)")
    to_account, content = get_token(content, r"(3984563001/5500\s*.*?\n)")  # .*?  = non-greedy match of anything
    amount, content = get_token(content, r"Částka v měně účtu\s*(\S*) CZK.")
    from_account, content = get_token(content, r"Z účtu\s*(\S*\s.*?\n)")  # .*?  = non-greedy match of anything
    from_account, from_owner = from_account.split('\n', 1)

    VS, content = get_token(content, r"Variabilní symbol\s*(\d*)\s")
    return [date, amount, VS, from_account, from_owner, PP]





content = sys.stdin.read()
try:
    [date, amount, VS, from_account, from_owner, PP] = parse_file(content)
except Exception:
    report_error("Chybny transakcni mail!\n")
    
who = vs_ropuchy.get(VS)
if who is None:
    report_error("Nenalezen variabilni symbol platce!")

msg = "{} {} VS: {} Z: {} PJ: {} PP: {}".format(date, amount, VS, from_account, from_owner, PP)
err=os.system("{} {} {} \"{}\"".format(mbrm, who, amount, msg))
if err:
    report_error("Neuspesne volani \'mbrm\'!");

mail = emails[who]
err=os.system("echo \"Zauctovana platba {}. Dik.\" | mail -s \' adopce OK \' {}".format(amount, mail))
