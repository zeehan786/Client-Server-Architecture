Developing a Command Line Application for Secure Transport Layer Communication
Group Members:
Josh:
Nick: 
Zeehan:
Project Idea:

The project concept was to develop a command-line application for communication between clients using TCP sockets that included several security features. Originally, the goal was to provide confidentiality and integrity as well as options for communication that supported asynchronous and synchronous bidirectional exchange of messages. For example, asynchronous “email” in the sense that it doesn’t require the receiving client to be online, but is instead retrievable upon next login. This requires the server to store messages for the clients. On the other hand, synchronous communication, i.e. real-time communication, was determined to be the best feature to support the security that was part of the project goal. The integrity feature was never implemented, instead the project evolved to focus on the different aspects of synchronizing communication between two clients and providing confidentiality. To provide that confidentiality, inspiration was drawn from transport layer security protocols like SSL/TLS. Although those protocols are far out of the scope of what we aimed to achieve, certain principles and concepts coming from their implementations served as the seeds of our own security development process. Along those lines, asymmetric and symmetric cryptographic algorithms were chosen to suit our protocol and implemented from the ground up. Incorporating those algorithms into our protocol involved synchronization of multiple processes, which ultimately when combined with bidirectional communication became the main effort of the project as a whole.

Implementations:
Even though we had the basic idea of encrypting messages between two clients, we first had to learn the fundamentals of socket programming. With thorough research (reference 1) we were able to have a decent understanding of implementing a generic client server model. In our very first implementation we set up a basic connection between a client and a server. In simple words, the client sends a message to the server and consequently waits for a reply from the server. We realized that clients were not able to send and receive messages at the same time (full duplex). This is where multithreading came into our project. The idea was to separate the receiving and sending part of the client in separate functions. As soon as the client program is run, two threads spawn off from the “start()” function. One thread runs the receive function while the other thread runs the send function, simultaneously.
Having learnt the basics of socket programming (Reference 2), we then implemented a basic model where a client establishes a connection with the server (that was already listening). Consequently, the server registers the client in its database (dictionary) through the functions (handle_client() -> RegisterNewCon()).
When the client is registered in the server’s database, the server offers different options: Join a chatroom (by pressing “J”) and chat with another online client with full encryption, send an email to someone, read inbox, or disconnect from the server by hitting “D”. These are implemented by simple if statements in the handle_client(..) function on the server side. As a result, with the server offering encryption to the clients in the chatroom, it also acts as a SMTP server by allowing clients to send emails to other clients and enabling clients to check their inbox. 
How does our server act as a SMTP server? The idea is simple. A client (say client A) enters the email address (name) of the receiver (say client B) and the message it wants to send. Following this, the server runs the SendEmail (…) function with the two inputs entered by the client A. In the SendEmail(receiver_name, message) function, the server creates a text file with the name: receiver_name and the content of the file: “message”.
Once the receiver (client B) logs in to the server, it can request the server (By pressing “R”) to check if someone has sent client B an email while client B was offline. The server runs the ReadMessage (…) function where it looks for a file named as the client B’s name and returns the content of the file to client B.

Security 
The security of our application is part of the “Chat Room” feature. This feature is designed to be like instant messaging, i.e. real time and bidirectional. In order to add confidentiality to this feature and make it secure, a combination of asymmetric and symmetric cryptographic algorithms were adapted. Symmetric encryption means encryption and decryption is done with the same key, whereas asymmetric encryption means there are separate keys for encryption and decryption. The implementation follows a common pattern whereby an asymmetric method is used to establish a key that can be used with a symmetric method. To stay within the scope of our project the symmetric method is a simple XOR cipher, based on the concept of the “One Time Pad” (OTP). The OTP is a provably secure cryptosystem that derives its security from the randomness of its key. For the asymmetric algorithm a simplified version of Diffie-Hellman is used, which gets its security from the computational infeasibility of doing brute force calculations relating to modular exponentiation.

Diffie-Hellman
Diffie-Hellman (DH) is an asymmetric cryptographic protocol, commonly referred to as a “Key Exchange Protocol”. Some would argue that “Key Establishment” would be more appropriate however, due to the fact that a key is never actually “exchanged” (in the sense that it never traverses the network). The fact that the key never traverses the network constitutes the core aspect of the security that DH provides. DH uses a combination of public and private keys to create a shared secret between two clients with a process based on principles of modular exponentiation. Consider that Alice and Bob have a shared secret, gxy mod N which is based on the publicly available key pair (g, N). Eavesdropper Eve has knowledge of the public information and also knows gx (mod N) and gy (mod N). Is this a problem? It is not, because even with the information Eve has, finding xy given gxy mod N is equivalent to solving the discrete log problem (DLP). That is, given g, ge=b, and N find the exponent e such that the equation geb (mod N) is satisfied. There are certain algorithms that attack discrete logs and do better than brute force, for example taking advantage of lack of randomness or poor choice of parameters. In this case the implementation was focused on achieving confidentiality and not resistance to cryptanalysis, so the parameter g is not chosen in the way that it would be realistically. The modulus N is a 1024-bit prime, generated and tested by custom cryptographic functions. Since DH is elegant it doesn’t require a lot of code to implement which made it the top candidate for our asymmetric component. In the context of sockets, even though the computational overhead for DH is relatively high, it is still possible to compute a key fast enough that a new one can be generated for almost every message. The whole DH algorithm can be found in the Algorithms Appendix.

