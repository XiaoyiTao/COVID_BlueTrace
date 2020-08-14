# COMP9331 Assignment One
# Name: XIAOYI TAO
# ID: z5181350
# Client Program
# python 3.7

import sys
import socket
import threading
import re
import time


class client:
    socket_client = None
    socket_client_UDP = None
    username = ""
    check_login = False
    temp_id = ""
    lock_contactlog = None
    contactlog_pool = []

    # initialize the connection of the client
    def __init__(self, IP_server, PORT_server, PORT_UDP):
        try:
            self.socket_client = socket.socket()
            self.socket_client.connect((IP_server, PORT_server))
        except:
            print("server connection error!!!")
            exit()
        try:
            self.socket_client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket_client_UDP.bind(("127.0.0.1", PORT_UDP))
        except:
            print("p2p connection error!!!")
            exit()

    # get the structure time
    def struct_time(self, tm):
        time_exp = "%d/%m/%Y %H:%M:%S"
        structure_time = time.strftime(time_exp, tm)
        return structure_time

    # send message to the server
    def send_to_server(self, send_msg):
        encoded = send_msg.encode(encoding="utf8")
        self.socket_client.send(encoded)

    # receive message from server
    def receive_from_server(self):
        receive_msg = self.socket_client.recv(1024)
        decoded = receive_msg.decode(encoding="utf8")
        return decoded

    # match the message received from other client
    def match_receive_from_client(self):
        client_msg, p2p_addr = self.socket_client_UDP.recvfrom(1024)
        client_msg = client_msg.decode(encoding="utf8")
        match_exp = r"beacon:(\d+) (\d+/\d+/\d+ \d+:\d+:\d+) (\d+/\d+/\d+ \d+:\d+:\d+)"
        match_sentence = re.match(match_exp, client_msg)
        return match_sentence, client_msg

    # receive message from other client
    def receive_from_client(self):
        while True:
            match_sentence, client_msg = self.match_receive_from_client()
            if not match_sentence:
                pass
            else:
                match_group_1 = match_sentence.group(1)
                match_group_2 = match_sentence.group(2)
                match_group_3 = match_sentence.group(3)
                print("received beacon:"+ match_group_1+", "+match_group_2+", "+match_group_3+".")
                struct_local = self.struct_time(time.localtime())
                print("Current time is "+ struct_local+".")
                current_time = time.time()
                time_exp = "%d/%m/%Y %H:%M:%S"
                expirying_time = time.mktime(time.strptime(match_group_3, time_exp))
                starting_time = time.mktime(time.strptime(match_group_2, time_exp))
                # if the beacon is in the valid time, record the beacon into the contactlog
                if starting_time <= current_time:
                    if current_time <= expirying_time:
                        print("The beacon is valid")
                        log_msg = client_msg[7:]
                        new_contactlog = {"temp_id":match_group_1, "start_time":float(starting_time),
                                          "expiry_time":float(expirying_time), "str":log_msg}
                        self.contactlog_pool.append(new_contactlog)
                        self.lock_contactlog.acquire()
                        with open("z5181350_contactlog.txt", "a") as fp:
                            fp.write(log_msg+"\n")
                        self.lock_contactlog.release()
                else:
                    print("The beacon is invalid.")

    # send message to other client
    def send_to_client(self,address, send_msg):
        encoded = send_msg.encode(encoding="utf8")
        self.socket_client_UDP.sendto(encoded, address)

    # type username and password
    def login_interface(self):
        user_name = input("username:")
        pass_word = input("password:")
        send_msg = "login_information:" + " " + user_name + " " + pass_word
        self.send_to_server(send_msg)
        receive_msg = self.receive_from_server()
        return receive_msg, user_name

    # login the client
    def client_login(self):
        receive_msg, user_name = self.login_interface()
        if receive_msg == "login:success":
            self.check_login = True
            self.username = user_name
            print("Welcome to the BlueTrace Simulator!")
            self.lock_contactlog = threading.Lock()
            beacon_remove_thread = threading.Thread(target=self.beacon_remove)
            beacon_remove_thread.setDaemon(True)
            beacon_remove_thread.start()
        elif receive_msg == "login:wrong_password":
            print("Invalid Password. Please try again.")
        elif receive_msg == "login:block":
            print("Invalid Password. Your account has been blocked. Please try again later.")
        elif receive_msg == "login:username_not_exist":
            print("Username does not exist.")
        elif receive_msg == "login:already_login":
            print("User already login.")

    # type logout command
    def logout_interface(self):
        send_msg = "logout:" + " " + self.username
        self.send_to_server(send_msg)
        receive_msg = self.receive_from_server()
        return receive_msg

    # logout the client
    def client_logout(self):
        receive_msg = self.logout_interface()
        if receive_msg == "logout:success":
            self.temp_id = ""
            self.username = ""
            self.check_login = False
        else:
            print("logout failure")

    # type download_tempID command
    def dowloadID_interface(self):
        send_msg = "tempID:" + " " + self.username
        self.send_to_server(send_msg)
        receive_msg = self.receive_from_server()
        return receive_msg

    # downloadID command
    def downloadID_command(self):
        receive_msg = self.dowloadID_interface()
        if receive_msg[:6] == "tempID":
            receive_msg_list = receive_msg.split(":")
            self.temp_id = receive_msg_list[1]
        print("TempID:\n"+ self.temp_id)

    # send beacon to other client
    def send_beacon(self, p2p_address):
        current_time = time.time()
        expiry_time = current_time + 60 * 15
        expirying_time = self.struct_time(time.localtime(expiry_time))
        starting_time = self.struct_time(time.localtime(current_time))
        beacon_msg = self.temp_id + " " + starting_time + " " + expirying_time
        print_msg = self.temp_id+", "+starting_time+", "+expirying_time+","
        print(print_msg)
        send_msg = "beacon:"+ beacon_msg
        self.send_to_client(p2p_address, send_msg)
        pass

    def beacon_filter(self, beacon):
        current_time = time.time()
        if beacon["start_time"] <= current_time:
            if current_time <= beacon["expiry_time"]:
                return True
        return False

    # remove the expired beacons from the contactlog
    def beacon_remove(self):
        while True:
            l = len(self.contactlog_pool)
            temp_list = filter(self.beacon_filter, self.contactlog_pool)
            self.contactlog_pool = list(temp_list)
            new_l = len(self.contactlog_pool)
            if l > new_l:
                self.lock_contactlog.acquire()
                with open("z5181350_contactlog.txt", "w") as fp:
                    for beacon_info in self.contactlog_pool:
                        write_msg = beacon_info["str"]+"\n"
                        fp.write(write_msg)
                self.lock_contactlog.release()

    # upload contact log command
    def upload_log_command(self):
        context = ""
        for beacon_info in self.contactlog_pool:
            context += beacon_info["str"]
            context += "&"
        #print(self.contactlog_pool)
        #print(context)
        self.lock_contactlog.acquire()
        with open("z5181350_contactlog.txt", "w") as fp:
            for beacon_info in self.contactlog_pool:
                write_msg = beacon_info["str"]+"\n"
                fp.write(write_msg)
        self.lock_contactlog.release()
        context = context[:-1]
        #print(context)
        send_msg = "uploadlog:" + " " + self.username + " " + context
        self.send_to_server(send_msg)

    # start the thread for receiving from clients
    def start_thread(self):
        client_receive_thread = threading.Thread(target=self.receive_from_client)
        client_receive_thread.setDaemon(True)
        client_receive_thread.start()

    # start the client
    def start(self):
        self.start_thread()
        while True:
            while not self.check_login:
                self.client_login()
            command = input()
            match_exp = r"Beacon (\d+\.\d+\.\d+\.\d+) (\d+)"
            if command == "Download_tempID":
                self.downloadID_command()
            elif command == "Upload_contact_log":
                self.upload_log_command()
            elif command == "logout":
                self.client_logout()
            elif re.match(match_exp, command):
                match_command = re.match(match_exp, command)
                match_group_1 = match_command.group(1)
                match_group_2 = match_command.group(2)
                self.send_beacon((match_group_1, int(match_group_2)))
            else:
                print("Error. Invalid command")

# main function
if __name__ == "__main__":
    IP_server = sys.argv[1]
    PORT_server = int(sys.argv[2])
    PORT_UDP = int(sys.argv[3])
    mobile_client = client(IP_server, PORT_server, PORT_UDP)
    mobile_client.start()