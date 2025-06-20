import asyncio
import websockets
import pyaudio
import base64
import os
import json
import queue
import threading
from datetime import datetime
import time

## OpenAIのAPIキー
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

## WebSocket URLとヘッダー情報。Websocketに接続してOpenAIのモデルに繋ぐ
# WS_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"  # 旧バージョン
WS_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"  # 新バージョン
HEADERS = {
    "Authorization": "Bearer "+ API_KEY, 
    "OpenAI-Beta": "realtime=v1"
}

## キューを初期化
audio_send_queue = queue.Queue()
audio_receive_queue = queue.Queue()

## PCM16形式に変換する関数
def base64_to_pcm16(base64_audio):
    audio_data = base64.b64decode(base64_audio)
    return audio_data

## ここまでは初期設定----------------------------------------------------------------------------------------------------


## 音声を送信する非同期関数
async def send_audio_from_queue(websocket): ## websocket接続、音声ストリーム、データの読み取り単位サイズが引数
    ## マイクからCHUNKサイズ分の音声データを同期的に読み取る関数

    print("【システム】マイクから音声を取得して送信中...")
    
    while True:
        # マイクから音声を取得（先の関数を使って）
        audio_data = await asyncio.get_event_loop().run_in_executor(None, audio_send_queue.get)
        if audio_data is None:
            continue  # 読み取りに失敗した場合はスキップ
        
        ## PCM16データをBase64にエンコード
        base64_audio = base64.b64encode(audio_data).decode("utf-8")

        ## audio_event辞書に音声データ格納
        audio_event = { 
            "type": "input_audio_buffer.append", ## input_audio_buffer.appendイベント(Client events)を作成
            "audio": base64_audio
        }
        ## input_audio_buffer.appendイベントを送信（WebSocketで音声データを送信）
        await websocket.send(json.dumps(audio_event))
        # キューの処理間隔を少し空ける
        await asyncio.sleep(0)

# マイクからの音声を取得しキューに入れる関数
def read_audio_to_queue(stream, CHUNK):
    while True:
        try:
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            audio_send_queue.put(audio_data)
        except Exception as e:
            print(f"音声読み取りエラー: {e}")
            break


## サーバーから音声を受信して再生する非同期関数
async def receive_audio_to_queue(websocket): ## websocket接続と、音声出力用のストリーム
    print("=====開始します=====") ## コマンドラインに開始タイミングを出力
    print("【AI 】", end = "", flush = True)

    ##########################################
    ## セッション設定更新。開始時に設定される。
    init_request = {
        "type": "session.update",
        "session": {
            "modalities": ["audio", "text"],
            "instructions": """あなたは基本的に日本語で話します。あなたはユーザーの質問に答えるAIアシスタントです。ユーザーの質問に対して、できるだけ正確で役立つ情報を提供してください。
""",
            ## ボイス設定
            "voice": "echo",        ## "alloy","echo","shimmer","ash","ballad","coral","sage","verse"から選べる
            ## ターン検出の設定
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
            },
            ## 文字起こしに必要
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            ## ツール
            "tools": [   
            ],
            ## モデルが何のツールを使うか
            "tool_choice": "auto",
        }
    }
    await websocket.send(json.dumps(init_request)) ## これでイベントをサーバーに送る
    # print("初期リクエストを送信しました")

    # # conversation.item.create　ユーザーが問いかける内容を設定する（ここでは一番最初のタイミングの設定）
    # con_create = {
    #     "type": "conversation.item.create"
    # }
    # await websocket.send(json.dumps(con_create))

    # response_create 開始時に問いかけてくるようにする
    res_create = {
        "type": "response.create"
    }
    await websocket.send(json.dumps(res_create))

    while True:
        # サーバーからの応答を受信、While Trueで継続的に動作
        response = await websocket.recv()

        if response:
            response_data = json.loads(response)

            # イベントを表示（デバッグ用）
            # print(response_data["type"])

            ## サーバーからのデータのtypeに応じて異なる処理をする（Server eventsを処理）
            ## サーバーからの応答をリアルタイム（ストリーム）で表示
            if "type" in response_data and response_data["type"] == "response.audio_transcript.delta":
                print(response_data["delta"], end = "", flush = True)

            # elif "type" in response_data and response_data["type"] == "response.created":
            #     print("【AI】")
                
            ## サーバからの応答が完了したことを取得
            elif "type" in response_data and response_data["type"] == "response.done":
                # print("応答完了")
                # print("\n(音声受付中…)")
                print("\n【AI 】", end = "", flush = True)

                ## 会話履歴を更新
                # print("会話履歴を保存しました")
                
            ## ユーザ発話の文字起こしを出力
            # elif "type" in response_data and response_data["type"] == "conversation.item.input_audio_transcription.completed":
            #     print("【ユーザー】", response_data["transcript"])      
            #     print("【AI】")

            ## レートリミットの情報を取得
            # elif "type" in response_data and response_data["type"] == "rate_limits.updated":
            #     print(f"Rate limits: {response_data['rate_limits'][0]['remaining']} requests remaining.")

            #こちらの発話がスタートしたことをサーバが取得したことを確認する
            if "type" in response_data and response_data["type"] == "input_audio_buffer.speech_started":
                #すでに存在する取得したAI発話音声をリセットする
                while not audio_receive_queue.empty():
                        audio_receive_queue.get() 

            # サーバーからの音声データをキューに格納
            if "type" in response_data and response_data["type"] == "response.audio.delta":
                base64_audio_response = response_data["delta"]
                if base64_audio_response:
                    pcm16_audio = base64_to_pcm16(base64_audio_response)
                    audio_receive_queue.put(pcm16_audio)
       
        await asyncio.sleep(0)

