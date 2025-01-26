import os
import time
import json
import xattr
import random
import socket
import hashlib
import tempfile
import requests

print("Process Type ", os.environ['TYPE'], os.getpid())

# Add header to the response
def response_message(start_response, code, headers=[('Content-type', 'text/plain')], body=b''):
  start_response(code, headers)
  return [body]

# MASTER SERVER

class SimpleKV(object):
  
  # Create a new instance of the SimpleKV class
  def __init__(self, fn): 
    import plyvel
    self.db = plyvel.DB(fn, create_if_missing=True) 

  # utility functions for plyvel
  def get(self, k):
    return self.db.get(k)

  def put(self, k, v):
    self.db.put(k, v)

  def delete(self, k):
    self.db.delete(k)


if os.environ['TYPE'] == "master":
  # check on volume servers
  volumes = os.environ['VOLUMES'].split(",")

  for v in volumes:
    print(v)
  # Create an instance of the SimpleKV class
  db = SimpleKV(os.environ['DB'])


def master(env, sr):
  host = env['SERVER_NAME'] + ":" + env['SERVER_PORT']
  key = env['PATH_INFO']

  # POST is called by the volume servers to write to the database
  if env['REQUEST_METHOD'] == 'POST':
    # Get the length of the content
    flen = int(env.get('CONTENT_LENGTH', '0'))
    print("posting", key, flen)

    if flen > 0:
      db.put(key.encode('utf-8'), env['wsgi.input'].read())
    else:
      db.delete(key.encode('utf-8'))
    return response_message(sr, '200 OK')

  # Get the value of the key
  metakey = db.get(key.encode('utf-8'))
  print(key, metakey)

  if metakey is None:      
    # key not found put it in a random volume
    if env['REQUEST_METHOD'] == 'PUT':
      volume = random.choice(volumes)
    else:
      # this key doesn't exist and we aren't trying to create it
      return response_message(sr, '404 Not Found')
    
  else:
    # key found 
    if env['REQUEST_METHOD'] == 'PUT':
      # already exists, return conflict
      return response_message(sr, '409 Conflict')
    
    meta = json.loads(metakey.decode('utf-8'))
    volume = meta['volume'] # get the volume from the metadata

  # send the redirect
  headers = [('Location', 'http://%s%s?%s' % (volume, key, host))]

  return response_message(sr, '307 Temporary Redirect', headers)






# VOLUME SERVER

class FileCache(object):
  # FileCache is a simple key value store that stores files on disk in a directory structure

  def __init__(self, basedir):
    self.basedir = os.path.realpath(basedir)
    self.tmpdir = os.path.join(self.basedir, "tmp")
    os.makedirs(self.tmpdir, exist_ok=True)
    print("FileCache in %s" % basedir)

  # key to path converter
  def k2p(self, key, mkdir_ok=False):
    key = hashlib.md5(key.encode('utf-8')).hexdigest()

    # Path is two layers deep in nginx cache with md5 hash
    path = self.basedir+"/"+key[0:2]+"/"+key[0:4]
    if not os.path.isdir(path) and mkdir_ok:
      # exist ok is fine, could be a race
      os.makedirs(path, exist_ok=True)

    return os.path.join(path, key)

  # utility functions
  def exists(self, key):
    return os.path.isfile(self.k2p(key))

  def delete(self, key):
    try:
      os.unlink(self.k2p(key))
      return True
    except FileNotFoundError:
      pass
    return False

  def get(self, key):
    return open(self.k2p(key), "rb")

  def put(self, key, stream):
    with tempfile.NamedTemporaryFile(dir=self.tmpdir, delete=False) as f:
      f.write(stream.read())

      # Save the real name in xattr in case we rebuild cache
      xattr.setxattr(f.name, 'user.key', key.encode('utf-8'))
      os.rename(f.name, self.k2p(key, True))

if os.environ['TYPE'] == "volume":

  # create the filecache
  fc = FileCache(os.environ['VOLUME'])

def volume(env, sr):
  host = env['SERVER_NAME'] + ":" + env['SERVER_PORT']
  key = env['PATH_INFO']

  # For PUT requests
  if env['REQUEST_METHOD'] == 'PUT':
    # check if the key exists in the FileCache
    if fc.exists(key):
      req = requests.post("http://"+env['QUERY_STRING']+key, json={"volume": host})
      return response_message(sr, '409 Conflict')

    flen = int(env.get('CONTENT_LENGTH', '0'))
    if flen > 0:
      # write the content to the FileCache
      fc.put(key, env['wsgi.input'])
      req = requests.post("http://"+env['QUERY_STRING']+key, json={"volume": host})
      if req.status_code == 200:
        return response_message(sr, '201 Created')
      else:
        fc.delete(key)
        return response_message(sr, '500 Internal Server Error')
      
    else:
      return response_message(sr, '411 Length Required')


  # For DELETE requests
  if env['REQUEST_METHOD'] == 'DELETE':
    req = requests.post("http://"+env['QUERY_STRING']+key, data='')
    if req.status_code == 200:
      if fc.delete(key):
        return response_message(sr, '200 OK')
      else:
        return response_message(sr, '500 Internal Server Error (not on disk)')
    else:
      return response_message(sr, '500 Internal Server Error (master db write fail)')

  if not fc.exists(key):
    # key not in the FileCache, 404
    return response_message(sr, '404 Not Found')


  # For GET requests
  if env['REQUEST_METHOD'] == 'GET':
        
    if 'HTTP_RANGE' in env:
      b,e = [int(x) for x in env['HTTP_RANGE'].split("=")[1].split("-")]
      f = fc.get(key)
      f.seek(b)
      ret = f.read(e-b)
      f.close()
      return response_message(sr, '200 OK', body=ret)
    else:
      return response_message(sr, '200 OK', body=fc.get(key).read())
