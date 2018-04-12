# !/usr/bin/env python3

import argparse
import json
import os
import sys

import pop3
from pop3 import POP3, POP3_PORT, POP3_SERVER

SENDER = "From"
RECEIVERS = "To"
TEXT = "Text"
SUBJECT = "Subject"
ATTACHMENTS = "Attachments"

def main():
    parser = argparse.ArgumentParser(
        usage='{} [OPTIONS]'.format(
            os.path.basename(
                sys.argv[0])),
        description='SMTP client')
    parser.add_argument('address', help='address to connect',
                        nargs='?', default=POP3_SERVER)
    parser.add_argument('port', help='port', nargs='?',
                        type=int, default=POP3_PORT)
    parser.add_argument('-c', '--console', action="store_true", help="Enable console mode")

    args = parser.parse_args()
    pop3_con = POP3(args.address, args.port)
    print(pop3_con.connect())
    if args.console:
        pop3_con.run_batch()


def send_mail(smtp_con):
    """

    :type smtp_con: SMTP
    :return:
    """
    with open("input.json", 'r', encoding=smtp.ENCODING) as f:
        config = json.loads(f.read())
    sender = config[SENDER]
    recievers = config[RECEIVERS]
    subject = config[SUBJECT]
    attachments = config[ATTACHMENTS]
    with open(config[TEXT], 'r', encoding='utf8') as f:
        text_lines = f.readlines()
    message = Message(sender, recievers, subject, text_lines, attachments)
    email = message.get_email()
    print(smtp_con.ehllo())
    print(smtp_con.auth())
    print(smtp_con.mail_from(sender))
    for reciever in recievers:
        print(smtp_con.rcpt_to(reciever))
    print(smtp_con.data())
    print(smtp_con.send(email))
    print(smtp_con.quit())


if __name__ == '__main__':
    sys.exit(main())
