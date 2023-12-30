"""
    ##  Implementation of peer
    ##  Each peer has a client and a server side that runs on different threads
    ##  150114822 - Eren Ulaş
"""

#New file

import hashlib
from socket import *
import threading
import time
import select
import logging
from colorama import init, Fore, Back, Style
import db

db = db.DB()

from utils import print_with_color

init()

cuurentChat = None
notifications = []


class ChatServer(threading.Thread):
    # Peer server initialization
    def __init__(self, chatServerPort):
        threading.Thread.__init__(self)
        # tcp socket for peer server
        self.tcpServerSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpServerSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # port number of the peer server
        self.peerServerPort = chatServerPort

    # main method of the peer server thread
    def run(self):
        hostname = gethostname()
        self.peerServerHostname = gethostbyname(hostname)

        self.tcpServerSocket.bind((self.peerServerHostname, self.peerServerPort))
        print_with_color(
            f"Chat server started on {self.peerServerHostname}...", Fore.LIGHTBLUE_EX
        )
        self.tcpServerSocket.listen(4)
        # inputs sockets that should be listened
        inputs = [self.tcpServerSocket]
        # server listens as long as there is a socket to listen in the inputs list and the user is online
        while inputs:
            # print(f"Whiling")
            # monitors for the incoming connections
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                # If a server waits to be connected enters here
                # print(f"Readables: {readable}")
                for s in readable:
                    if s == self.tcpServerSocket:
                        connected, addr = s.accept()
                        connected.setblocking(0)
                        inputs.append(connected)
                    else:
                        # message is received from connected peer
                        messageReceived = s.recv(1024).decode()
                        if messageReceived:
                            # print(f"Message recieved {messageReceived}")
                            # connected peer ended the chat
                            area, rest = messageReceived.split(":")
                            print(area)
                            if area == "group":
                                # print(f"Group message recieved")
                                group_name, sender_and_message = rest.split("@")
                                if group_name == cuurentChat:
                                    sender, message = sender_and_message.split("~")
                                    if message == "quit":
                                        print_with_color(f"{sender} left the chat", Fore.CYAN)
                                    elif message == "leave":
                                        print_with_color(f"{sender} left the group", Fore.LIGHTBLUE_EX)
                                    elif message == "join":
                                        
                                        print_with_color(f"{sender} joined the group", Fore.GREEN)
                                    else:
                                        print_with_color(f"{sender} -> {message}", Fore.LIGHTMAGENTA_EX)
                                else:
                                    notifications.append(sender_and_message)
                                    print_with_color(f"You have new notification from group {group_name}", Fore.CYAN)
                        elif messageReceived[:2] == ":q":
                            self.isChatRequested = 0
                            # inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            if len(messageReceived) == 2:
                                print("User you're chatting with ended the chat")
                                print("Press enter to quit the chat: ")
                        # if the message is an empty one, then it means that the
                        # connected user suddenly ended the chat(an error occurred)
                        elif len(messageReceived) == 0:
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            # print("User you're chatting with suddenly ended the chat")
                            # print("Press enter to quit the chat: ")
            # handles the exceptions, and logs them
            except Exception as e:
                print_with_color(f"Error occured {e}", Fore.RED)


