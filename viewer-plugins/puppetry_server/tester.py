#!/usr/bin/env python3
import asyncio

async def main():
    proc = await asyncio.create_subprocess_exec('./src.elf',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    async def loop(proc):
        stdout= await proc.stdout.read()
        print("RECV:", stdout)
    
    asyncio.create_task(loop(proc))
    while True:
        test = """{"example":1}"""
        proc.stdin.write((str(len(test))+":"+test).encode())
        await proc.stdin.drain()
        await asyncio.sleep(1)


asyncio.run(main())