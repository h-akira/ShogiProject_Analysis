import subprocess
import time
import re
import json
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ENGINE_PATH = "./YaneuraOu-by-gcc"
MOVETIME = 3000  # ミリ秒
MAIN_TABLE_NAME = "table-sgp-main"

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
  # Lambdaのテストイベントを使用する場合、eventにtestを追加する
  if event.get("test") == "test":
    event["Records"] = [
      {
        "body": json.dumps(
          {
            "username": "testuser",
            "aid": None,
            "position": "lnsgkgsnl/1r5b1/p1pppp1p1/6p1p/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL b - 1"
          }
        )
      }
    ]
  for record in event['Records']:
    body = json.loads(record['body'])
    logger.info(f"username: {body['username']}")
    logger.info(f"aid: {body['aid']}")
    logger.info(f"position: {body['position']}")
    try:
      result = analysis(body['position'])
      status = "successed"
    except Exception as e:
      logger.error(f"Error: {e}")
      result = {}
      status = "failed"
    if event.get("test") == "test":
      logger.info("test mode end")
      return None
    else:
      table = boto3.resource('dynamodb').Table(MAIN_TABLE_NAME)
      table.update_item(
        Key={
          'pk': f"analysis",
          'sk': f"aid#{body['aid']}"
        },
        UpdateExpression="set #status=:st, #response=:re",
        ExpressionAttributeNames={
          "#status": "status",
          "#response": "response"
        },
        ExpressionAttributeValues={
          ':st': status,
          ':re': json.dumps(result)
        }
      )
      return None

def analysis(SFEN):
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
      result[idx] = {
        "score": score_desc,
        "pv": pv
      }
  logger.info(f"result: {json.dumps(result)}")
  return result