# Client side of peer
class PeerClient(threading.Thread):
    # variable initializations for the client side of the peer
    def __init__(
        self, ipToConnect, portToConnect, username, peerServer, responseReceived
    ):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # client side tcp socket initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False

    # main method of the peer client thread
    def run(self):
        print(f"Peer client started... {self.ipToConnect} {self.portToConnect}")
        # connects to the server of other peer
        self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))
        # if the server of this peer is not connected by someone else and if this is the requester side peer client then enters here
        if self.peerServer.isChatRequested == 0 and self.responseReceived is None:
            # composes a request message and this is sent to server and then this waits a response message from the server this client connects
            requestMessage = (
                "CHAT-REQUEST "
                + str(self.peerServer.peerServerPort)
                + " "
                + self.username
            )
            # logs the chat request sent to other peer
            logging.info(
                "Send to "
                + self.ipToConnect
                + ":"
                + str(self.portToConnect)
                + " -> "
                + requestMessage
            )
            # sends the chat request
            self.tcpClientSocket.send(requestMessage.encode())
            print("Request message " + requestMessage + " is sent...")
            # received a response from the peer which the request message is sent to
            self.responseReceived = self.tcpClientSocket.recv(1024).decode()
            # logs the received message
            logging.info(
                "Received from "
                + self.ipToConnect
                + ":"
                + str(self.portToConnect)
                + " -> "
                + self.responseReceived
            )
            print("Response is " + self.responseReceived)
            # parses the response for the chat request
            self.responseReceived = self.responseReceived.split()
            # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
            if self.responseReceived[0] == "OK":
                # changes the status of this client's server to chatting
                self.peerServer.isChatRequested = 1
                # sets the server variable with the username of the peer that this one is chatting
                self.peerServer.chattingClientName = self.responseReceived[1]
                # as long as the server status is chatting, this client can send messages
                while self.peerServer.isChatRequested == 1:
                    # message input prompt
                    messageSent = input(self.username + ": ")
                    # sends the message to the connected peer, and logs it
                    self.tcpClientSocket.send(messageSent.encode())
                    logging.info(
                        "Send to "
                        + self.ipToConnect
                        + ":"
                        + str(self.portToConnect)
                        + " -> "
                        + messageSent
                    )
                    # if the quit message is sent, then the server status is changed to not chatting
                    # and this is the side that is ending the chat
                    if messageSent == ":q":
                        self.peerServer.isChatRequested = 0
                        self.isEndingChat = True
                        break
                # if peer is not chatting, checks if this is not the ending side
                if self.peerServer.isChatRequested == 0:
                    if not self.isEndingChat:
                        # tries to send a quit message to the connected peer
                        # logs the message and handles the exception
                        try:
                            self.tcpClientSocket.send(":q ending-side".encode())
                            logging.info(
                                "Send to "
                                + self.ipToConnect
                                + ":"
                                + str(self.portToConnect)
                                + " -> :q"
                            )
                        except BrokenPipeError as bpErr:
                            logging.error("BrokenPipeError: {0}".format(bpErr))
                    # closes the socket
                    self.responseReceived = None
                    self.tcpClientSocket.close()
            # if the request is rejected, then changes the server status, sends a reject message to the connected peer's server
            # logs the message and then the socket is closed
            elif self.responseReceived[0] == "REJECT":
                self.peerServer.isChatRequested = 0
                print("client of requester is closing...")
                self.tcpClientSocket.send("REJECT".encode())
                logging.info(
                    "Send to "
                    + self.ipToConnect
                    + ":"
                    + str(self.portToConnect)
                    + " -> REJECT"
                )
                self.tcpClientSocket.close()
            # if a busy response is received, closes the socket
            elif self.responseReceived[0] == "BUSY":
                print("Receiver peer is busy")
                self.tcpClientSocket.close()
        # if the client is created with OK message it means that this is the client of receiver side peer
        # so it sends an OK message to the requesting side peer server that it connects and then waits for the user inputs.
        elif self.responseReceived == "OK":
            # server status is changed
            self.peerServer.isChatRequested = 1
            # ok response is sent to the requester side
            okMessage = "OK"
            self.tcpClientSocket.send(okMessage.encode())
            logging.info(
                "Send to "
                + self.ipToConnect
                + ":"
                + str(self.portToConnect)
                + " -> "
                + okMessage
            )
            print("Client with OK message is created... and sending messages")
            # client can send messsages as long as the server status is chatting
            while self.peerServer.isChatRequested == 1:
                # input prompt for user to enter message
                messageSent = input(self.username + ": ")
                self.tcpClientSocket.send(messageSent.encode())
                logging.info(
                    "Send to "
                    + self.ipToConnect
                    + ":"
                    + str(self.portToConnect)
                    + " -> "
                    + messageSent
                )
                # if a quit message is sent, server status is changed
                if messageSent == ":q":
                    self.peerServer.isChatRequested = 0
                    self.isEndingChat = True
                    break
            # if server is not chatting, and if this is not the ending side
            # sends a quitting message to the server of the other peer
            # then closes the socket
            if self.peerServer.isChatRequested == 0:
                if not self.isEndingChat:
                    self.tcpClientSocket.send(":q ending-side".encode())
                    logging.info(
                        "Send to "
                        + self.ipToConnect
                        + ":"
                        + str(self.portToConnect)
                        + " -> :q"
                    )
                self.responseReceived = None
                self.tcpClientSocket.close()


