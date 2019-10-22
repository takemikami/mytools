#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 共通モジュールのインクルード管理コマンド
#
#  sync_include.py diff filename: 共通モジュールとの差分表示
#  sync_include.py get filename: 共通モジュールを取り込む
#  sync_include.py put filename: 個別修正を共通モジュールに反映する
#

import sys
import difflib
import re


# 対象範囲外のコードを消す
def filter_module(str, conf):
  inc_flag = False
  rtn = []
  for ln in str.split("\n"):
    if ln == conf['comment_module_start']:
      inc_flag = True
    if inc_flag:
      rtn.append(ln)
    else:
      rtn.append("")
    if ln == conf['comment_module_end']:
      break
  return rtn


# 空文字列の数を数える
def count_head_empty_lines(str):
  skip_length = 0
  for ln in str:
    if ln != "":
      break
    skip_length += 1
  return skip_length


# 差分の表示
def get_diff(path1, path2, conf):
  with open(path1) as f:
    s1 = f.read()
  with open(path2) as f:
    s2 = f.read()
  s1 = filter_module(s1, conf)
  s2 = filter_module(s2, conf)
  diffstr = difflib.unified_diff(s1, s2, fromfile=path1, tofile=path2,
                                 lineterm="")

  # インクルードモジュールより前の部分のdiffは除外する
  skip_length = count_head_empty_lines(s1) - 3
  re_at = re.compile(r"^@@\s-([0-9]+),[0-9]+\s\+[0-9]+,[0-9]+\s@@$")
  mute_flag = False
  diff_str = []
  for ln in diffstr:
    re_result = re_at.match(ln)
    if re_result:
      diff_ln_num = int(re_result.group(1))
      if diff_ln_num < skip_length:
        mute_flag = True
      else:
        mute_flag = False
    if not mute_flag:
      diff_str.append(ln)
  return diff_str


# モジュールの展開
def put_module(path_from, path_to, conf):
  with open(path_from) as f:
    s1 = f.read()
  with open(path_to) as f:
    s2 = f.read()
  s1 = filter_module(s1, conf)
  module_str = s1[count_head_empty_lines(s1):len(s1)]

  # print('\n'.join(module_str))
  put_str = []
  inc_flag = False
  for ln in s2.split("\n"):
    if ln == conf['comment_module_start']:
      inc_flag = True
      put_str.extend(module_str)
      # print('\n'.join(module_str))
    if inc_flag:
      pass
    else:
      put_str.append(ln)
    if ln == conf['comment_module_end']:
      inc_flag = False

  with open(path_to, "w") as f:
    f.write('\n'.join(put_str))


# 続行確認
def continue_check():
  input_str = input('continue? (y/N) >> ')
  return input_str == "y" or input_str == "Y"


# コマンドの実行
def execute(subcmd, target1=None, target2=None):
  if subcmd == "init":
    initialize()
    return

  conf = load_config()
  if conf is None:
    print("configuration is invalid.")
    return
  if target2 is None:
    target2 = conf['module_file_path']
  if target1 is None:
    print("File name parameter required.")
    print_usage()
    return

  if subcmd == "diff":
    print('\n'.join(get_diff(target1, target2, conf)))
  elif subcmd == "put" or subcmd == "get":
    if subcmd == "put":
      target_f = target1
      target_t = target2
      sync_str = "sync {} ===> {}".format(target1, target2)
    else:
      target_f = target2
      target_t = target1
      sync_str = "sync {} <=== {}".format(target1, target2)

    diff_str = get_diff(target_f, target_t, conf)
    if len(diff_str) <= 2:
      print("No changes.")
      return
    print('\n'.join(diff_str))
    print('')
    print(sync_str)
    if continue_check():
      put_module(target_f, target_t, conf)
  else:
    print("Unknown command.")
    print_usage()


# 設定ファイルの初期化
def initialize():
  comment_module_start = input('comment_module_start >> ')
  comment_module_end = input('comment_module_end >> ')
  module_file_path = input('module_file_path? >> ')
  conf = {
    'comment_module_start': comment_module_start,
    'comment_module_end': comment_module_end,
    'module_file_path': module_file_path,
  }
  f = open(".sync_include-config", "w")
  f.write('\n'.join(["{}: {}".format(k, conf[k]) for k in conf]))


# 設定ファイルの読み込み
def load_config():
  with open(".sync_include-config") as f:
    conf_str = f.read()
  conf = {}
  for ln in conf_str.splitlines(keepends=False):
    keyval = ln.split(":", maxsplit=1)
    conf[keyval[0]] = keyval[1].strip()
  if 'comment_module_start' in conf \
      and 'comment_module_end' in conf \
      and 'module_file_path' in conf:
    return conf
  return None


# コマンドラインオプションの解釈
def parse_args(args):
  if len(args) < 2:
    return None
  subcmd = args[1]
  target1 = None
  target2 = None
  if len(args) > 2:
    target1 = args[2]
  if len(args) > 3:
    target2 = args[3]
  return {
    "subcmd": subcmd,
    "target1": target1,
    "target2": target2,
  }


# 使い方の表示
def print_usage():
  print("sync_include: コードフラグメントの同期コマンド")
  print(" init: sync_includeの初期化")
  print(" get [file name]: 共通フラグメントを個別ソースに取り込む")
  print(" put [file name]: 個別ソースのフラグメントを共通フラグメントに反映する")
  print(" diff [file name]: 個別ソース・共通フラグメントの差分を確認する")


if __name__ == '__main__':
  execute_options = parse_args(sys.argv)
  if execute_options is not None:
    execute(**execute_options)
  else:
    print_usage()
