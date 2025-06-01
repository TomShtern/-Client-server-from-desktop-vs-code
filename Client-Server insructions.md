--- Page 1 ---

# Assignment 15 (Maman 15)

**Course:** Defensive Systems Programming - 20937
**Study Material for Assignment:** Units 1-5; Bonus question on Chapter 7.
**Number of Questions:** 2 + 1 Bonus
**Assignment Weight:** 14 points
**Semester:** K2024 (Likely Spring 2024)
**Submission Deadline:** 24.3.2024

## Question 1 (80%)

In this exercise, you will implement a server and client program that allows clients to transfer files encrypted from their computer for storage on the server. The server will be written in Python, and the client will be written in C++.

**Important!**
Read the entire assignment carefully before starting work. Ensure you fully understand the communication protocol and the structure of the server and client programs.

### Architecture

The program's architecture is based on a client-server model. The client initiates contact with the server, exchanges encryption keys with it, and then transfers the requested file via encrypted communication. The client verifies that the server received the file correctly by comparing a checksum on both sides. If it didn't transfer correctly, it tries to send again (up to 3 attempts). Page 3 describes the system's flow chart.

### Server

The server's role is to manage the list of registered users for the service and allow them to exchange messages (files in this context) of various types.

**Server Requirements:**
a.  The server will be written in **Python**. The version for testing is **3.11.4**.
b.  The server will support multiple users using **threads** or **selector**.
c.  The server version will be **3** (this version appears in communication messages from the server).
d.  The server will operate with the **PyCryptodome** encryption package, and otherwise only with standard libraries included in the interpreter.

### Port

The server will read the port number from a text file as follows:
*   **File Name:** `port.info`
*   **File Location:** In the same directory as the server's source code files.
*   **File Content:** Port number
    *   Example:
        ```
        1234
        ```
*   **Data (This seems to be a formatting artifact in the original, the example `1234` is the content)**

--- Page 2 ---

The server will store client data and saved files in RAM. It will also maintain a local directory that will contain the files received from clients.

### Server Operation Mode

1.  Reads the port from the `port.info` file. (If the file does not exist, issue a warning and work on default port **1256**. Do not crash with a Traceback if the file is not available.)
2.  If you choose to answer question 3 (bonus): The server checks the database, if it already exists, and loads data of clients registered in previous runs.
3.  Waits for requests from clients in an infinite loop.
4.  Upon receiving a request, decodes the request according to the protocol:
    a.  **Registration Request:** If the requested username already exists, the server will return an error. Otherwise, the server will generate a new UUID for the user, save the data in memory and in the database (if Q3 is implemented), and return a success response.
    b.  **Public Key from Client:** The client's public key will be received and updated in the database. In response, the server will generate an AES key, encrypt it using the client's public key, and send it back to the client.
    c.  **Message with Encrypted File:** The server will decrypt the encrypted file using the original AES key sent to that client and will calculate the CRC (which is the value obtained from a `checksum` operation). The calculation, on the server and client, must be identical to the `cksum` command in Linux.
        (See: `https://www.howtoforge.com/linux-cksum-command`)
        In Unit 7, you can find code for `checksum` calculation to use.
    d.  The server will receive a success message from the client (CRC verified) or a re-send of the file up to 3 times.

A diagram of the main communication process between the server and client is attached.

--- Page 3 ---

### Client-Server Communication Flow (Diagram Description)

**Client** -> **Server**
1.  Client: `Registration Request` -> Server: `Accept`
2.  Client: `Generate RSA pair, Send public Key` -> Server: `Receive, Generate AES Key, Encrypt with public key & send to client`
3.  Client: `Encrypt file with AES key, Send encrypted file to server` -> Server: `Decrypt file, Calculate checksum, Send to client`
4.  Client: `Check sum ok?`
    *   If **No**:
        *   `Re-send` (up to 3 times) -> (Go back to step 3, client sends encrypted file again)
        *   If **No (4th time)**: `Send abort message`
    *   If **Yes**: -> Server: `Accept`

--- Page 4 ---

### Client

The client program will know how to communicate with a server, register (if not already registered from a previous run), exchange encryption keys, and then securely transfer a file from the client to be stored on the server. The client does not communicate with or is aware of other clients in the system.

