# COMP9331 Assignment One
# Name: XIAOYI TAO
# ID: z5181350
# Server Program
import sys
import socket
import threading

class user:
    state = "logout"

    def __init__(self, user_name, pass_word):
        self.user_name = user_name
        self.pass_word = pass_word

    def user_state(self, password, client, block_duration):
        if self.pass_word ==


class server:
    IP_server = "127.0.0.1"
    Block_duration = 0
    socket_server = None
    credentials = {}

    # initialize the connection of the server
    def __init__(self, PORT_server, Block_duration):
        self.Block_duration = Block_duration
        self.PORT_server = PORT_server

        # read from credentials.txt and transfer the username and password to dictionary
        file = open("credentials.txt", 'r')
        for line in file.readlines():
            content = line.split()
            self.credentials[content[0]] = content[1]

        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.bind((self.IP_server, self.PORT_server))

    def login_request(self, socket_client, user_name, pass_word):
        if user_name in self.credentials:
            if self.credentials[user_name] == pass_word:
                send_msg = "login:success"
                socket_client.sendall(send_msg.encode(encoding="utf8"))
            else:
                send_msg = "login:failure"
                socket_client.sendall(send_msg.encode(encoding="utf8"))

    def logout_request(self, socket_client, user_name):
        if user_name in self.credentials:
            send_msg = "logout:success"
            socket_client.sendall(send_msg.encode(encoding="utf8"))
            print(user_name+" logout")

    def receive_from_Client(self, socket_client):
        while True:
            try:
                receive_from_client = socket_client.recv(1024)
            except ConnectionError:
                print("Connection error!!!")
                socket_client.close()
                break

            receive_from_client = receive_from_client.decode(encoding="utf8")
            receive_msg = receive_from_client.split()
            if receive_msg[0] == "login_information:":
                user_name = receive_msg[1]
                pass_word = receive_msg[2]
                self.login_request(socket_client, user_name, pass_word)
            elif receive_msg[0] == "logout:":
                user_name = receive_msg[1]
                self.logout_request(socket_client, user_name)

    def server_start(self):
        self.socket_server.listen(10)
        while True:
            socket_client, addr = self.socket_server.accept()
            # print('Connected by ', addr)
            self.receive_from_Client(socket_client)
            # thread = threading.Thread(target=self.receive_from_Client, args=(socket_client,))
            # thread.setDaemon(True)
            # thread.start()


if __name__ == "__main__":
    PORT_server = int(sys.argv[1])
    Block_duration = int(sys.argv[2])
    center_server = server(PORT_server, Block_duration)
    center_server.server_start()
