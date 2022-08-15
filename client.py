import socket
import time
import threading


HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

OtherRound = 0 #NVM I think it does
#sendmsg = "" #Global variable that holds the messages sent by the client
#recmess = "" #Non-encrypted receive messages and also a lock for encrypted send I think?
#Pretty sure this also doesn't work as intended
sendlock = True
#username = ""
full_secret = "" #Holds the full secret for both encrypting and decrypting
recmsg = "" #Encrypted receive messages

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

#Functions to encrypt and decrypt the messages
def Encrypt(msg):
    uppercase = msg.upper()
    encoded = ""

    for b in uppercase:
        encoded += str(ord(b))
    ENC = str(int(encoded) ^ full_secret)

    return ENC

def Decrypt(enc):
    MSG = ""
    encoded = enc ^ full_secret
    encoded = str(encoded)
    
    for c in range(0, len(encoded), 2):
        MSG += chr(int(encoded[c:c+2]))

    return MSG

##################################################
'''
def ChooseSecret():
   
    secret_val = str(input("Choose a secret value:"))

    KeyExchange(secret_val)

    return secret_val
'''    
######################################################

#Function to receive the key for encryption
def KeyExchange():
    
    #SYNC A: receive g,n from the server
    pub = client.recv(1024).decode("utf-8") # Receive the public key

    ##calculate the half secret
    pub_data = pub.split()

    g = int(pub_data[0])
    N = int(pub_data[1])
    secret_val = str(input("Choose a secret value:"))
    half_secret = pow(g, int(secret_val), N)

    #SYNC B:send the half secret to the receiver
    client.send(str(half_secret).encode("utf-8"))  

    #SYNC C: receive the other half secret from the server
    other_half = client.recv(1024).decode("utf-8")

    ##calcualte the full secret
    global full_secret
    full_secret = pow(int(other_half), int(secret_val), N)
    
    global sendlock
    sendlock = False#unlocks the send(before first round) or Enc_Send(following rounds)

    return

######################################################

def Enc_Rec(rec_name):
    global recmsg, OtherRound
    DEC = ""
    while True:        
        recmsg = (client.recv(1024).decode(FORMAT))

        #when server gets to know that one of the client has hit D, it
        #sends "D" to both the clients, so their Enc_Rec() can also return
        if str(recmsg) == "D":
            #Consider adding a print statement here to inform the other side?
            print(client.recv(1024).decode(FORMAT))
            return

        DEC = Decrypt(int(recmsg))
        
        print(rec_name+": "+DEC)

        while OtherRound < 1:
            time.sleep(5)

        #print("Type your message below:")
        KeyExchange()
        OtherRound = 0
        global sendlock
        sendlock = False

######################################################
    
def Enc_Send():
    global recmsg, OtherRound
    while True:
        #ask user for the input and then encrypt the message
        enc_msg = (input("Type your message:\n"))

        #before encrypting, we are checking the first condition: enc_msg == "D",
        #so we can return and also let the server side know(line 119)
        #the second condition is when the other clients hits D, so this send func checks
        #if my Enc_Recv() received a "D" from the server thread of the other client (line 201 in server side)
        #this send func is able to know if its Enc_Rev received "D" since recmsg is a global variable
        if str(enc_msg) == "D" or str(recmsg) == "D":
            client.send(str(enc_msg).encode(FORMAT))
            OtherRound = 0
            recmsg = ""
            return

        enc_msg = Encrypt(enc_msg)

        #send the encrypted text
        client.send(enc_msg.encode(FORMAT))

        OtherRound +=1#to keeping track of the client who is
        #done sending a message in a specific round, since only one
        #message can be sent per client (so total: two mess per round)
        print("Please Wait...")##so user does not keep sending messages
        global sendlock
        sendlock = True
        while sendlock:##wait for KeyExchange to occur before going
            # to the next iteration of Enc_Send()
            time.sleep(1) 

######################################################

def recv():
        #global recmess
        #Need to replace global variable recmess with something else
        while True:
            recmess = (client.recv(2048).decode(FORMAT))
            ##if recmessage == 29332, start the KeyExchange Function: line 173 of server is the sender
            '''
            added the '29332' as a "header" in the message containing the receiver_name
            to avoid the problem of receiving quickly twice in a row
            '''
            if(recmess[:5] == "29332"):
                receiver_name = (recmess[5:])#line 177 of server is the sender
                KeyExchange()
                Enc_Rec(receiver_name)
                continue
            elif recmess == "D":
                break
            print(recmess)

        return



######################################################

def send():
#Desktop\Documents\Courses\CSCI 348\Project
    global sendlock
    sendmsg = ""
    while sendmsg != "D":
        sendmsg = str(input()) 

        message = sendmsg.encode(FORMAT)
        client.send(message)

        if sendmsg == "Y":
            #problem: wrong input no chance
            #sendmsg = str(input())
            #message = sendmsg.encode(FORMAT)
            #client.send(message)

            while sendlock:#waits for KeyExchange to finish (KeyExchange is called in recv() -> ChooseSecret())
                time.sleep(0)#yields to its recv()
            
            Enc_Send()

    #message = sendmsg.encode(FORMAT)
    #client.send(message)
    print("exiting")
    return

######################################################

  ######int main() like in C#######
  
thread1 = threading.Thread(target=recv)
thread1.start()

username = str(input("Enter your username: "))
message = username.encode(FORMAT)
client.send(message)

#time.sleep(2)

thread2 = threading.Thread(target=send)
thread2.start()