# main process of the peer
class peerMain:
    # peer initializations
    def __init__(self):
        global notifications
        # ip address of the registry
        self.hostname = gethostname()

        self.registryName = "localhost"
        # self.registryName = 'localhost'
        # port number of the registry
        self.registryPort = 15601
        # tcp socket connection to registry
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName, self.registryPort))
        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None

        self.username = None

        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            # menu selection prompt
            choice = input(
                Fore.MAGENTA
                + "\nChoose: \nCreate account: 1\nLogin: 2\nLogout: 3\nSearch: 4\nStart a chat: 5\nOnline Users: 6\nCreate room: 7\nJoin room: 8\nEnter room: 9\nShow notifications: 10\nShow all rooms: 11\n"
                + Fore.YELLOW
                + "> "
                + Fore.RESET
            )
            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1":
                username = input("username: ")
                password = input("password: ")
                password = hashlib.sha256(password.encode()).hexdigest()

                self.createAccount(username, password)
            elif choice == "11":
                rooms = db.db.rooms.find({})
                for room in rooms:
                    print_with_color(f"{room['name']}", Fore.LIGHTGREEN_EX)
            elif choice == "10":
                if len(notifications) == 0:
                    print_with_color("You have no new notifications ya lonely", Fore.YELLOW)
                for notification in notifications:
                    print_with_color(f"{notification}", Fore.LIGHTBLUE_EX)
                notifications.clear()
            elif choice == "7" and self.isOnline:
                username = input("roomname: ")

                self.createRoom(username)

            elif choice == "7":
                print_with_color("Please login", Fore.RED)
            elif choice == "8" and self.isOnline:
                username = input("roomname: ")

                self.joinRoom(username)

            elif choice == "8":
                print_with_color("Please login", Fore.RED)
            elif choice == "9" and self.isOnline:
                username = input("roomname: ")
                self.enterRoom(username)

            elif choice == "8":
                print_with_color("Please login", Fore.RED)
            elif choice == "2" and not self.isOnline:
                username = input("username: ")
                password = input("password: ")
                password = hashlib.sha256(password.encode()).hexdigest()
                # asks for the port number for server's tcp socket
                peerServerPort = int(input("Enter a port number for peer server: "))
                # peerServerPort = 3000
                
                hostname = gethostname()
                ip = gethostbyname(hostname)
                status = self.login(username, password, ip, peerServerPort)
                # is user logs in successfully, peer variables are set
                if status == 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort

                    self.sendHelloMessage()
                    chat = ChatServer(peerServerPort)
                    chat.start()
                    
            elif choice == "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient != None:
                    self.peerClient.tcpClientSocket.close()
                print("Logged out successfully")
            # is peer is not logged in and exits the program
            elif choice == "3":
                self.logout(2)
            # if choice is 4 and user is online, then user is asked
            # for a username that is wanted to be searched
            elif choice == "4" and self.isOnline:
                username = input("Username to be searched: ")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus != None and searchStatus != 0:
                    print("IP address of " + username + " is " + searchStatus)
            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "5" and self.isOnline:
                username = input("Enter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus != None and searchStatus != 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(
                        searchStatus[0],
                        int(searchStatus[1]),
                        self.loginCredentials[0],
                        self.peerServer,
                        None,
                    )
                    self.peerClient.start()
                    self.peerClient.join()
            elif choice == "6" and self.isOnline:
                self.listUsers()
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info(
                    "Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage
                )
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(
                    self.peerServer.connectedPeerIP,
                    self.peerServer.connectedPeerPort,
                    self.loginCredentials[0],
                    self.peerServer,
                    "OK",
                )
                self.peerClient.start()
                self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info(
                    "Send to " + self.peerServer.connectedPeerIP + " -> REJECT"
                )
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    def listUsers(self):
        message = "ONLINE_USERS"
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        print_with_color(response, Fore.BLUE)

    # account creation function
    def createAccount(self, username, password):
        message = "JOIN " + username + " " + password
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "join-success":
            print_with_color("Account created...", Fore.GREEN)
        elif response == "join-exist":
            print_with_color("choose another username or login...", Fore.RED)

    def createRoom(self, roomname):
        message = "CREATE " + roomname
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "create-success":
            print_with_color("Room created...", Fore.GREEN)
        elif response == "create-exist":
            print_with_color("choose another roomname...", Fore.RED)

    def joinRoom(self, roomname):
        message = "JOIN-ROOM " + roomname + " " + self.username
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)

        #print("Debug: Response from server:", response)  # Add this line for debugging

        if response == "join_room-success":
            print_with_color("Joined success...", Fore.GREEN)
            self.sendChatMessage("join", roomname)
        elif response == "already-exist":
            print_with_color("You are joined...", Fore.RED)
        elif response == "room-not-found":
            print_with_color("The chat room does not exist. Please choose another room or create a new one.", Fore.RED)

    def handleChatMessage(self, server: socket, roomname):
        while 1:
            c, a = server.accept()
            while 1:
                data = c.recv(1024)
                if data:
                    print(f"Recieved from {c} {data}")

    def sendChatMessage(self, message, roomname):
        message = f"group:{roomname}@{self.username}~{message}".encode()
        users = db.users_in_room(roomname)
        # print(f"Sending {message} to {users}")
        ips = []
        for user in users:
            if user != self.username:
                res = db.get_peer_ip_port(user)
                if res:
                    ips.append(res)
        # print(f"The ips are: {ips}")
        for ip in ips:
            singleSocket = socket(AF_INET, SOCK_STREAM)
            # print(f"Sending to {ip[0]} {ip[1]}")
            singleSocket.connect((ip[0], int(ip[1])))
            singleSocket.send(message)
            singleSocket.close()

    def enterRoom(self, roomname):
        global cuurentChat
        # cuurentChat = "asu"
        cuurentChat = roomname
        # Check if the room exists before entering
        if not db.is_room_exist(roomname):
            print_with_color(f"The chat room '{roomname}' does not exist. Please choose another room or create a new one.", Fore.RED)
            return        
        while 1:
            # input prompt for user to enter message
            messageSent = input("message in " + roomname + ": ")
            self.sendChatMessage(messageSent, roomname)
            if messageSent == "leave":
                print_with_color(f"Leaving the group {roomname}", Fore.BLACK + Back.CYAN)
                db.remove_user_from_room(roomname, self.username)
                break
            elif messageSent == "quit":
                print("Quitting")
                cuurentChat = None
                break

    # login function
    def login(self, username, password, ip , peerServerPort):
        message = "LOGIN " + username + " " + password + " " + ip + " " + str(peerServerPort)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "login-success":
            print_with_color("Logged in successfully...", Fore.GREEN)
            self.username = username
            return 1
        elif response == "login-account-not-exist":
            print_with_color("Account does not exist...", Fore.RED)
            return 0
        elif response == "login-online":
            print_with_color("Account is already online...", Fore.YELLOW)
            return 2
        elif response == "login-wrong-password":
            print_with_color("Wrong password...", Fore.RED)
            return 3

    # logout function
    def logout(self, option):
        # a logout message is composed and sent to registry
        # timer is stopped
        if option == 1:
            message = "LOGOUT " + self.loginCredentials[0]
            self.timer.cancel()
        else:
            message = "LOGOUT"
        self.tcpClientSocket.send(message.encode())

    # function for searching an online user
    def searchUser(self, username):
        message = "SEARCH " + username
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        if response[0] == "search-success":
            print(username + " is found successfully...")
            return response[1]
        elif response[0] == "search-user-not-online":
            print(username + " is not online...")
            return 0
        elif response[0] == "search-user-not-found":
            print(username + " is not found")
            return None

    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self):
        message = "HELLO " + self.loginCredentials[0]
        self.udpClientSocket.sendto(
            message.encode(), (self.registryName, self.registryUDPPort)
        )
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()


# peer is started
main = peerMain()
