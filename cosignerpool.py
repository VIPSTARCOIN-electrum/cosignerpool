#!/usr/bin/env python3
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2015 THomas Voegtlin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import sys, socket, os, re
import urllib.request, urllib.error
import traceback
import plyvel
import json, ast
import time
import configparser

config = configparser.ConfigParser()
config.read("/etc/cosignerpool.conf")
my_password = config.get('main','password')
my_host = config.get('main','host')
my_port = config.getint('main','port')
dbpath = config.get('main', 'dbpath')


def run_server():
    from xmlrpc.server import SimpleXMLRPCServer
    from xmlrpc.server import SimpleXMLRPCRequestHandler
    server = SimpleXMLRPCServer((my_host, my_port), allow_none=True, logRequests=False)
    server.register_function(delete, 'delete')
    server.register_function(get, 'get')
    server.register_function(put, 'put')
    server.register_function(dump, 'dump')
    server.register_function(lambda: setattr(server,'running', False), 'stop')
    server.running = True
    while server.running:
        try:
            server.handle_request()
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
    print("server stopped")

def get(key):
    key = key.encode("UTF-8")
    try:
        o = db.get(key)
    except Exception as e:
        o = None
    if o:
        print("get", key, len(o))
    return o.decode("UTF-8")

def put(key, value):
    print("put", key, len(value))
    db.put(key.encode("UTF-8"), value.encode("UTF-8"))

def delete(key):
    print("delete", key)
    key = key.encode("UTF-8")
    db.delete(key)

def dump():
    print("dump")
    out = {}
    for key, value in db:
        out[ key.decode("UTF-8") ]= value.decode("UTF-8")
    return out

def handle_command(cmd):
    import xmlrpc.client
    server = xmlrpc.client.ServerProxy('http://%s:%d'%(my_host, my_port), allow_none=True)

    try:
        if cmd == 'stop':
            out = server.stop()
        else:
            out = "unknown command"
    except socket.error:
        print("Server not running")
        return 1

    print(out)
    return 0

if __name__ == '__main__':

    if len(sys.argv) > 1:
        ret = handle_command(sys.argv[1])
        sys.exit(ret)

    db = plyvel.DB(dbpath, create_if_missing=True, compression=None)
    run_server()
    db.close()


