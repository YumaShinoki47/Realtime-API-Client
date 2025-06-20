# Realtime API Client

OpenAIのRealtime APIを使用したリアルタイム音声対話アプリケーションです。マイクからの音声入力をリアルタイムでAIに送信し、AI応答を音声で受け取ることができます。

## 機能

- リアルタイム音声入力・出力
- WebSocketを使用した双方向通信
- 日本語での音声対話
- PCM16フォーマット（24kHz、モノラル）での高品質音声処理

## 必要な環境

- Python 3.7以上
- PyAudio（システムレベルの音声ライブラリが必要な場合があります）
- OpenAI API キー

## インストール

1. 依存関係をインストール：
```bash
pip install asyncio websockets pyaudio base64 json queue threading
```

2. 環境変数を設定：
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## 使用方法

アプリケーションを実行：
```bash
python main.py
```

実行後、マイクに向かって話しかけると、AIが音声で応答します。
`Ctrl+C`で終了できます。

## 技術仕様

### 音声設定
- 形式：16-bit PCM
- サンプリングレート：24,000 Hz
- チャンネル：1（モノラル）
- チャンクサイズ：2,400サンプル

### AI設定
- モデル：gpt-4o-realtime-preview-2024-12-17
- 音声：echo
- 言語：日本語
- 音声認識：Whisper-1

## 注意事項

- OpenAI APIの使用料金が発生します
- インターネット接続が必要です
- マイクとスピーカーを使用できる環境が必要です