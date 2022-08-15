import socket
import threading
import time
import random
from datetime import datetime


HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

ActiveUsers = {}  # Dictionary containing all socket objects connected to the server
# Used to convert human-readable usernames to socket objects
Username = {}  # Dictionary containing the username of each socket object
# Used to convert socket objects to human-readable usernames
# Dictionary containing all users in or looking for an active connection
GetReceiverName = {}
# Format: {receivingthread | senderthread} represents that the sender wants to connect with receiver
ChatRoomUsers = {}  # Dictionary containing the users in the chatroom
# Global variable containing the number of users in the chatroom, and is used for indexing
chatroomcount = 0
mess = ""  # Global variable to maintain the message between chatroom and keyexchange
# UNDER SCRUTINY. REEVALUATE LATER
First = True  # Flag indicating if the public key needs to be sent
KeyReady = 0  # Flag indicating if both half secrets are received
OtherRound = 0  # Flag preventing each client from sending more than 1 message per round

Menu = "\nChoose the appropriate option:" + "\n" + \
    "(R)ead Inbox"+"\n" + "(J)oin Chat Room" + \
      "\n" + "(D)isconnect \n"+"(S)end an email\n"
# Displays the full menu. Might not need a variable for this


# Function to handle user input in the main menu
def handle_client(newconn, addr):

    try:
        print(f"[NEW CONNECTION] {addr} connected.")

        #newconnection = True
        #userchoice = ""
        username = RegisterNewCon(newconn)##the server uses this function to basically registers the user userchoice = Userinfo["userchoice"]      
        #username = Userinfo["username"]
        #newconnection = False
        #userchoice = Userinfo["userchoice"]

        while True:

            # Moved this section outside the loop since it's only being called once anyway
            '''
            if newconnection:##true only for the first, so that the client can register their name to the server

                ##the server uses this function to basically registers the user userchoice = Userinfo["userchoice"]
                Userinfo = RegisterNewCon(newconn)

                username = Userinfo["username"]
                newconnection = False
                userchoice = Userinfo["userchoice"]
            '''                
            newconn.send((Menu).encode(FORMAT))      
            #userchoice = ""
            userchoice = newconn.recv(1024).decode(FORMAT)
            
            if(userchoice == "J"):
                JoinChatRoom(newconn, username)##before entering the chatroom client has to go through this func
                #userchoice = Continue(newconn)##Continue func basically gets the client ready to make more choice
                continue

            if(userchoice == "R"):
                userinbox = ReadMessage(username)
                if(userinbox == "Inbox Empty"):
                    newconn.send("File Not Found".encode(FORMAT))

                userinbox += "\n --------------------"
                newconn.send(userinbox.encode(FORMAT))##retrives the content from the file and send it to the requester
                time.sleep(3)##I noticed some messages were being out of order, therefore time ensures order
                #userchoice = Continue(newconn)
                continue

            if(userchoice == "S"):
                newconn.send("Enter the name of the receiver".encode(FORMAT))
                receivername = newconn.recv(1024).decode(FORMAT)
                newconn.send("Enter your message: ".encode(FORMAT))
                message = newconn.recv(1024).decode(FORMAT)

                SendEmail(username, receivername, message)
                time.sleep(3)
                newconn.send("Message successfully sent ".encode(FORMAT))
                # time.sleep(3)

                #userchoice = Continue(newconn)
                continue

            if(userchoice == "D"):
                newconn.send("Thank you for using Socket Chat".encode(FORMAT))
                newconn.send("D".encode(FORMAT))
                break

            # not sure if it works the way is supposed to
            userchoice = str(userchoice)
            newconn.send(("\nIncorrect choice: "+userchoice +
                         "\nPlease try again:").encode(FORMAT))

            #userchoice = Continue(newconn)
            continue

        del Username[newconn]
        del ActiveUsers[username]
        newconn.close()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

    except ConnectionResetError:  # If the client closes the window directly
        print("User forcibly closed the connection")
        del Username[newconn]
        del ActiveUsers[username]
        newconn.close()

        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

        return  # DeleteUser(newconn)

# Function to add the users info to the server


def RegisterNewCon(newconn):

    # just some work of registering the user to the server
    #newconn.send("Enter your username".encode(FORMAT))
    username = newconn.recv(1024).decode(FORMAT)
    #Userinfo = {}##this dictionary will be return by the function, the dict stores the username and choice of user
    #Userinfo["username"] = username
    print(username+ " joined")

    newconn.send(("Welcome "+username).encode(FORMAT))   
    #userchoice = newconn.recv(1024).decode(FORMAT)

    #Userinfo["userchoice"] = userchoice

    ActiveUsers[username] = newconn

    Username[newconn] = username

    return username

# Function to handle the user in the chatroom lobby


