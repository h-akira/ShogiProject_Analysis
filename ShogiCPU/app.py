import subprocess
import time
import re
import json
import boto3

ENGINE_PATH = "./YaneuraOu-by-gcc"
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
  # エンジン起動
  proc = subprocess.Popen(
    [ENGINE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    cwd="/var/task/Engine"
  )
  # 初期化
  send(proc, "usi")
  read_lines_until(proc, "usiok")
  send(proc, "setoption name MultiPV value 3")
  send(proc, "isready")
  read_lines_until(proc, "readyok")
  # 局面セット＆思考開始
  send(proc, f"position sfen {SFEN}")
  send(proc, f"go movetime {MOVETIME}")
  time.sleep(MOVETIME / 1000 + 1)
  # 出力を読み取る
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
  # パースして格納
  result = {}
  pattern = re.compile(r"score (cp|mate) (-?\d+).*multipv (\d+).*pv (.+)")
  for line in lines:
    match = pattern.search(line)
    if match:
      score_type, score, idx, pv = match.groups()
      score_desc = f"#{score}" if score_type == "mate" else f"{score}"
      # print(f"候補{idx}: 評価値={score_desc} 指し手={pv}")
      result[idx] = {
        "score": score_desc,
        "pv": pv
      }
  print(json.dumps(result, ensure_ascii=False, indent=2))



