# COMP9331 Assignment One
# Name: XIAOYI TAO
# ID: z5181350
# Server Program
# python 3.7

import sys
import socket
import threading
import re
import time
import random

# the user class
class user:
    password = None
    username = None
    client = None
    client_state = "logout"
    temp_id = []
    block_time = 0
    login_failure_times = 1

    def __init__(self, username, password):
        self.username = username
        self.password = password

    # the block state
    def blocker(self):
        self.client_state = "logout"
        self.login_failure_times = 1

        # when a user try to log out, change the state of the user
    def user_logout(self):
        if self.client_state != "login":
            return "failure"
        else:
            self.client_state = "logout"
            self.client = None
            self.login_failure_times = 1
            self.temp_id = []
            return "success"

    # when client try to login, store and change the state of the user
    def user_login(self, password, client, block_duration):
        if self.client_state == "block":
            return "block"
        if self.client_state == "login":
            return "already_login"
        if self.password == password:
            self.client_state = "login"
            self.client = client
            self.login_failure_times = 1
            return "success"
        else:
            if self.login_failure_times >= 3:
                self.client_state = "block"
                threading.Timer(block_duration, self.blocker).start()
                return "block"
            else:
                self.login_failure_times += 1
                return "wrong_password"

    # create temp ID for a user
    def create_temp_ID(self, temp_id):
        self.temp_id.append(temp_id)