def JoinChatRoom(newconn, username):
    # newconn is the initiator
    global chatroomcount
    chatroomcount += 1
    ChatRoomUsers[username] = chatroomcount
    print("how are you")
    if len(ChatRoomUsers) <= 1:
        newconn.send(
            ("No one else is here. Press d to leave the chatroom").encode(FORMAT))

        while len(ChatRoomUsers) <= 1:
            # inside the try section, the user has only 2 seconds to input, if the user does
            # not enter withins 2 seconds(an error is thrown and loop continues), the server checks for online users again
            try:
                newconn.settimeout(2.0)
                msg = newconn.recv(1024).decode(FORMAT)
                newconn.settimeout(None)
            except socket.timeout:
                print(".")
                newconn.settimeout(None)
                continue

            if msg == "d":
                del ChatRoomUsers[Username[newconn]]
                chatroomcount -= 1
                return
            continue

    newconn.send(("The list of active users are:\n"+str(ChatRoomUsers) +
                 "\nType the name of the person to chat with").encode(FORMAT))

    while True:
        try:
            recusername = newconn.recv(1024).decode(FORMAT)
            if(recusername == username):  # Prevents the user from initiating a connection with themselves
                newconn.send(
                    ("You cannot chat with yourself. Try Again").encode(FORMAT))
                continue
            elif(recusername == 'Y'):  # A fast way for a user to accept a connection when pinged
                # Sets the receiver to the person trying to connect with them
                recusername = GetReceiverName[username]
                # retrieves the socket object using the name of the receiver
                receiverobj = ActiveUsers[recusername]
                break
            # Checks to make sure the given username is currently in the lobby
            ChatRoomUsers[recusername]
            # retrieves the socket object using the name of the receiver
            receiverobj = ActiveUsers[recusername]
            break
        except KeyError:  # If the user gives an incorrect input
            newconn.send(
                (recusername+" is offline\nType the name of the person to chat with").encode(FORMAT))
            continue

    GetReceiverName[recusername] = username
    newconn.send(("Setting things up...Hang on a moment").encode(FORMAT))
    if not username in GetReceiverName:  # Checks if the receiver is already trying to initiate a connection back
        # prepares the client send() to enter encrypted mode
        newconn.send(("Type Y to proceed").encode(FORMAT))
        while newconn.recv(1024).decode(FORMAT) != 'Y':
            continue
        # pings the receiver that this client is trying to initiate a connection
        receiverobj.send(
            (username+" wants to chat. Type Y to confirm").encode(FORMAT))
    # 29332 header indicates that the client recv() should enter encrypted mode
    newconn.send(f"29332{recusername}".encode(FORMAT))
    while True:  # The initiator waits in this thread until the receiver responds
        try:
            # Checks if the receiver has recipricated the connection
            GetReceiverName[username]
            break
        except KeyError:
            time.sleep(3)
            continue
    #error when server is robust################################

    print("[*] Step 0 ")
    # KeyExchange(same name) also starts in the client side
    KeyExchange(newconn, receiverobj)
    return

################################################

# Function where clients send messages


def chatroom(senderobj, receiverobj):

    global mess, OtherRound

    #senderobj.send(("Type your message below: ").encode(FORMAT))
    mess = senderobj.recv(1024).decode(FORMAT)
    if mess == "D" or len(ChatRoomUsers) <= 1:

        # also send a message 'D' to stop the function Enc_Rec() in the receiver side

        if mess == "D" and len(ChatRoomUsers) == 2:
            # Enc_Rec in client's sender side stops
            senderobj.send(("D").encode(FORMAT))
            senderobj.send(("You have left the chatroom").encode(FORMAT))
            #senderobj.send(("Chatroom session is over").encode(FORMAT))
            # Enc_Rec in client's receivercd side stops
            receiverobj.send(("D").encode(FORMAT))
            receiverobj.send(
                ("The other person has left the chatroom. Enter any key to exit").encode(FORMAT))
            #receiverobj.send((Username[senderobj]+" has left the meeting. Press any key to exit").encode(FORMAT))
            #global KeyReady
            # KeyReady = 0#preparing these variables for the next round if the clients again join the chatroom after exiting
        mess = "D"  # Ensures that the second person to leave the chatroom correctly leaves KeyExchange
        DeleteUser(senderobj)
        return

    # josh forward the encrypted message to nick (nick also does the same)
    receiverobj.send((mess).encode(FORMAT))
    print(f'[*] Printing encrypted message: {mess}')
    #StoreMessages(Username[senderobj] + ": "+mess,receiverobj, senderobj)
    OtherRound += 1
    print(f'[*] The current val of OtherRound is {OtherRound}')
    while OtherRound < 2:  # josh cannot finish the current round unless nick is also done with sending message to josh in that same round
        time.sleep(3)
        print(f'[*] Still sleeping, OtherRound = {OtherRound}')

    # chatroom ends (note: chatroom while loop functionality has been transferred to KeyExchange that iteratively calls chatroom)
    return
    #mess = senderobj.recv(1024).decode(FORMAT)


