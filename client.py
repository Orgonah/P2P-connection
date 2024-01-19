import socket
import pickle
import threading
import sqlite3
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import sys
import os
import time

HOST = 'localhost'
AS_SERVER_PORT = 0
print_records=''
flag_over=False

if (not os.path.exists(sys.path[0]+"/database.db")):
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    c.execute(""" CREATE TABLE addresses (
            name text,
            port integer
            )""")
    conn.commit()
    conn.close()

def openFile():
    filepath = filedialog.askopenfilename(initialdir=sys.path[0],
                                                filetypes= (("text files","*.txt"),
                                                            ("all files","*.*")))
    file=open(filepath,'r')
    file_name=filepath.split("/")[-1]
    global send_file
    send_file=file_name + "\n" + file.read()
    send_btn["state"]=NORMAL
    file.close()

def refresh():
    global print_records
    while True:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT *, oid FROM addresses")
        records = c.fetchall()
        print_records = ''
        conn.commit() 
        conn.close()
        for record in records:
            print_records += str(record[2]) + "\t" + str(record[0]) + "\n"
        global flag_over
        if flag_over==True:
            break
        query_label["text"]=print_records
        time.sleep(2)

def send():
    other_cliasser_socket.send(pickle.dumps(send_file))  
    messagebox.showinfo(f"File Sharing ({main_name})","File successfuly sent!")
    send_btn["state"]=DISABLED

def connect(e):
    global other_cliasser_socket
    if conn_btn["text"]=="Connect":
        oid_ent["state"]=DISABLED
        if (oid_ent.get()==str(main_iod)):
            error_lab["text"]="This is yourself!"
            return 0
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("SELECT *, oid FROM addresses WHERE oid ="+ oid_ent.get())
            record=c.fetchall()
            conn.commit()
            conn.close()
        except sqlite3.OperationalError:
            error_lab["text"]="Invalid Index!"
            return 0

        if record==[]:
            error_lab["text"]="Invalid Index!"
            return 0
        try:
            other_cliasser_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            other_cliasser_socket.connect(("localhost", record[0][1]))
            other_cliasser_socket.send(pickle.dumps(main_name))
            data = pickle.loads(other_cliasser_socket.recv(1024))

        except ConnectionRefusedError:
            error_lab["text"]="Connection Error!"
            c.execute("DELETE FROM addresses WHERE oid = " + str(record[2]))
            return 0
        
        if(data):
            conn_btn["text"]="Disconnect"
            open_file_btn["state"]=NORMAL

        else:
            error_lab["text"]="Connection Rejected by the client"
    else:
        try:
            other_cliasser_socket.sendall("")
        except:
            pass
        else:
            other_cliasser_socket.close()
        conn_btn["text"]="Connect"
        open_file_btn["state"]=DISABLED
        
def submit(e):
    global AS_SERVER_PORT,this_cliasser_socket,server_thread
    this_cliasser_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    this_cliasser_socket.bind(("localhost", 0))
    AS_SERVER_PORT = this_cliasser_socket.getsockname()[1]
    this_cliasser_socket.listen()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT *, oid FROM addresses")
    records = c.fetchall()
    conn.commit()
    conn.close()

    for record in records:
        if record[0]==login_ent.get():
            error_label["text"]="This Name is already taken."
            return 0
    global main_name
    main_name=login_ent.get()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO addresses VALUES (:name, :port)",
                { 
                    'name': login_ent.get(),
                    'port': AS_SERVER_PORT
                })
    conn.commit()
    conn.close()
    root.destroy()
    connect_to_file()
    
def connect_to_file():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT *, oid FROM addresses")
    records = c.fetchall()
    record = ''
    conn.commit() 
    conn.close()
    for record in records:
        if record[0]==main_name:
            break
    global main_iod,top
    main_iod=record[2]

    server_thread = threading.Thread(target=listen_for_clients, args=())
    server_thread.start()
    
    top=Tk()
    top.title(f"File Sharing ({main_name})")

    global conn_btn,clients_frame,query_label,open_file_btn,send_btn,error_lab,oid_ent

    oid_label = Label(top, text="ID: ",font=("Arial",12))
    oid_label.grid(row=0,column=0,pady=20,padx=10)

    oid_ent = Entry(top,width=15)
    oid_ent.grid(row=0,column=1)
    oid_ent.focus_force()

    conn_btn = Button(top, text="Connect",width=10,border=3,command=lambda: connect(''))
    conn_btn.grid(row=0,column=2,padx=50)

    top.bind('<Return>',connect)

    open_file_btn = Button(top, text="Open File",width=10,border=3,state=DISABLED,command=openFile)
    open_file_btn.grid(row=1,column=0,pady=15,padx=10)

    send_btn = Button(top, text="Send",width=10,border=3,state=DISABLED,command=send)
    send_btn.grid(row=1,column=1)

    global error_lab
    error_lab=Label(top,text="",fg="red")
    error_lab.grid(row=2,column=0,columnspan=3,pady=5,padx=5) 

    clients_frame=LabelFrame(top,text="Online Clients")
    clients_frame.grid(sticky="w",row=3,column=0,columnspan=3,padx=50,pady=10)



    ex=Label(clients_frame,text="     ID        Name                      ",
                 font= ('Helvetica 10 underline'),justify=LEFT,anchor="w") 
    ex.grid(sticky="w",row=0,column=0,pady=5)

    query_label = Label(clients_frame, text=print_records,justify=LEFT,anchor="w",width=20)
    query_label.grid(sticky="w",row=1, column=0,padx=20)

    refresh_thread=threading.Thread(target=refresh,args=())
    refresh_thread.start()

 
    top.mainloop()
    global flag_over
    flag_over=True
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM addresses WHERE oid = " + str(main_iod))
    conn.commit()
    conn.close()

    os._exit(0)
                
def be_a_server(other_cliascli_socket, address):
    while True:
        try:
            data = pickle.loads(other_cliascli_socket.recv(1024))
            All=data.split("\n")
            file_name=All[0]
            payload="\n".join(All[1:])
            file_rcvd=open(file_name,'w')
            file_rcvd.write(payload)
            file_rcvd.close()
        except socket.error:
            error_lab["text"]="Client Disconnected!"
            break

def listen_for_clients():
    while True:
        other_cliascli_socket, address = this_cliasser_socket.accept()
        data = pickle.loads(other_cliascli_socket.recv(1024))
        n=messagebox.askyesno(f"File Sharing ({main_name})",f"{data} wants to send you a file. Do you agree?")
        other_cliascli_socket.send(pickle.dumps(n)) 
        if(n):
            client_thread = threading.Thread(target=be_a_server, args=(other_cliascli_socket, address))
            client_thread.start()

root = Tk()
root.title("File Sharing")

login_label=Label(root,text="What is your name?")
login_label.grid(padx=2,pady=2)

login_ent=Entry(root,width=30,border=3)
login_ent.grid(pady=5,padx=10)
login_ent.focus_set()

error_label=Label(root,text="",fg="red")
error_label.grid(pady=5,padx=10)

login_submit_btn=Button(root,text="Submit",border=3,command=lambda: submit(''))
login_submit_btn.grid(pady=5)

root.bind('<Return>',submit)

root.mainloop()

os._exit(0)

