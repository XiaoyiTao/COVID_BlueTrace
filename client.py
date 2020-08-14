# COMP9331 Assignment One
# Name: XIAOYI TAO
# ID: z5181350
# Client Program

import sys
import socket
import threading


class client:
    socket_client = None
    socket_client_UDP = None
    check_login = False
    username = ""

    # initialize the connection of the client
    def __init__(self, IP_server, PORT_server, PORT_UDP):
        try:
            self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_client.connect((IP_server, PORT_server))
        except:
            print("Server connection Error!!!")
            exit()
        try:
            self.socket_client_UDP = socket.socket()
            self.socket_client_UDP.bind(("127.0.0.1", PORT_UDP))
        except:
            print("Client UDP connection Error!!!")
            exit()

    # login the client
    def client_login(self):
        user_name = input("Username: ")
        pass_word = input("Password: ")
        send_msg = "login_information:" + " " + user_name + " " + pass_word
        self.socket_client.send(send_msg.encode(encoding="utf8"))
        receive_from_server = self.socket_client.recv(1024).decode(encoding="utf8")
        if receive_from_server == "login:success":
            self.check_login = True
            self.username = user_name
            print("Welcome to the BlueTrace Simulator!")
        if receive_from_server == "login:failure":
            print("Invalid Password. Please try again")

    def client_logout(self):
        send_msg = "logout:" + " " + self.username
        self.socket_client.send(send_msg.encode(encoding="utf8"))
        receive_from_server= self.socket_client.recv(1024).decode(encoding="utf8")
        if receive_from_server == "logout:success":
            self.check_login = False
            self.username = ""

    def client_start(self):
        while True:
            while not self.check_login:
                self.client_login()
            command = input()
            if command == "logout":
                self.client_logout()


if __name__ == "__main__" :
    IP_server = sys.argv[1]
    PORT_server = int(sys.argv[2])
    PORT_UDP = int(sys.argv[3])
    mobile_client = client(IP_server, PORT_server, PORT_UDP)
    mobile_client.client_start()