################################################

# Function to distribute the public key and half secrets
def KeyExchange(senderobj, receiverobj):
    # mess is global variable and loop terminates when mess="D" (mess can equal to "D" in chatroom)
    while mess != "D":
        print("[*] came here")
        print("[*] Step 1")
        global First
        if First:
            First = False
            ReCalc_PublicKey(senderobj, receiverobj)
            print("[*] public key sent")
            # send g,N to both the clients
        else:
            First = True
            '''
        Waiting += 1
        while Waiting < 2:
            time.sleep(3)
            '''
        # SYNC A (there is also "SYNC A" in clients KeyExchange function, so it easier to understand which line in the client
        # side, the receiving occurs)
        # senderobj.send(public_key.encode(FORMAT))

        # time.sleep(3)

        print("[*] Step 2")

        # receive the half secret from the client(say josh is client and his receiver is nick)

        # SYNC B
        half = senderobj.recv(1024)
        print("[*] Step 3")
        global KeyReady
        KeyReady += 1  # at this point we make sure nick and josh server thread remain close to each other: eg: josh will not
        # go ahead of line 257 unless nick also reaches line 257 (ofcousrse nick and josh are runnning different server threads)

        while KeyReady != 2:
            time.sleep(0)
            # continue
        # and then exchange the half secret
        # SYNC C
        receiverobj.send(half)

        print("[*] Step 4")

        global OtherRound
        # if OtherRound == 2:##setting OtherRound to 0, to get it ready for the upcoming round of sending messages in chatroom
        OtherRound = 0
        chatroom(senderobj, receiverobj)
        # if KeyReady == 2:####setting KeyRound to 0, to get it ready for the upcoming round of sending messages in chatroom
        KeyReady = 0
        print("[*] One Iteration Done")
    return

################################################

# Function for one server side thread to send out the public key to both clients


def ReCalc_PublicKey(senderobj, receiverobj):
    prime = get_prime(1024)
    public_key = f'5 {prime}'
    senderobj.send(public_key.encode(FORMAT))
    receiverobj.send(public_key.encode(FORMAT))
    return  # public_key


# ********************** Crypto Functs *************************
# **************************************************************
# **************************************************************

''' This function represents a single LFSR.
    The parameters are an initial fill and an
    array of tap indices. The LFSR goes through
    an iteration and returns the next fill.
    The output bit is gotten in the ilfsr()
    function which calls lfsr().
'''
def lfsr(start, tap_array):
    temp = start
    for tap in tap_array:
        temp ^= (start >> tap)
    # function is hard coded for deg-32 polys
    temp = (temp & 1) << 31 | (start >> 1)
    start = temp
    # print(start & 1, end='')
    return start


''' This function is used to build the 
    "filter" that is a part of the prime
    test. It is a naive algorithm that
    does trial division on a number by
    odds up to its square root to find
    primes.
'''
def naive_isPrime(x): # helper function to identify small primes by trial division
    x = abs(int(x))
    if x < 2:
        return False
    elif x == 2:
        return True
    elif x % 2 == 0:
        return False
    else:
        for n in range(3, int(x**0.5)+2, 2):
            if x % n == 0:
                return False
        return True

''' This is an implementation of the widely
    used Miller-Rabin probabilistic primality
    test. Right now the second parameter isn't
    being used. This means we are only running
    MR once on each big number. Fine for our
    purposes but not ideal IRL.
'''
def miller_rabin(n, k): 

    if n == 2:
        return True
    l = n - 1  # holds the value of n-1
    m = l
    b = 0
    while m % 2 == 0:
        b += 1
        m >>= 1
    m = int(m)
    a = int(random.randrange(1, l))
    j = 0
    b0 = pow(a, m, n)
    if b0 == 1 or b0 == l:
        #print("n is probably prime: ", n)
        return True
    else:
        b1 = pow(b0, 2, n)
        # print("b1 = ", b1)
        while True:
            j += 1
            if(b1 == 1):
                # print("n is composite")
                return False
            elif(b1 == l):
                #print("n is probably prime: ", n)
                return True
            elif(j > b and b1 != l):
                # print("max iterations reached. n is composite")
                return False
            b1 = pow(b1, 2, n)
            # print("b1 = ", b1)


''' This is the primality test that 
    combines the filter of dividing
    by small primes and Miller-Rabin.
'''
def prime_test(n, smallPrimes): 
    for k in range(len(smallPrimes)):
        if n % smallPrimes[k] == 0:
            # print("n is composite")
            return False
    return miller_rabin(n, 1) # if the input passes the divisibility trials, pass it to miller rabin

