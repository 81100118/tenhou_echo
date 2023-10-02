import websocket
import json
import threading
import time
import signal

authenticated = False
client = None
PXR = 0
voluntarily_close = False
send_timestamp = 0.0
send_num = 0
recv_num = 0
timeout_num = 0
over_400ms_num = 0
over_1000ms_num = 0
total_echo_time = 0.0

def on_error(ws, error):
    print('error')
    print(error)

def on_close(ws, code, reason):
    global authenticated
    authenticated = False
    print("connection closed")
    print('recv:', recv_num, ', timeout:', timeout_num, ', avg echo:', int(total_echo_time / recv_num * 1000), 'ms, over 400ms count:', over_400ms_num, ', over 1000ms count:', over_1000ms_num)
    global voluntarily_close
    if voluntarily_close:
        voluntarily_close = False
    else:
        pass

def on_open(ws):
    pass

def on_message(ws, message):
    # print('recv: ' + message)
    try:
        j = json.loads(message)
        process_message(j)
    except Exception as e:
        print(e)

def process_message(message):
    # message :: dict
    if message['tag'] == 'HELO':
        global authenticated
        authenticated = True
    elif message['tag'] == 'LN':
        if 'n' in message:
            num_online = [0,0,0,0]
            tmp = message['n'].split(',')
            for i in range(len(tmp)):
                num_online[i] = int(tmp[i])
    elif message['tag'] == 'CHAT':
        if 'lobby' in message:
            # 切换个室成功
            if message['lobby'][0] == 'C':
                client.lobby = int(message['lobby'][1:])
            else:
                client.lobby = int(message['lobby'])
            print('切换到个室' + message['lobby'])
        else:
            # 可能是聊天消息
            uname = message['uname']
            text = message['text']
            print('聊天消息：' + uname + ': ' + text)
    elif message['tag'] == 'GO':
        pass
    elif message['tag'] == 'SAIKAI':
        authenticated = True
    elif message["tag"] == "ECHO":
        global send_timestamp
        if send_timestamp != 0.0:
            global recv_num, total_echo_time, over_400ms_num, over_1000ms_num
            recv_num += 1
            echo_time = time.time() - send_timestamp
            total_echo_time += echo_time
            if echo_time >= 1.0:
                over_1000ms_num += 1
            elif echo_time >= 0.4:
                over_400ms_num += 1
            
            print(str(int(echo_time * 1000)) + 'ms')
        send_timestamp = 0.0
    client.processFunc(message)

def send(ws, msg):
    try:
        if isinstance(msg, dict):
            ws.send(json.dumps(msg))
            # print('sent json: ' + json.dumps(msg))
        else:
            ws.send(msg)
            # print('sent string: ' + msg)
    except:
        print('SEND ERROR:')
        print(msg)

class HeartbeatLoopThread(threading.Thread):
    def __init__(self, ws):
        super().__init__()
        self.ws = ws
        self.timer = None
        self.skip = True
    def run(self):
        if self.ws.sock and self.ws.sock.connected:
            if self.skip:
                self.skip = False
            else:
                send(self.ws, '<Z/>')
                if PXR != 0:
                    send(self.ws, '<PXR v="' + str(PXR) + '" />')
            self.timer = threading.Timer(10, self.run)
            self.timer.start()
    def join(self):
        if self.timer != None:
            self.timer.cancel()
        super().join()

class EchoThread(threading.Thread):
    def __init__(self, ws):
        super().__init__()
        self.ws = ws
        self.timer = None
        self.skip_count = 0
    def run(self):
        if self.ws.sock and self.ws.sock.connected:
            global send_timestamp
            if send_timestamp != 0.0:
                if self.skip_count < 4:
                    self.skip_count += 1
                else:
                    send_timestamp = 0.0
                    self.skip_count = 0
                    global timeout_num
                    timeout_num += 1
                    print('timeout')
            else:
                self.skip_count = 0
                global send_num
                send_num += 1
                send_timestamp = time.time()
                send(self.ws, '<ECHO />')
            self.timer = threading.Timer(1, self.run)
            self.timer.start()
    def join(self):
        if self.timer != None:
            self.timer.cancel()
        super().join()


class MainLoopThread(threading.Thread):
    def __init__(self, ws):
        super().__init__()
        self.ws = ws
    def run(self):
        print('main loop starts')
        self.ws.run_forever(suppress_origin=True)
        print('main loop ends')


class TenhouClient:
    def __init__(self):
        global authenticated
        authenticated = False
        self.mainLoopThread = None
        self.playerData = None
        self.lobby = 0
        self.processFunc = lambda msg: 1
        self.onCloseFunc = lambda : 1
    def init(self):
        # connect to tenhou
        # websocket.enableTrace(True)
        h = ['Pragma: no-cache',
        'Cache-Control: no-cache',
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Origin: https://tenhou.net',
        'Accept-Encoding: gzip, deflate, br',
        'Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,ja;q=0.5',
        'Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits']
        self.ws = websocket.WebSocketApp('wss://b-ww.mjv.jp', header = h, on_message = on_message, on_error= on_error, on_close= on_close)#, suppress_origin = True)
        self.ws.on_open = on_open
        self.mainLoopThread = MainLoopThread(self.ws)
        self.mainLoopThread.start()
        counter = 0
        while not (self.ws.sock and self.ws.sock.connected):
            counter += 1
            time.sleep(0.1)
            if counter == 50:
                return False
        print('done')
        return True
    def login(self, name, sx='F', gpid = None):
        if authenticated:
            return
        msg_to_send = {'tag': 'HELO', 'name': name, 'sx': sx}
        if gpid:
            msg_to_send['gpid'] = gpid
        # msg_to_send = '{"tag":"HELO","name":"' + name + '","sx":"' + sx + '"}'
        send(self.ws, msg_to_send)
        counter = 0
        while not authenticated:
            counter += 1
            time.sleep(0.1)
            if counter == 50:
                return False
        self.heartbeatLoopThread = HeartbeatLoopThread(self.ws)
        self.heartbeatLoopThread.start()
        self.echoThread = EchoThread(self.ws)
        self.echoThread.start()
        return True
    def logout(self):
        global authenticated
        if not authenticated:
            return
        send(self.ws, '<BYE/>')
        authenticated = False
        self.heartbeatLoopThread.join()
        self.echoThread.join()
        # time.sleep(1)
    def gotoLobby(self, lobby):
        if not authenticated:
            return
        send(self.ws, {'tag' : 'LOBBY', 'id' : lobby})
        #self.lobby = lobby
    def pxr(self):
        send(self.ws, '<PXR v="' + str(PXR) + '" />')
    def disconnect(self, voluntary=True):
        global voluntarily_close
        voluntarily_close = voluntary
        self.heartbeatLoopThread.join()
        self.ws.close()

if __name__ == '__main__':
    client = TenhouClient()
    client.init()
    client.login('NoName')
    lobby = 0000
    client.gotoLobby(lobby)
    while client.lobby != lobby:
        time.sleep(0.1)
    
    def signal_handler(signal, frame):
        client.logout()
        client.disconnect()
    
    signal.signal(signal.SIGINT, signal_handler)

