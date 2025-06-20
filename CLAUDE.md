# CLAUDE.md
基本的に日本語で回答してください。
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based real-time audio streaming application that interfaces with OpenAI's Realtime API. The application enables bidirectional audio communication using WebSockets, allowing users to speak to an AI assistant and receive spoken responses in real-time.

## Core Architecture

### Main Components
- **main.py**: Primary application with full WebSocket implementation, session management, and comprehensive audio handling

### Audio Processing Pipeline
1. **Input**: PyAudio captures microphone input in PCM16 format (24kHz, mono)
2. **Encoding**: Audio data is Base64-encoded for WebSocket transmission
3. **WebSocket**: Bidirectional communication with OpenAI's Realtime API
4. **Output**: Received audio is decoded and played through speakers

### Threading Architecture
- Main async loop handles WebSocket communication
- Separate threads for:
  - Reading audio from microphone (`read_audio_to_queue`)
  - Playing received audio (`play_audio_from_queue`)
- Queue-based communication between threads (`audio_send_queue`, `audio_receive_queue`)

## Development Commands

### Running the Application
```bash
python main.py          # Run the main application
python sample.py        # Run the simplified version
```

### Dependencies
Install required packages:
```bash
pip install asyncio websockets pyaudio base64 json queue threading
```

Note: PyAudio may require system-level audio libraries depending on your platform.

## Configuration

### API Settings
- API key is loaded from the `OPENAI_API_KEY` environment variable
- WebSocket URL uses OpenAI's Realtime API endpoint with gpt-4o-realtime-preview-2024-12-17 model
- Audio format: PCM16, 24kHz sample rate, mono channel

### Environment Variables
Set the following environment variable before running:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Session Configuration
The application configures the AI session with:
- Japanese language instructions
- Voice selection (echo/alloy)
- Server-side Voice Activity Detection (VAD)
- Whisper-1 model for transcription

## Important Notes

### Security Considerations
- API keys are now securely loaded from environment variables
- Ensure the `OPENAI_API_KEY` environment variable is not committed to version control

### Audio Specifications
- Chunk size: 2400 samples for both input and output
- Format: 16-bit PCM
- Sample rate: 24000 Hz
- Channels: 1 (mono)

### WebSocket Events
The application handles various OpenAI Realtime API events:
- `input_audio_buffer.append` - Send audio data
- `response.audio.delta` - Receive audio chunks
- `response.audio_transcript.delta` - Real-time transcription
- `input_audio_buffer.speech_started` - User speech detection