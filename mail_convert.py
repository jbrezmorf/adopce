#!/usr/bin/python3

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
        print(line)
        name, mail, *rest = line.split()
        emails[name] = mail

def report_error(msg):
    command = "echo \"{}\" | mail -s \' ADOPCE ERRROR \' {} ".format(msg, admin_mail)
    os.system(command)
    print(command)
    exit


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

        single_line =''.join(data.split("\n"))
        #print("line: ", single_line)
        single_line = re.sub(r'=([\dA-Fa-f][\dA-Fa-f])=([\dA-Fa-f][\dA-Fa-f])', to_utf, single_line)
        single_line = re.sub(r'=', '', single_line)
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
    #print(content)

    PP='No msg'
    date, content = get_token(content, r"Datum a čas\s*(\d*\. \d*\. \d* \d*:\d*)")
    to_account, content = get_token(content, r"(3984563001/5500\s*.*?\n)")  # .*?  = non-greedy match of anything
    amount, content = get_token(content, r"Částka v měně účtu\s*(\S*) CZK.")
    from_account, content = get_token(content, r"Z účtu\s*(\S*\s.*?\n)")  # .*?  = non-greedy match of anything
    from_account, from_owner = from_account.split('\n', 1)

    VS, content = get_token(content, r"Variabilní symbol\s*(\d*)\s")
    return [date, amount, VS, from_account, from_owner, PP]


    #$who=$lidi{$VS};
    #if (! $who) {
        #while (($xx, $name) = each (%lidi)) {
        #if ($PP =~ /$name/i) {
            #$who=$name; 
        #}
    #}
    #if (! $who) {
    #report_error("Nenalezen variabilni symbol platce!\nline: $line");}
    #}
    ## account by call mbrm
    #$_=`~/bin/mbrm $who $amount \"$date $amount VS: $VS Z: $ucet PJ: $PJ PP: $PP\"`;
    #if (!/SUCCESS/ || /ERR/) {
      #report_error("Neuspesne volani \'mbrm\'!\n line: $line\n$_");
    #}

    ## send informative mail 
        #$MAIL=`cat $MAILS|grep $who |head -n 1`; # get appropriate line
        #$MAIL=~/([a-z.]*@[a-z.]*)/;
    #$MAIL=$1;
    #system(" echo \"Zauctovana platba $amont. Dik.\" | mail -s \' adopce OK \' $MAIL");

    #$OK=1;
    #} 
#else {
    #report_error("Chybny transakcni mail!\n");
#}



#filetext = sys.stdin.read()
with open("test-data/raw_mail_plz", "r") as f:
    content = f.read()
[date, amount, VS, from_account, from_owner, PP] = parse_file(content)
who = vs_ropuchy.get(VS)
if who is None:
    report_error("Nenalezen variabilni symbol platce!")

msg = "{} {} VS: {} Z: {} PJ: {} PP: {}".format(date, amount, VS, from_account, from_owner, PP)
err=os.system("{} {} {} \"{}\"".format(mbrm, who, amount, msg))
if err:
    report_error("Neuspesne volani \'mbrm\'!");

mail = emails[who]
err=os.system("echo \"Zauctovana platba {}. Dik.\" | mail -s \' adopce OK \' {}".format(amount, mail))