''' this function returns an array of all
    primes less than 2000. The array is 
    used as a filter when checking for
    primes.
'''
def getSmallPrimes(a, b):
    t = {}
    t[0] = 2  # manually set 2 as prime
    ctr = 1
    if a % 2 == 0:  # start odd
        a += 1
    for x in range (a, b, 2):  # only check odds
        if naive_isPrime(x):
            t[ctr] = x
            ctr += 1
    return t


''' This function combines multiple LFSRs.
    seeds is an array of initial fills for
    the multiple registers. length is the 
    desired amount of bits.
'''
def ilfsr(seeds, length):
    # the function is hard coded for deg-32 polys
    # to avoid referencing another parameter
    # polys = getPolys(src, 32)
    polys = [[25, 27, 29, 30, 31], [25, 26, 30], [ # array of degree-32 primitive tap polynomials
        25, 26, 27, 28, 30], [24, 27, 30], [24, 26, 27, 28, 31]]
    N = len(polys)
    i = 0
    # output is one bit per lfsr per while loop
    # so the number of loops needed is length / N
    res = ''
    while(i < length / N):
        for k in range(N):
            seeds[k] = lfsr(seeds[k], polys[k])
            res += str(seeds[k] & 1)

        i += 1
    return int(res, 2) # return as a decimal


''' This function is a pseudorandom number
    generator. The parameter is the desired 
    length in bits of the output. Uses LFSR
    seeded with nanosecond precision time.

    It's possible that this function returns
    a 1025-bit number instead of 1024, but
    that doesn't affect our implementation.
'''
def gen_random(output_length):
    fluff = time.time_ns()
    seeds = [(pow(fluff, i) % pow(2, 32)) for i in range(1, 6)]
    random_bits = ilfsr(seeds, output_length - 1) # obtain a random number with (output_length - 1) bits
    base = nbit(output_length) # obtain a number w/ output_length bits from random library
    rand_int = base + random_bits # add the randomization to the non-random base
    return rand_int + 1 if rand_int % 2 == 0 else rand_int # right now the function will return odds only


''' This function takes a number of bits
    as input and returns a "random" n-bit
    integer. The built-in random function
    isn't secure, so this shouldn't be 
    the only source of randomness.
'''
def nbit(n):  
    num = random.randrange((2 ** (n-1)) + 1, (2 ** n) - 1) 
    if num % 2 == 0:
        num += 1
    return num


''' This is the function that gets called
    for the key exchange. It combines 3 
    utility functions to return a prime
    with the specified number of bits
    as a string of decimal digits.
'''
def get_prime(bits): 
    # find a way to make this accessible so it doesn't have to be recomputed every time
    smallPrimes = getSmallPrimes(1, 2000)
    t1 = time.perf_counter()
    q = gen_random(bits)
    while prime_test(q, smallPrimes) == False:
        q = gen_random(bits)

    elapsed = time.perf_counter() - t1
    print(f'[*] {elapsed} sec to generate {len(bin(q))-2}-bit prime')

    return str(q)


# Commenting out this function since it's not being used
'''
def StoreMessages(savemess, recobj, sendobj):##store in the text file
    
    Recfilename = Username[recobj]+".txt"
    recfile = open(Recfilename, 'a')
    recfile.write("\n"+savemess+"\n")

    ##since savemess is mutual to both rec and send, it is posted to both their "database"

    Sendfilename = Username[sendobj] + ".txt"
    senfile = open(Sendfilename, 'a')
    senfile.write("\n"+savemess+"\n")

    return
'''
################################################

# Function to open the message inbox

def ReadMessage(username):
    try:
        with open(username+".txt") as f:
            contents = f.read()
            return contents

    except IOError:
        return "Inbox Empty"

################################################

# Function to send a message to a user

def SendEmail(sendername, receivername, message):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    receivername += ".txt"
    recfile = open(receivername, 'a')
    recfile.write("\n"+sendername+" texted you while you were away \n"+message+" -----" + str(current_time))

################################################
'''
#Function to prepare for next user input in the menu
def Continue(newconn):
    newconn.send((Menu).encode(FORMAT))
    userchoice = ""
    userchoice = newconn.recv(1024).decode(FORMAT)
    return userchoice
'''
################################################

# Function to remove the user from the chatroom
def DeleteUser(senderobj):  # does the job of deleting the user from dict once they leave the chatroom
    try:
        del ChatRoomUsers[Username[senderobj]]
        del GetReceiverName[Username[senderobj]]
        global chatroomcount
        chatroomcount -= 1
        return
    except KeyError:
        return

################################################


def start():
    server.listen()

    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

################################################


print("[STARTING] server is starting...")
start()  # all starts here