class server:
    temp_ID_file = "tempIDs.txt"
    credentials_file = "credentials.txt"
    user_dic = {}
    host_port = 11024
    host_address = "127.0.0.1"
    socket_server = None
    client_list = []
    block_duration = 10;
    temp_id_start = 10000000000000000000
    temp_id_list = {}

    def __init__(self, PORT_server, block_duration):
        self.block_duration = block_duration
        self.host_port = PORT_server
        fp = open(self.credentials_file, 'r')
        for line in fp.readlines():
            match_exp = r"(\+\w+) (\w+)"
            match_sentence = re.match(match_exp, line)
            match_group_1 = match_sentence.group(1)
            match_group_2 = match_sentence.group(2)
            new_user = user(match_group_1, match_group_2)
            self.user_dic[match_sentence.group(1)] = new_user
        fp.close()
        fp = open(self.temp_ID_file, 'r')
        for line in fp.readlines():
            match_exp = r"(\+\w+) (\d+) (\d+/\d+/\d+ \d+:\d+:\d+) (\d+/\d+/\d+ \d+:\d+:\d+)"
            match_sentence = re.match(match_exp, line)
            match_group_1 = match_sentence.group(1)
            match_group_2 = match_sentence.group(2)
            match_group_3 = match_sentence.group(3)
            match_group_4 = match_sentence.group(4)
            #new_temp_ID = temp_ID(match_group_2, match_group_3, match_group_4)
            new_temp_ID = {"temp_id":match_group_2, "start_time":match_group_3, "expiry_time":match_group_4}
            self.user_dic[match_group_1].temp_id.append(new_temp_ID)
            time_exp = "%d/%m/%Y %H:%M:%S"
            starting_time = time.mktime(time.strptime(match_group_3, time_exp))
            expirying_time = time.mktime(time.strptime(match_group_4, time_exp))
            new_temp_id_dic = {"username": match_group_1, "start_time": starting_time, "expiry_time":expirying_time}
            self.temp_id_list[match_group_2] = new_temp_id_dic
        fp.close()
        self.socket_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_server.bind((self.host_address, self.host_port))

    # send message to client
    def send_to_client(self, send_msg, client):
        encoded = send_msg.encode(encoding="utf8")
        client.sendall(encoded)

    # deal with the login request sending from client
    def login_request(self, client, user_name, pass_word):
        send_msg = "login:"
        if user_name in self.user_dic:
            check = self.user_dic[user_name].user_login(pass_word, client, self.block_duration)
            send_msg += str(check)
        else:
            send_msg += "username_not_exist"
        self.send_to_client(send_msg, client)

    # deal with the logout request sending from client
    def logout_request(self, client, username):
        send_msg = "logout:"
        check = ""
        if username in self.user_dic:
            check = self.user_dic[username].user_logout()
            send_msg += str(check)
        else:
            send_msg += "username_not_exist"
        self.send_to_client(send_msg, client)
        if check == "success":
            print(username+" logout")

    # produce temp ID
    def produce_temp_ID(self):
        temp_id = self.temp_id_start
        while True:
            temp_id = temp_id + random.randint(0, 89999999999999999999)
            self.temp_id_start = temp_id
            yield temp_id

    def struct_time(self, tm):
        time_exp = "%d/%m/%Y %H:%M:%S"
        structure_time = time.strftime(time_exp, tm)
        return structure_time

    # deal with the download temp ID request
    def temp_ID_command(self, client, username):
        temp_id = next(self.produce_temp_ID())
        self.user_dic[username].create_temp_ID(temp_id)
        starting_time = time.time()
        expirying_time = starting_time + 15*60
        send_msg = "tempID:" + str(temp_id) + ":" + str(starting_time) + ":" + str(expirying_time)
        self.send_to_client(send_msg, client)
        new_temp_id_dic = {"username":username, "start_time":starting_time, "expiry_time":expirying_time}
        self.temp_id_list[str(temp_id)] = new_temp_id_dic
        with open(self.temp_ID_file, "a") as fp:
            struct_start = self.struct_time(time.localtime(starting_time))
            struct_expiry = self.struct_time(time.localtime(expirying_time))
            write_msg = "\n"+username+" "+str(temp_id)+" "+struct_start+" "+struct_expiry
            fp.write(write_msg)
        print_msg = "user:"+username+"\nTempID\n"+ str(temp_id)
        print(print_msg)

    # deal with the upload contact log command
    def contactlog_command(self, username, context):
        log_list = context.split("&")
        print("received contact log form "+username)
        #print(log_list)
        for log in log_list:
            match_exp = r"(\d+) (\d+/\d+/\d+ \d+:\d+:\d+) (\d+/\d+/\d+ \d+:\d+:\d+)"
            match_sentence = re.match(match_exp, log)
            if match_sentence:
                match_group_1 = match_sentence.group(1)
                match_group_2 = match_sentence.group(2)
                match_group_3 = match_sentence.group(3)
                log = match_group_1+", "+match_group_2+", "+match_group_3+";"
                print(log)
        print("\nContact log checking")
        for log in log_list:
            match_exp = r"(\d+) (\d+/\d+/\d+ \d+:\d+:\d+) (\d+/\d+/\d+ \d+:\d+:\d+)"
            match_sentence = re.match(match_exp, log)
            if match_sentence:
                match_group_1 = match_sentence.group(1)
                match_group_2 = match_sentence.group(2)
                username = self.temp_id_list[match_group_1]["username"]
                log = username+", "+match_group_2 + ", " + match_group_1 + ";"
                print(log)

    # deal with the commands sending from client
    def receive_from_client(self, client):
        while True:
            try:
                receive_msg = client.recv(1024)
            except ConnectionError:
                print("connect error. client close.")
                client.close()
                self.client_list.remove(client)
                for username in self.user_dic:
                    user = self.user_dic[username]
                    if user.client == client and user.client_state == "login":
                        user.client_state = "logout"
                break
            receive_msg = receive_msg.decode(encoding="utf8")
            if receive_msg == "":
                continue
            receive_msg = receive_msg.split()
            if receive_msg[0] == "login_information:":
                user_name = receive_msg[1]
                pass_word = receive_msg[2]
                self.login_request(client, user_name, pass_word)
            elif receive_msg[0] == "logout:":
                user_name = receive_msg[1]
                self.logout_request(client, user_name)
            elif receive_msg[0] == "tempID:":
                user_name = receive_msg[1]
                self.temp_ID_command(client, user_name)
            elif receive_msg[0] == "uploadlog:":
                user_name = receive_msg[1]
                s = " "
                l = receive_msg[2:]
                context = s.join(l)
                self.contactlog_command(user_name, context)

    # start the server
    def start(self):
        self.socket_server.listen(10)
        while True:
            client, _ = self.socket_server.accept()
            receive_thread = threading.Thread(target=self.receive_from_client, args=(client,))
            receive_thread.setDaemon(True)
            receive_thread.start()
            self.client_list.append(client)


if __name__ == "__main__":
    PORT_server = int(sys.argv[1])
    block_duration = int(sys.argv[2])
    central_server = server(PORT_server, block_duration)
    central_server.start()


