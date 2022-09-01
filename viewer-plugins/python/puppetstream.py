#!/usr/bin/env python3
import asyncio
import socket
import sys
import llbase.llsd
from signal import SIGINT, SIGTERM

async def getStdStreams(loop = None):
    if not loop:
        loop = asyncio.get_event_loop()
    
    #Create reader
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin.buffer)
    
    #Create writer
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout.buffer)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    
    return reader, writer

#log = open("/tmp/puppetstream.log", "w")
#sys.stderr = log
def print(*args, **kwargs):
    data = " ".join([str(i) for i in args])
    #_print("{}:{}".format(len(data)+1,data))
    #log.write(data+"\n")
    #log.flush()

class PuppertryStreamingServer:
    def __init__(self, loop = None):
        if not loop:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.clients = []
        self.initial = None
    
    async def start(self):
        self.stdin, self.stdout = await getStdStreams(self.loop)
        self.readerTask = self.loop.create_task(self.reader())
    
    def shutdown(self):
        for client in self.clients:
            client[1].close()
        exit()
    
    async def reader(self):
        while True:
            length = await self.stdin.readuntil(b":")
            #print(length)
            if length == None or length[-1] != 58: #:
                break
            try:
                length = int(length[:-1])
            except ValueError:
                print("Invalid data received from viewer!")
                break
            
            data = await self.stdin.read(length)
            #print(data)
            #Socket lost
            if data == None:
                self.shutdown()
                break
            
            #Incomplete stream
            if len(data) != length:
                self.shutdown()
                break
            
            if not self.initial:
                self.initial = str(length).encode()+b":"+data
            
            await self.sendall(str(length).encode()+b":"+data)
    
    async def sendall(self, data):
        for client in self.clients:
            client[1].write(data)
            await client[1].drain()
    
    async def handleClient(self, reader, writer):
        client = (reader, writer)
        self.clients.append(client)
        if self.initial:
            writer.write(self.initial)
            await writer.drain()
        while True:
            try:
                length = b""
                while True:
                    tmp = await reader.read(1)
                    if tmp == b":":
                        break
                    
                    if tmp == None or tmp == b"":
                        length = None
                        break
                    length += tmp
                    
                if length == None: #:
                    break
                
                try:
                    length = int(length)
                except ValueError:
                    print("Invalid data received from socket!", reader, length)
                    break
                
                data = await reader.read(length)
                
                #Socket lost
                if data == None or data == b"":
                    break
                
                #Incomplete stream
                if len(data) != length:
                    break
                
                #TODO: Validation
                #try:
                #    print("r" + str(data))
                #    print("rd" + str(llbase.llsd.parse_notation(data)))
                #except Exception as e:
                #    print(e)
                sys.stdout.buffer.write(str(length).encode() + b":" + data)
                sys.stdout.buffer.flush()
            except Exception:
                break
        
        self.clients.remove(client)
        writer.close()

async def run_server():
    srv = PuppertryStreamingServer()
    await srv.start()
    server = await asyncio.start_server(
        srv.handleClient, '127.0.0.1', 15555, reuse_port=True)

    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        server.close()
        server.wait_closed()
        sys.exit()
        exit()


if __name__ == "__main__":
    asyncio.run(run_server())
    