# サーバーからの音声を再生する関数
def play_audio_from_queue(output_stream):
    while True:
        pcm16_audio = audio_receive_queue.get()
        if pcm16_audio:
            output_stream.write(pcm16_audio)
            

## ここまでが音声の送信と受信のタスク（async関数）------------------------------------------------------------------------


## マイクからの音声を取得し、WebSocketで送信しながらサーバーからの音声応答を再生する非同期関数（メインのループ）
async def stream_audio_and_receive_response():

    ## WebSocketに接続
    async with websockets.connect(WS_URL, extra_headers=HEADERS) as websocket: ## このwebsocketに接続することで、OpenAIモデルに繋ぐ
        print("【システム】WebSocketに接続しました")        
        
        # PyAudioの設定
        INPUT_CHUNK = 2400 # マイクからの入力データのチャンクサイズ、データの読み取り単位サイズ
        OUTPUT_CHUNK = 2400
        FORMAT = pyaudio.paInt16 # PCM16形式
        CHANNELS = 1 # モノラル
        INPUT_RATE = 24000 # サンプリングレート（24kHz）
        OUTPUT_RATE = 24000

        # PyAudioインスタンス
        p = pyaudio.PyAudio()

        # マイクストリームの初期化
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=INPUT_RATE, input=True, frames_per_buffer=INPUT_CHUNK)

        # サーバーからの応答音声を再生するためのストリームを初期化
        output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=OUTPUT_RATE, output=True, frames_per_buffer=OUTPUT_CHUNK)

        # マイクの音声読み取りをスレッドで開始
        threading.Thread(target=read_audio_to_queue, args=(stream, INPUT_CHUNK), daemon=True).start()

        # サーバーからの音声再生をスレッドで開始
        threading.Thread(target=play_audio_from_queue, args=(output_stream,), daemon=True).start()

        print("【システム】マイク入力およびサーバーからの音声再生を開始...")

        try:
            # 音声送信タスクと音声受信タスクを非同期で並行実行
            send_task = asyncio.create_task(send_audio_from_queue(websocket))
            receive_task = asyncio.create_task(receive_audio_to_queue(websocket))

            # タスクが終了するまで待機
            await asyncio.gather(send_task, receive_task)

        except KeyboardInterrupt:
            print("終了します...")
        finally:
            if stream.is_active():
                stream.stop_stream()
            stream.close()
            output_stream.stop_stream()
            output_stream.close()
            p.terminate()

if __name__ == "__main__":
    asyncio.run(stream_audio_and_receive_response())