**Client Requirements:**
a.  The client program will be written in **C++** compatible with version **17**, and will be tested by us using **Visual Studio 2022**.
b.  The client will operate according to a fixed sequence of operations, so it can be run in **Batch mode**.
c.  The client will be based on encryption using the **CryptoPP** library.
d.  The client version will be **3**.

### Client Instructions File (`transfer.info`)

*   **File Name:** `transfer.info`
*   **File Location:** In the same directory as the executable file (`.exe`).
*   **File Content:**
    *   Line 1: IP address + colon + port number
    *   Line 2: Client name (string up to 100 characters)
    *   Line 3: File path to send to the server.
    *   Example:
        ```
        127.0.0.1:1234
        Michael Jackson
        New_product_spec.docx
        ```

### Client Name and Unique Identifier (`me.info`)

The client will save and read its name and unique identifier from a text file as follows:

*   **File Name:** `me.info`
*   **File Location:** In the same directory as the executable file (`.exe`).
*   **File Content:**
    *   Line 1: Name
    *   Line 2: Unique identifier in ASCII representation where every two characters represent a hex value of 8 bits.
    *   Line 3: Private key generated during the first run of the program in Base64 format.
    *   Example:
        ```
        Michael Jackson
        64f3f63985f04beb81a0e43321880182
        MIGdMA0GCSqGSIb3DQEBA...
        ```

### Error from Server Side

In any case of an error, the client will print to the screen the message: `"server responded with an error"` and will try to send the message again, up to 3 times. If it still doesn't succeed, it will exit with a detailed Fatal error message.

1.  In this exercise, a Globally Unique Identifier (UUID) is used. For more information: `https://en.wikipedia.org/wiki/Universally_unique_identifier`

--- Page 5 ---

### Possible Client Actions

#### Registration Request
1.  If the `me.info` file does not exist, the client will read the username from the `transfer.info` file and send a registration request to the server.
2.  The client will save the name and the unique identifier it receives from the server in the `me.info` file.
3.  If the file already exists, the client will instead send a request for reconnection to the server. In this case, RSA keys will not be exchanged anew, and the previous key from the `priv.key` file will be used.
    **Note!** If the file already exists, the client will not register again.

#### Public Key
The client will generate an RSA key pair (public and private), send the public key to the server, and save the private key in a `priv.key` file.
(For reconnection, this file will be reused, and new RSA keys will not be generated).
In response, the server should send an AES key encrypted with the public key.

#### Receiving AES Key and Encrypting the File
After the client receives the AES key, it decrypts the key using its RSA private key and receives the AES key. In response, it encrypts the file it needs to transfer using this key and sends the encrypted file to the server. Concurrently, it should calculate the CRC of the file so it can compare it to the CRC received from the server.

#### Authentication of Sending via CRC
The server should receive the encrypted file from the client, decrypt it using the AES key, and also calculate the CRC and send it to the client for verification.

### Communication Protocol

#### General
*   The protocol is binary and implemented over TCP.
*   All numeric fields must have values greater than zero (unsigned) and are represented as **little-endian**.
*   This protocol supports requests to the server and responses to the client. Requests or responses can contain a "message."
*   A message is transferred between clients (implicitly, via the server).

**Remember!** The protocol is binding and cannot be changed. Consequently, any server and client implementing the protocol can work with each other.

#### System Registration
1.  Every client connecting for the first time registers with the service with a name (string, max length 255 bytes) and transfers its public key.
2.  The server will return to the client a unique identifier generated for it or an error if the name already exists in the database.

--- Page 6 ---

### Protocol Details

#### Requests
Structure of a request from the client to the server. The server will decode the content (payload) according to the request code.

**Request to Server Structure:**

| Field       | Size              | Meaning                                     |
| :---------- | :---------------- | :------------------------------------------ |
| **Header**  |                   |                                             |
| Client ID   | 16 bytes (128 bits) | Unique identifier for each client           |
| Version     | 1 byte            | Client version number                       |
| Code        | 2 bytes           | Request code                                |
| Payload size| 4 bytes           | Size of the request content (payload)       |
| **Payload** |                   |                                             |
| payload     | Variable          | Request content. Varies according to request|

