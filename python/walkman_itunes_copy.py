#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# iTunesのプレイリストをwalkmanにコピーするスクリプト
#

from xml.etree.ElementTree import *
import urllib.parse
import os
import shutil

walkman_music_root = '/Volumes/WALKMAN/MUSIC'


# load itunes library xml
def load_ituneslib(fname):
  tree = parse(fname)
  elem = tree.getroot()
  return parse_xmllist(elem)


def parse_xmllist(elem, sub_type='dict'):
  if sub_type == 'array':
    subarray = []
    for e in list(elem):
      if e.tag == 'dict':
        subarray.append(parse_xmllist(e))
      elif e.tag == 'array':
        subarray.append(parse_xmllist(e, sub_type='array'))
      else:
        subarray.append(e.text)
    return subarray

  elif sub_type == 'dict':
    subdict = {}
    k = "root"
    for e in list(elem):
      if e.tag == 'key':
        k = e.text
      elif e.tag == 'dict':
        subdict[k] = parse_xmllist(e)
      elif e.tag == 'array':
        subdict[k] = parse_xmllist(e, sub_type='array')
      else:
        subdict[k] = e.text
    return subdict

  else:
    return None


# sync function
def sync_playlist(ituneslib, walkman_music_root, list_name):
  for pl in ituneslib['root']['Playlists']:
    if 'Playlist Items' in pl and pl['Name'] == list_name:
      extm3u_str = "#EXTM3U\n"
      for trk in pl['Playlist Items']:
        trk_info = ituneslib['root']['Tracks'][trk['Track ID']]
        src_path = urllib.parse.unquote(trk_info['Location'])[7:]
        dest_albumpath = trk_info['Artist'] + '/' + trk_info['Album']
        if 'Album Artist' in trk_info:
          dest_albumpath = trk_info['Album Artist'] + '/' + trk_info['Album']
        dest_albumpath = dest_albumpath.replace('*', '').replace('"', '')
        dest_dir = walkman_music_root + '/' + dest_albumpath
        dest_trkname = trk_info['Name'].replace('*', '').replace('"',
                                                                 '').replace(
            '/', '')
        dest_filename = trk_info['Track Number'] + " " + dest_trkname + '.mp3'
        dest_file = dest_albumpath + '/' + dest_filename
        dest_path = dest_dir + '/' + dest_filename
        if not os.path.exists(dest_dir):
          os.makedirs(dest_dir)
        if not os.path.exists(dest_path):
          shutil.copy(src_path, dest_path)
          print("copy ", dest_path)
        extm3u_str += "#EXTINF:" + str(
            int(int(trk_info['Total Time']) / 1000)) + "," + trk_info[
                        'Name'] + "\n"
        extm3u_str += dest_file + "\n"

      print('create ' + walkman_music_root + '/' + pl['Name'] + '.m3u8')
      with open(walkman_music_root + '/' + pl['Name'] + '.m3u8', 'w') as f:
        f.write(extm3u_str)
  return


if __name__ == '__main__':
  import sys

  if len(sys.argv) > 1 and sys.argv[1] == "init":
    itunesxml_path = input('iTunes Library.xml path >> ')
    f = open("{}/.walkman-itunes-copy-config".format(walkman_music_root), "w")
    f.write("itunesxml_path: {}".format(itunesxml_path))

  with open("{}/.walkman-itunes-copy-config".format(walkman_music_root)) as f:
    conf_str = f.read()
  conf = {}
  for ln in conf_str.splitlines(keepends=False):
    keyval = ln.split(":", maxsplit=1)
    conf[keyval[0]] = keyval[1].strip()

  ituneslib = load_ituneslib(fname=conf['itunesxml_path'])

  while True:
    listnames = []
    idx = 0
    for pl in ituneslib['root']['Playlists']:
      if 'Playlist Items' in pl:
        idx += 1
        print(idx, pl['Name'])
        listnames.append(pl['Name'])

    plnum = input('? ')

    if not plnum.isdigit():
      break

    print("sync " + listnames[int(plnum) - 1])
    sync_playlist(ituneslib, walkman_music_root, listnames[int(plnum) - 1])
