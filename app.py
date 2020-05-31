import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
import aiomysql

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html')

def log(sql, args=()):
    logging.info('SQL: %s' % sql)
#连接池
async def craete_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf-8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )
#查找
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (await __pool) as conn:
        cur = await conn.curor(aiomysql.DictCursor)
        await cur.excute(sql.replace('?', '%s'),args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs
#更新 包括 update、add、delete
async def excute(sql, args):
    log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.curor()
            await cur.excute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise e
    return affected

#@asyncio.coroutine
async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    runner = web.AppRunner(app)

    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    await site.start()
    #DeprecationWarning: Application.make_handler(...) is deprecated, use AppRunner API instead
    # srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    # logging.info('server started at http://127.0.0.1:9000...')
    # return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()