The content (payload) changes according to the request. Each request has a different structure.

**Request Code 1025 – Registration**
*Payload:*
| Field | Size      | Meaning                                                        |
| :---- | :-------- | :------------------------------------------------------------- |
| Name  | 255 bytes | ASCII string representing username. Includes null terminator! |
*Note: The server will ignore the Client ID field in the header for this request.*

**Request Code 1026 – Send Public Key**
*Payload:*
| Field      | Size      | Meaning                                                        |
| :--------- | :-------- | :------------------------------------------------------------- |
| Name       | 255 bytes | ASCII string representing username. Includes null terminator! |
| Public Key | 160 bytes | Client's public key                                            |

**Request Code 1027 – Reconnection (if client already registered)**
*Payload:*
| Field | Size      | Meaning                                                        |
| :---- | :-------- | :------------------------------------------------------------- |
| Name  | 255 bytes | ASCII string representing username. Includes null terminator! |

**Request Code 1028 – Send File**
*Payload (starts with):*
| Field        | Size    | Meaning                       |
| :----------- | :------ | :---------------------------- |
| Content Size | 4 bytes | Size of the file (after encryption) |

--- Page 7 ---

*Payload for Request Code 1028 – Send File (continued):*
| Field                 | Size      | Meaning                                                 |
| :-------------------- | :-------- | :------------------------------------------------------ |
| Orig File Size        | 4 bytes   | Original file size (before encryption)                  |
| Packet number, total packets | 4 bytes   | 2 bytes: current message number; 2 bytes: total messages |
| File Name             | 255 bytes | Name of the file being sent                             |
| Message Content       | Variable  | File content. Encrypted with a symmetric key.           |

**Request Code 1029 – CRC is valid**
*Payload:*
| Field     | Size      | Meaning                   |
| :-------- | :-------- | :------------------------ |
| File Name | 255 bytes | Name of the sent file     |

**Request Code 1030 – CRC is not valid, sending again (followed by request 1028)**
*Payload:*
| Field     | Size      | Meaning                   |
| :-------- | :-------- | :------------------------ |
| File Name | 255 bytes | Name of the sent file     |

**Request Code 1031 – CRC is not valid for the 4th time, I'm done**
*Payload:*
| Field     | Size      | Meaning                   |
| :-------- | :-------- | :------------------------ |
| File Name | 255 bytes | Name of the sent file     |

---

#### Responses:

**Response from Server Structure:**

| Field       | Size     | Meaning                                          |
| :---------- | :------- | :----------------------------------------------- |
| **Header**  |          |                                                  |
| Version     | 1 byte   | Server version number                            |
| Code        | 2 bytes  | Response code                                    |
| Payload size| 4 bytes  | Size of the response content (payload)           |
| **Payload** |          |                                                  |
| payload     | Variable | Response content. Varies according to response.  |

**Response Code 1600 – Registration Successful**
*Payload:*
| Field     | Size     | Meaning                   |
| :-------- | :------- | :------------------------ |
| Client ID | 16 bytes | Client's unique identifier|

**Response Code 1601 – Registration Failed**
*(No specific payload structure detailed, likely payload size is 0)*

**Response Code 1602 – Public key received and AES key sent (encrypted)**
*Payload:*
| Field                | Size     | Meaning                                     |
| :------------------- | :------- | :------------------------------------------ |
| Client ID            | 16 bytes | Client's unique identifier                  |
| Encrypted Symmetric Key | Variable | AES key encrypted for the client (with RSA public key) |

--- Page 8 ---

**Response Code 1603 – File received successfully with CRC:**
*Payload:*
| Field        | Size      | Meaning                                      |
| :----------- | :-------- | :------------------------------------------- |
| Client ID    | 16 bytes  | Unique identifier of the sending client      |
| Content Size | 4 bytes   | Size of the file (after encryption)          |
| File Name    | 255 bytes | Name of the received file                    |
| Cksum        | 4 bytes   | CRC checksum                                 |

