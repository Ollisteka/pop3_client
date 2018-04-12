# !/usr/bin/env python3
import base64
import re
import socket
import ssl


POP3_PORT = 995
POP3_SERVER = 'pop.yandex.ru'  # 'smtp-relay.gmail.com'

FROM_MAIL = "inet.task@yandex.com"

ENCODING = 'utf-8'
MAXLENGTH = 4096

CRLF = '\r\n'
B_CRLF = b'\r\n'


class POP3:
    welcome = None
    closed = False

    def __init__(self, address=None, port=None):
        if not address and not port:
            self.address = None
        else:
            self.address = (address, port)
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receivers = []
        self.sender = ""
        self.subject = ""

        self.commands = {"AUTH": self.auth,
                         "USER": self.user,
                         "DELE": self.delete,
                         "PASS": self.password,
                         "STAT": self.stat,
                         "LIST": self.list,
                         "TOP": self.top,
                         "NOOP": self.noop,
                         "RSET": self.reset,
                         "RETR": self.retrieve,
                         "QUIT": self.quit,
                         }

    def top(self, mail_num, lines_shown):
        mes = "TOP " + str(mail_num) + " " + str(lines_shown) + CRLF
        rep = self.send(mes)
        return rep

    def reset(self):
        rep = self.send("RSET" + CRLF)
        return rep

    def noop(self):
        rep = self.send("NOOP" + CRLF)
        return rep

    def retrieve(self, letter_number):
        rep = self.send("RETR " + letter_number + CRLF)
        boundary = self.find_boundary(rep)
        mime_objects = self.find_mime(boundary, rep)
        result = []
        for obj in mime_objects:
            result.append(self.parse_mime(obj))

        for element in result:
            if isinstance(element, tuple):
                print("Saving attachment " + element[0])
                with open(element[0], 'wb') as f:
                    f.write(element[1])
            else:
                print(element)

    def parse_mime(self, text):
        coded_reg = re.compile('\n\n(.+==)', re.DOTALL)
        coded_reg2 = re.compile('\r\n\r\n(.+?)--', re.DOTALL)
        plain_reg = re.compile('Content-Transfer-Encoding:.*?\r\n\r\n(.+)--',
                               re.DOTALL)
        filename_reg = re.compile('filename="(.*)"')
        if "text" in text:
            if "base64" in text:
                coded = re.search(coded_reg, text).group(1)
                return base64.b64decode(coded)
            else:
                res = re.search(plain_reg, text)
                return res.group(1)
        elif "application/octet-stream" in text \
                or "Content-Disposition: attachment" in text:
            coded = re.search(coded_reg, text)
            if not coded:
                coded = re.search(coded_reg2, text)
            filename = self.parse_filename(re.search(filename_reg,
                                                     text).group(1))
            coded_text = coded.group(1).strip('\n').strip('\r')
            return filename, base64.b64decode(coded_text)

    def parse_filename(self, name):
        if "=?UTF-8?B?" in name:
            extracted = name[10:-2]
            return base64.b64decode(extracted).decode('utf8')
        return name

    def find_mime(self, boundary, text):
        regexp = re.compile(r'(?=(--{0}(.+?)--{0}))'.format(boundary),
                            re.DOTALL)
        matches = re.finditer(regexp, text)
        if matches:
            result = []
            for match in matches:
                result.append(match.group(1))
            return result

    def find_boundary(self, text):
        match = re.search('boundary="(.+)"', text)
        if match:
            return match.group(1)

    def stat(self):
        rep = self.send("STAT" + CRLF)
        return rep

    def list(self, letter_number=None):
        if letter_number is None:
            letter_number = ""
        rep = self.send("LIST " + letter_number + CRLF)
        return rep

    def delete(self, letter_number):
        rep = self.send("DELE " + letter_number + CRLF)
        return rep

    def quit(self):
        """
        End the session
        :return:
        """
        rep = self.send("QUIT" + CRLF)
        self.closed = True
        self.control_socket.shutdown(socket.SHUT_RDWR)
        self.control_socket.close()
        return rep

    def user(self, username):
        rep = self.send("USER " + username + CRLF)
        return rep

    def password(self, password):
        mes = "PASS " + password + CRLF
        rep = self.send(mes)
        return rep

    def auth(self, username="inet.task@yandex.ru", password="inet.task."):
        print(self.user(username))
        print(self.password(password))
        # return rep

    def send(self, command, text=True):
        """
        Send a command to server
        :param text:
        :param command:
        :return:
        """
        if text:
            self.control_socket.sendall(command.encode(ENCODING))
        else:
            self.control_socket.sendall(command)
        return self.get_reply()

    def connect(self, address=None, port=None):
        """
        Connect to the server and print welcome message
        :return:
        """
        if not self.address:
            self.address = (address, port)
        elif not address and not port and not self.address:
            raise Exception("Address and port must be specified in "
                            "constructor or in connect()")
        self.control_socket = ssl.wrap_socket(
            self.control_socket, ssl_version=ssl.PROTOCOL_SSLv23)
        self.control_socket.connect(self.address)
        self.control_socket.settimeout(1)
        self.welcome = self.get_reply()
        return self.welcome

    def get_reply(self):
        """
        Get a reply from server
        :return:
        """
        reply = self.__get_full_reply()
        return reply
        # c = reply[:1]
        # if c in {'1', '2', '3'}:
        #     return reply
        # if c == '4':
        #     raise TransientError(reply)
        # if c == '5':
        #     raise PermanentError(reply)
        # raise ProtectedError(reply)

    def __get_full_reply(self):
        """
        Get a long reply
        :return:
        """
        reply = ''
        tmp = self.control_socket.recv(MAXLENGTH).decode(ENCODING)
        reply += tmp
        while tmp:
            try:
                tmp = self.control_socket.recv(MAXLENGTH).decode(ENCODING)
                reply += tmp
            except Exception:
                break
        return reply

    def run_batch(self):
        """
        Runs an ftp client in console mode
        :return:
        """
        while not self.closed:
            print("Type a command:")
            inp = input().split(' ')
            command = inp[0].upper()
            arguments = inp[1:]
            if command in self.commands:
                if arguments:
                    if len(arguments) == 1:
                        print(
                            self.commands[command](arguments[0]))
                    if len(arguments) == 2:
                        print(
                            self.commands[command](arguments[0],
                                                   arguments[1]))
                else:
                    print(self.commands[command]())
            else:
                print("UNKNOWN COMMAND")