Diffie-Hellman parameters
The DH protocol requires a base value that should have specific mathematical attributes to maximize security and a modulus commonly chosen as a large prime number. In a very rough sense, the base should be chosen such that it produces the maximum amount of possible values when exponentiated mod N to increase the infeasibility of brute force. To simplify, our implementation does not check that the base has the aforementioned mathematical properties. In addition, the secret values are chosen once in the chat room and reused. These are “big no-no’s” in the real world since reusing parameters can compromise the overall strength of the cryptosystem. The prime number is generated as 1024 bits which is a little small for DH from a security standpoint, but the implementation was basically throttled to that value by the fact that Python lacks speed for its convenience. That is to say, the cost of a convenient feature such as unbounded integers is the extra time that Python takes to do its job under the hood.

XOR cipher
To stay within the appropriate scope, the symmetric algorithm was chosen to be a simple XOR cipher. It is a straightforward way of directly using the shared secret that is obtained by both clients as a result of DH. In other words, the clients establish a key with DH that serves as the key for the XOR cipher, enabling symmetric encryption. This is possible because XOR has the property that it “undoes” itself. That is to say, ((a XOR b) XOR b) = a. Since XOR is associative, this can be demonstrated by moving the parentheses: (a XOR (b XOR b)).  The inner term reduces to 0 and (a XOR 0) = a. Therefore XOR as an operation can be used to encrypt a message on one end of communication and decrypt on the other. In order to use this method of encryption each message must be represented as an integer, which is accomplished by taking the uppercase ASCII encoding of each character and creating a string. Details of the XOR cipher are in the algorithm appendix.

Generating Primes
The prime number generator uses a combination of multiple Linear Feedback Shift Registers (LFSRs) to generate bits that can be added onto another integer to randomize it. The initial seed is an exponentiated version of system time with nanosecond precision. In the code the way this works is a 1024-bit integer is generated with the Python random library, and then the LFSR is seeded with the system time and used to generate a random 1023-bit number. The two are added together to get the randomized 1024-bit number for use as the Diffie-Hellman modulus. It is possible that the end result could be 1025 bits but that isn’t a problem for our implementation. Once the “random” integer is generated, it is tested for being prime. This involves a divisibility “filter” that checks for divisibility by all primes less than 2000. The reason for this step is that if a number passes it indicates that it is not divisible by a very high percentage of odd numbers, and therefore has a higher likelihood of being prime. When a number passes the “filter”, it is passed to an implementation of the Miller-Rabin probabilistic primality test. Miller-Rabin is a commonly used primality test that tests if a condition known to be true of primes is true for the number under examination. The underlying math is reliable in identifying numbers as probable primes with a success rate close to 100%. Although the algorithm can only identify probable primes, it can deterministically return whether a number is composite. In other words, there are no false negatives, only a very small possibility of false positives that can be mitigated by good testing practices such as repeating the test multiple times. If a number passes Miller-Rabin multiple times it greatly increases the confidence that it is prime.

Synchronization:
To ensure that the connection is stable throughout all of the encryption steps and message passing, we need to make sure all threads involved are synchronized so that they are reaching the correct sections when expected. There are a total of 6 threads involved in the connection sequence: The send and recv threads on client 1, the send and recv threads on client 2, and 1 server side thread per client. The send and recv function on each client side can share variables with each other, as can the two server side threads with each other. However, the send thread on each client side can only send to its corresponding server side thread, while both server side threads can send to either client program.

At the beginning of the connection when the clients first enter the lobby, the clients are not yet aware of each other. The server threads are responsible for informing the client threads about who else is in the lobby. If a client requests a connection with another client, the server threads will inform the recipient that someone is trying to connect with them. Once both clients agree on a connection, they will send a final confirmation message, which will inform the send thread in both client programs to lock themselves until the key exchange is completed. Now, the remaining 4 threads, the 2 server threads and the 2 recv threads, will start the key exchange.


All four threads will enter the KeyExchange function. Both the server side code and client side code have a KeyExchange function, and they are deliberately named the same as they correspond to one another. On the server side, we need to calculate and send the same public key info to both clients, but we want to avoid storing the key on the server side to minimize security issues, so the best way to approach this is to have one server side thread be responsible for calculating and sending the key to both clients. We decided to treat the public key sending as a critical section and have the first server thread to reach the critical section lock it and send out the public key, while the second thread would unlock the critical section and continue executing past. Both server threads will synchronize up when they are waiting to receive the half secret from their respective clients.

