from pymongo import MongoClient
from typing import List

# Includes database operations
class DB:
    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017')
        self.db = self.client["p2p-chat"]


    # checks if an account with the username exists
    def is_account_exist(self, username):
        if self.db.accounts.count_documents({'username': username})> 0:
            return True
        else:
            return False
    

    # registers a user
    def register(self, username, password):
        account = {
            "username": username,
            "password": password
        }
        self.db.accounts.insert_one(account)

    def create_chatroom(self, roomname):
        self.db.rooms.insert_one({"name": roomname, "users": []})
    
    def is_room_exist(self, roomname):
        if self.db.rooms.count_documents({'name': roomname})> 0:
            return True
        else:
            return False

    def join_room(self, roomname, username):
        print(f"starting to join {roomname}")
        room = self.db.rooms.find_one({"name": roomname})
        users_in_room: List[str] = room["users"]
        users_in_room.append(username)
        self.db.rooms.update_one({'_id': room['_id']}, {'$set': room})

    def remove_user_from_room(self, roomname, username):
        room = self.db.rooms.find_one({"name": roomname})
        users_in_room: List[str] = room["users"]
        users_in_room.remove(username)
        self.db.rooms.update_one({'_id': room['_id']}, {'$set': room})

    def is_user_in_room_exist(self, roomname, username):
        room = self.db.rooms.find_one({"name": roomname})
        print(f"found props for room: {roomname} are {room}")

        if room and "users" in room:
            users_in_room: List[str] = room["users"]
            if username in users_in_room:
                return True
            return False        

        # print(f"Users in room {users_in_room}")


    def users_in_room(self, roomname) -> List[str]:
        room = self.db.rooms.find_one({"name": roomname})
        
        users_in_room: List[str] = room["users"]

        print(f"Users in room {users_in_room}")

        return users_in_room

    # retrieves the password for a given username
    def get_password(self, username):
        return self.db.accounts.find_one({"username": username})["password"]


    # checks if an account with the username online
    def is_account_online(self, username):
        if self.db.online_peers.count_documents({"username": username}) > 0:
            return True
        else:
            return False

    def onlineUSers(self):
        users = self.db.online_peers.find()
        online_users = "Users: \n"
        for user in users:
            print(user["username"])
            online_users += user["username"] + "\n"
        # print(f"Online users {users}")
        return online_users
    
    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)
    

    # logs out the user 
    def user_logout(self, username):
        self.db.online_peers.delete_one({"username": username})
    

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        # print(f"Getting ip of {username}")
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"]) if res else None
    
    def clear_online_users(self):
        self.db.online_peers.delete_many({})