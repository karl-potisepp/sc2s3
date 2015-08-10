#!/usr/bin/python

import soundcloud
import Tkinter
import copy
import urllib
import boto
import ConfigParser
import string
import random
from boto.s3.connection import S3Connection
from boto.s3.key import Key

#function for reporting download/upload progress
def dl_callback(current, total, x=-1):
  if x is -1:
    print current,"/",total
  else:
    print current,"/",(x/total)

#function for track list retrieval based on username
def retrieve_track_list():

  #retrieve user id
  uname = uname_field.get()
  try:
    user = client.get('/resolve', url='http://soundcloud.com/'+uname)
  except:
    print "Error while retrieving user ID."
    return

  if user.id > 0:

    #retrieve user's tracks by id
    try:
      tracks = client.get('/tracks', user_id=user.id)
    except:
      print "Error while retrieving user track list."
      return

    c = 0
    for track in tracks:

      #uncomment to show only downloadable tracks
      #if not track.downloadable:
      #  continue

      t_frame = Tkinter.Frame(tracklist_frame)
      t_frame.pack(side=Tkinter.TOP)

      t = Tkinter.Text(t_frame, height=1)
      t.insert(Tkinter.INSERT, track.title)
      t.pack(side=Tkinter.LEFT)

      if track.downloadable:
        b = Tkinter.Button(t_frame, text="Copy to S3", command=lambda url=copy.deepcopy(track.download_url): import_track(url) )
        b.pack(side=Tkinter.RIGHT)

      c += 1
      if c > 20:
        break

def import_track(url):

  #S3 connection
  config = ConfigParser.ConfigParser()
  config.read([".boto"])
  aws_access_key_id = config.get("Credentials", "aws_access_key_id")
  aws_secret_access_key = config.get("Credentials", "aws_secret_access_key")
  s3connection = S3Connection(aws_access_key_id, aws_secret_access_key)
  
  #verify connection
  try:
    s3connection.get_all_buckets()
  except:
    print "Error accessing S3 buckets. Verify your credentials and connection."
    return

  #try and retrieve bucket
  bucket = s3connection.lookup(bucket_field.get())

  if bucket is None:
    print "Bucket '"+bucket_field.get()+"' does not exist."
    return
  
  url+= "?client_id="+client_id
  
  #retrieve mp3 (overwrites previous temporary file)
  mp3 = "tmp_download.mp3"
  print "Downloading:", mp3
  filename, headers = urllib.urlretrieve(url=url, filename=mp3, reporthook=dl_callback)
  print "Done"

  #generate key and check if by chance it already exists
  random_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
  while bucket.get_key(random_key) is not None:
    random_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
  
  #upload the file to S3
  print "Uploading to S3"
  k = Key(bucket)
  k.key = random_key
  k.set_contents_from_filename("tmp_download.mp3", cb=dl_callback, num_cb=100)

  print "Done"


def main():

  #initialize soundclound client
  global client_id 
  client_id = "5096bc9b963f098eb5cce0340bb9d215"
  global client
  client = soundcloud.Client(client_id=client_id)

  #check if we have the S3 configuration file
  try:
     with open(".boto"): pass
  except IOError:
     print "Boto configuration file missing."
     return

  #define the GUI
  top = Tkinter.Tk()

  frame = Tkinter.Frame(top)
  frame.pack()

  #username field
  uname_frame = Tkinter.Frame(frame)
  uname_frame.pack(side=Tkinter.TOP)

  global uname_field
  uname_field = Tkinter.Entry(uname_frame)
  uname_field.insert(0, "creative-commons")
  uname_field.pack(side=Tkinter.LEFT)

  uname_button = Tkinter.Button(uname_frame, text="Retrieve track list", command = retrieve_track_list)
  uname_button.pack(side=Tkinter.RIGHT)

  #S3 bucket field
  bucket_frame = Tkinter.Frame(frame)
  bucket_frame.pack() 
  bucket_text = Tkinter.Text(bucket_frame, height=1, width=10)
  bucket_text.insert(Tkinter.INSERT, "S3 bucket:")
  bucket_text.pack(side=Tkinter.LEFT)


  global bucket_field
  bucket_field = Tkinter.Entry(bucket_frame)
  bucket_field.insert(0, "karl_test_bucket")
  bucket_field.pack()

  #tracklist
  global tracklist_frame
  tracklist_frame = Tkinter.Frame(frame)
  tracklist_frame.pack(side=Tkinter.BOTTOM)

  #start the GUI
  top.mainloop()

if __name__=="__main__":
  main()