On both client sides, the recv functions will first wait to receive the public key from the server. Once they receive it, both clients will independently choose a secret value for themselves, and use this to calculate their respective half secret, which they will send out to their server threads. Since the send functions on the client side are currently locked, the recv functions temporarily take the responsibility of receiving user input and sending it to the server. When the server threads receive the half secret, they will simply forward it to the other client. Once each client receives the other’s half secret, they can use their secret value from before to calculate the full secret. At this point, the server threads and the recv functions are finished with the key exchange, and they can proceed into the chatroom. The recv functions unlock the send functions at this point so they can enter the chatroom as well.

In the chatroom, either side can send the first message. However, due to limitations of our project design, each side can only send one message before a new key needs to be sent out. The send functions will encrypt and send the message, the recv functions will receive and decrypt the messages, and the server threads will only forward the messages to the other party, without knowing the actual messages since they will be encrypted. When the send functions have sent their messages, they will lock themselves as they did at the start of the connection, and the recv functions will only proceed once they have both received a message and their corresponding send function has sent a message. After one round of messages, the send threads will be locked and the recv and server threads will continue with another key exchange, and the process will repeat itself.

Once one side of the connection is ready to leave, they will enter “D”. This also informs the send thread of that client to exit the chatroom. When the corresponding server thread receives this, it will notify both recv threads with a keyword to leave the function. The recv thread for the client that did not leave yet will also inform the send thread that it can leave as well. Once the server sees that the chatroom is empty, both server side threads will leave the chatroom. With that, all 6 threads are successfully able to end the connection and resume their normal execution.

Future Ideas: 

We are happy with what we achieved for this project. That being said, there are certain areas where we are aware of potential for improvement. This project was a crash course in multithreading and the demands of synchronizing multiple processes on client endpoints. This fact had the double impact of creating a learning curve with respect to threads and also decreasing emphasis on the aspects of the project that didn’t center on synchronization and achieving the desired communication features. In addition, there is a reason that SSL/TLS is the standard for communicating transport layer communications: it is complex and well-tested. That is to say, while our project aimed to deliver confidential communication between clients, the subject matter of security and cryptography extends far beyond both the scope of the course and the project itself. In short, while we accomplished our goal for this assignment, there are many opportunities for future projects based on extending it.










Contribution of each group members: (Equal Contributions)

Josh: Developed and refined the synchronization process during the connection sequence and drew up a visualization of the entire connection sequence to help with implementation. Refined and optimized the code after the initial structure to reduce bloat and busy waiting in the code. 


Nick: Developed project idea and initial starter code. Implemented all cryptographic features. Implemented keywords/headers as a way to synchronize threads without sleep(). Performed troubleshooting and testing.



Zeehan:

1. Built the client server architecture for the key exchange by implementing the following functions:
On the server side: handle_client(...), RegisterNewConn(..), JoinChatRoom(), KeyExchange(..), chatroom(..), SendEmail(..), ReadMesssage(..)
On the client side: recv(), send(), Enc_Rec(..), Enc_Send(), KeyExchange()
 (The description of each function are provided as comments in the code)
2. Enabled a new key exchange between two clients before every call to chatroom function. This required some crucial synchronization during the key exchange process between two clients
Busy waiting forced the server thread to wait for the second server thread before initiating the key exchange process
Busy waiting was also used on the client side. For example: Enc_Rec of the first client does busy waiting while the other client has not finished sending the message
Without these busy waiting and the necessary global variables, synchronization will not be maintained.   For example, a client would start the KeyExchange function and its server side will send the public key to the other client. However, since the receiver client is still in the chatroom expecting to receive encrypted messages, it will unexpectedly receive the public key instead. The runtime error will cause the program to crash
3. Incorporated the SMTP service in the server (client can send email to one another while the receiver is offline)
4. Enabled multithreading to make the client full duplex





Tools Used: Python. ‘socket’ and ‘threading’ libraries.


References:
Reference 1: (geeksforgeeks): https://www.geeksforgeeks.org/simple-chat-room-using-python/
Reference 2: (TechWithTim): https://www.youtube.com/watch?v=3QiPPX-KeSc&t=2207s
Reference 3: (Sequence Diagram): https://www.sequencediagram.org/



Algorithms Appendix
Diffie-Hellman algorithm
Parameters:
(g, N): public key pair
g: public base
N: modulus
x: Alice’s secret value
y: Bob’s secret value
Start:
Alice chooses a secret value x. She keeps x private.
Bob chooses a secret value y. He keeps y private.
Alice sends Bob 
gx mod N
Bob sends Alice gy mod N
(At this point an eavesdropper sniffing packets, say Eve, has theoretically seen both  gx mod N and gy mod N go over the network.)
Alice receives Bob’s gy mod N and computes (gy)x gxy mod N
Bob receives Alice’s gx mod N and computes (gx)y gxy mod N

XOR Algorithm
Parameters:
K: the key, a shared secret between Alice and Bob previously established with DH
M: the message to be encrypted, encoded as uppercase ASCII
C: the encrypted ciphertext
Start:
Alice computes M by concatenating the uppercase ASCII values of each character in the message into a string.
Alice computes 
M  K = C. This is a bitwise XOR operation between M and K.
Alice sends C to Bob.
Bob computes C  K = M.
Bob decodes the payload M from ASCII into the underlying message.