**Response Code 1604 – Acknowledges message receipt, thank you.**
(This message can be received in response to message 1029 or 1031 from the client).
*Payload:*
| Field     | Size     | Meaning                   |
| :-------- | :------- | :------------------------ |
| Client ID | 16 bytes | Client's unique identifier|

**Response Code 1605 – Confirms reconnection request, sends encrypted AES key – table identical to code 1602:**
*Payload:*
| Field                | Size     | Meaning                                     |
| :------------------- | :------- | :------------------------------------------ |
| Client ID            | 16 bytes | Client's unique identifier                  |
| Encrypted Symmetric Key | Variable | AES key encrypted for the client (with RSA public key) |

**Response Code 1606 – Reconnection request denied (client not registered or no valid public key). In this case, the client must re-register as a new client.**
*Payload:*
| Field     | Size     | Meaning                   |
| :-------- | :------- | :------------------------ |
| Client ID | 16 bytes | Client's unique identifier|

**Response Code 1607 – General server error not handled by previous cases (e.g., disk full, general database error, etc.).**
*(No specific payload structure detailed, likely payload size is 0 or contains an error message string)*

### Encryption
The communication protocol uses symmetric encryption to encode files and asymmetric encryption to exchange the symmetric key between the client and server.

*   In this exercise, use the **Crypto++** library² on the client side (see code example in Unit 7 on the course website).
    (² `https://www.cryptopp.com`)

#### Symmetric Encryption
*   For symmetric encryption, use **AES-CBC**.
*   Key length **256 bits**. It can be assumed that the **IV is always zeroed** (memory full of zeros).
*   Using such an IV is not secure if the same key is used multiple times, but for the purpose of this assignment, it is sufficient.

#### Asymmetric Encryption
*   For asymmetric encryption, use **RSA**. Key length **1024 bits**.

--- Page 9 ---

### Disconnection and Recovery: The following diagram describes the process:

**Client** -> **Server**
1.  Client: `Reconnect Request`
2.  Server: `Client listed in DB + RSA public key exists?`
    *   If **No**: -> Server: `Reconnect rejected`, Client should `Restart as new client` (i.e., register)
    *   If **Yes**: -> Server: `Accept reconnect, Generate AES Key, Encrypt with public key & send to client`
3.  Client: `Encrypt file with AES key, Send encrypted file to server` -> Server: `Decrypt file, Calculate checksum, Send to client`
4.  Client: `Check sum ok?`
    *   If **No**:
        *   `Re-send` (up to 3 times) -> (Go back to step 3)
        *   If **No (4th time)**: `Send abort message`
    *   If **Yes**: -> Server: `Accept`

--- Page 10 ---

**Note:** The Crypto++ library³ holds public keys in X509 format. This format includes a Header before the key itself and other values. Therefore, its final size (in binary form) is **160 bytes** (for keys of the specified size; for different key sizes, the final size of the key will change accordingly).
(³ `https://en.wikipedia.org/wiki/X.509`)

### Development Guidelines

1.  It is recommended to work with a version control system (e.g., Git⁴).
    (⁴ `https://www.atlassian.com/git/tutorials/what-is-version-control`)
2.  Work in a modular way and test yourself constantly.
    a.  Identify the important classes and functions.
    b.  **Server Side:** Write code to handle one request. Add support for multiple clients at a later stage.
    c.  **Client Side:** Implement the major components independently of other parts of the system (communication, encryption, protocol, etc.).
3.  Implement testing code in the early stages of the project.
    a.  **Server Side:** Use screen prints or logging to track communication. You can also load the module into the interpreter and work dynamically.
    b.  **Client Side:** Write small functions that test separate parts of the system. Use these functions while writing your code.
4.  Code Writing:
    a.  Implement the program according to object-oriented programming principles.
    b.  Pay attention to the representation of values in memory as **little-endian vs. big-endian**.
    c.  Ensure your code is well-documented (comments).
    d.  Use meaningful names for variables, functions, and classes. Avoid magic numbers!
    e.  A message can be very large (dynamic size). Think about the correct way to receive and send large amounts of data.
    f.  **Information Security** – Throughout the process, think about writing secure code according to the principles you've learned: Did you check the input? How is dynamic memory used? Is type casting performed? etc.
