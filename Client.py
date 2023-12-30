import hashlib
from socket import *
import threading
import time
import select
import logging


class Client:
    # peer initializations
    def __init__(self):
        # ip address of the registry
        hostname = gethostname()
        try:
            host = gethostbyname(hostname)
        except gaierror:
            import netifaces as ni
            host = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']
        self.serverName = host
        # self.serverName = 'localhost'
        # port  number of the registry
        #number da given aslan f el server.py
        self.serverPort = 15600
        # tcp socket connection to registry
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.serverName, self.serverPort))
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the client
        self.isOnline = False
        # server port number of this peer
        self.ServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None

        choice = "0"
        # log file initialization
        logging.basicConfig(filename="Client.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            # menu selection prompt
            choice = input("Choose: \nCreate account: 1\nLogin: 2\nLogout: 3\nSearch: 4\nStart a chat: 5\n")
            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1":
                username = input("username: ")
                password = input("password: ")

                self.createAccount(username, password)
            # if choice is 2 [log in] and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                username = input("username: ")
                password = input("password: ")
                password = hashlib.sha256(password)
                # asks for the port number for server's tcp socket
                ServerPort =15600

                status = self.login(username, password, ServerPort)
                # 1--> is user logs in successfully, peer variables are set
                if status == 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.ServerPort = ServerPort
                    # creates the server thread for this peer, and runs it
                    #self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    #self.peerServer.start()

                    # hello message is sent to registry
                    self.sendHelloMessage()
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice == "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                #self.peerServer.isOnline = False
                #self.peerServer.tcpServerSocket.close()
               # if self.peerClient is not None:
                #    self.peerClient.tcpClientSocket.close()
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
           # elif choice is "5" and self.isOnline:
           #     username = input("Enter the username of user to start chat: ")
           #     searchStatus = self.searchUser(username)
           #     # if searched user is found, then its ip address and port number is retrieved
           #     # and a client thread is created
           #     # main process waits for the client thread to finish its chat
           #     if searchStatus is not None and searchStatus is not 0:
           #         searchStatus = searchStatus.split(":")
           #         self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]), self.loginCredentials[0],
           #                                      self.peerServer, None)
           #         self.peerClient.start()
           #         self.peerClient.join()
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            #elif choice == "OK" and self.isOnline:
            #    okMessage = "OK " + self.loginCredentials[0]
            #    logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
            #    self.peerServer.connectedPeerSocket.send(okMessage.encode())
            #    self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort,
            #                                 self.loginCredentials[0], self.peerServer, "OK")
            #    self.peerClient.start()
            #    self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            #elif choice == "REJECT" and self.isOnline:
            #    self.peerServer.connectedPeerSocket.send("REJECT".encode())
            #    self.peerServer.isChatRequested = 0
            #    logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    # account creation function
    def createAccount(self, username, password):
        # join message to create an account is composed and sent to server
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        message = "JOIN " + username + " " + password
        logging.info("Send to " + self.serverName + ":" + str(self.serverPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.serverName + " -> " + response)
        if response == "join-success":
            print("Account created...")
        elif response == "join-exist":
            print("choose another username or login...")

    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to server
        # an integer is returned according to each response
        message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
        logging.info("Send to " + self.serverName + ":" + str(self.serverPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.serverName + " -> " + response)
        if response == "login-success":
            print("Logged in successfully...")
            return 1
        elif response == "login-account-not-exist":
            print("Account does not exist...")
            return 0
        elif response == "login-online":
            print("Account is already online...")
            return 2
        elif response == "login-wrong-password":
            print("Wrong password...")
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
        logging.info("Send to " + self.serverName + ":" + str(self.serverPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())

    # function for searching an online user
    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        message = "SEARCH " + username
        logging.info("Send to " + self.serverName + ":" + str(self.serverPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.serverName + " -> " + " ".join(response))
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
        #logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
       # self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()
main = Client()