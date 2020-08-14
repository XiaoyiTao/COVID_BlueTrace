import socket

credentials = {}
file = open("credentials.txt", 'r')
for line in file.readlines():
    content = line.split()
    credentials[content[0]] = content[1]

print(credentials)