5.  Before Submission:
    a.  Check that the project compiles and runs correctly without crashes or dependencies on different libraries (except for the libraries required for the exercise).
    b.  It is recommended to create a new folder and copy the files designated for submission into it. Create a new VS project, compile, and run.
    c.  The work will be checked on a Windows machine with **Visual Studio Community 2022** with **C++ version 17**.

### Server Code Guidelines:
1.  Use Python version 3.
2.  Use only standard Python libraries (except for the encryption library)!
3.  You can use the `struct` library to conveniently work with communication data.

### Client Code Guidelines:
1.  It is recommended (but not mandatory) to use STL libraries.

--- Page 11 ---

2.  It is permissible and recommended to use C++11 features and above (e.g., lambda functions, use of `auto`, etc.).
3.  For implementing communication, use **winsock** or the **boost** library.

### Submission

#### Server
1.  You must submit only the source code files (i.e., `.py` files).
    **Note!** The program must load and run correctly (without needing additional files and without crashes).
2.  A main function named `main` must be included. This function will be the main function of the server program and will operate according to the server operation mode detailed above.
    Tip: You can use the following mechanism to allow both interactive work and running the code:
    ```python
    if __name__ == "__main__":
        # main() or server execution logic
        pass
    ```

#### Client
1.  You must submit only the source code files (i.e., `.h` and `.cpp` files).
    **Note!** The program must run correctly (without needing additional files, without crashes).
2.  Your work will be tested on a Windows operating system, using Visual Studio, so it is recommended to work with this environment.

### Video with Demo Run
You must record a video from your computer screen, in which you open two `cmd` windows simultaneously and run the system you developed. First, run the server, then the client. Go through the process of client registration and key exchange, with the corresponding messages appearing in both windows. Transfer a binary data file of about 100KB from the client to the server. The video should include an identifying detail such as your name or ID card, and it should last 2-5 minutes.

## Question 2 (20%)
You need to analyze the protocol proposed in Question 1 and find potential weaknesses in it. You must submit a research document detailing the weaknesses you found, possible attacks, and a proposal for correction. Among other things, you should present a table in the format of the weakness document from study unit 3.

## Question 3 – Bonus (15%)
Add an SQLite database to the server that will include a table for the list of users, names of encryption keys sent to them, and a table for the list of files received from them, and whether the file passed successful verification with the client using checksum. Saving the data will be done via SQL tables in a file named `defensive.db`. This will allow, in case of a server crash and restart, to retrieve data about registered clients and stored files.

Client information will be stored in a table named `clients`. The table structure:

| Field | Type                | Notes                                                    |
| :---- | :------------------ | :------------------------------------------------------- |
| ID    | 16 bytes (128 bits) | Unique identifier for each client. Index.                |
| Name  | string (255 chars)  | ASCII string representing username. Includes null terminator! |

--- Page 12 ---

| Field      | Type          | Notes                                                        |
| :--------- | :------------ | :----------------------------------------------------------- |
| PublicKey  | 160 bytes     | Client's public key.                                         |
| LastSeen   | Date and Time | The time when the last request was received from the client. |
| AESKey     | 256 bits      | AES key sent to the client.                                  |
*(Self-correction: The table above is a continuation of the `clients` table from page 11)*

Information about received files will be stored in a table named `files`. The table structure:

| Field     | Type                | Notes                                                              |
| :-------- | :------------------ | :----------------------------------------------------------------- |
| ID        | 16 bytes (128 bits) | Unique identifier for each file (likely linked to client ID or new UUID). |
| FileName  | string (255 chars)  | ASCII string representing file name as sent by user. Includes null! |
| PathName  | string (255 chars)  | ASCII string representing relative path and file name as stored on server. Includes null! |
| Verified  | Boolean             | Was checksum successfully verified with the client.                |

In case the server crashes, it will have an option to restart, load the database from the SQLite file, and registered clients will be able to perform a recovery process with it and continue working without needing to send an RSA key again.

### Submission (for Question 3 if attempted)
A Word or PDF document.

**Note: All system files (code, supporting files for running) should be packed into a zip file.**