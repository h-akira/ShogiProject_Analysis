#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Created: 2025-04-22 22:23:06

import sys
import os

# def parse_args():
#   import argparse
#   parser = argparse.ArgumentParser(description="""\
#
# """, formatter_class = argparse.ArgumentDefaultsHelpFormatter)
#   parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
#   parser.add_argument("-o", "--output", metavar="output-file", default="output", help="output file")
#   # parser.add_argument("-", "--", action="store_true", help="")
#   parser.add_argument("file", metavar="input-file", help="input file")
#   options = parser.parse_args()
#   if not os.path.isfile(options.file): 
#     raise Exception("The input file does not exist.") 
#   return options
#
# def main():
#   options = parse_args()
#
# if __name__ == '__main__':

import subprocess
import time
import re

ENGINE_PATH = "./YaneuraOu-by-gcc"  # ← ここを書き換える
SFEN = "lnsgkgsnl/1r5b1/p1pppp1p1/6p1p/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL b - 1"
MOVETIME = 3000  # ミリ秒

def send(proc, cmd):
    print(f">>> {cmd}")
    proc.stdin.write(cmd + '\n')
    proc.stdin.flush()

def read_lines_until(proc, stopword="readyok"):
    lines = []
    while True:
        line = proc.stdout.readline().strip()
        if line:
            print(line)
            lines.append(line)
        if stopword in line:
            break
    return lines

def handler(event, context):
    # --- USIエンジン起動 ---
    proc = subprocess.Popen(
        [ENGINE_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        cwd="/var/task/Engine"  # ← 重要（ここで移動）
    )


    # --- 初期化 ---
    send(proc, "usi")
    read_lines_until(proc, "usiok")

    send(proc, "setoption name MultiPV value 3")
    send(proc, "isready")
    read_lines_until(proc, "readyok")

    # --- 局面セット＆思考開始 ---
    send(proc, f"position sfen {SFEN}")
    send(proc, f"go movetime {MOVETIME}")
    time.sleep(MOVETIME / 1000 + 1)

    # --- 出力を読み取る ---
    lines = []
    proc.stdin.write("quit\n")
    proc.stdin.flush()

    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        if line.startswith("info") and "multipv" in line:
            lines.append(line)

    # --- パースして表示 ---
    pattern = re.compile(r"score (cp|mate) (-?\d+).*multipv (\d+).*pv (.+)")
    for line in lines:
        match = pattern.search(line)
        if match:
            score_type, score, idx, pv = match.groups()
            score_desc = f"#{score}" if score_type == "mate" else f"{score}"
            print(f"候補{idx}: 評価値={score_desc} 指し手={pv}")



