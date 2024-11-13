# 랭체인 2차 Test
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import speech, texttospeech
from langchain.llms import OpenAI
import os
import asyncio
import time
import uvicorn
import io
import wave
import struct
# 노드로 보내기
import requests

# 환경 변수 설정 (Google Cloud 인증서 경로)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/shimgeon-u/test/carbot_back_2/carbot_back/credentials.json'

# FastAPI 인스턴스 생성
app = FastAPI()

# Google Cloud STT 및 TTS 클라이언트 생성
stt_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()

# OpenAI GPT-4 모델 사용 (OpenAI API 키 필요)
# llm = OpenAI 키 적어야함
# 1차 코드
def extract_pcm_data(wav_file_path):
    try:
        with wave.open(wav_file_path, 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()

            # 형식 검증: 모노 채널, 16-bit 샘플 너비, 16000 Hz 샘플링 속도
            if channels != 1 or sample_width != 2 or frame_rate != 16000:
                print("WAV 파일 형식이 올바르지 않습니다. 모노 채널, 16-bit, 16000 Hz 형식이어야 합니다.")
                return None

            # PCM 데이터 추출 (WAV 헤더 제외)
            pcm_data = wav_file.readframes(wav_file.getnframes())
            print("PCM 데이터 추출 완료")
            return pcm_data
    except Exception as e:
        print(f"PCM 데이터 추출 중 오류 발생: {e}")
        return None


# 일정 시간 동안 오디오 데이터를 수집하고, 인식 요청을 보내는 함수
async def process_audio_data(audio_data):
    if len(audio_data) == 0:
        print("수집된 오디오 데이터가 없습니다.")
        return ""

    print("음성 인식을 시작합니다...")
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR"
    )

    try:
        response = stt_client.recognize(config=config, audio=audio)
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        print(f"인식된 텍스트: {transcript}")
        return transcript
    except Exception as e:
        print(f"음성 인식 중 오류 발생: {e}")
        return ""

# LangChain을 사용하여 응답 생성
def generate_response(text):
    prompt = f"사용자가 '{text}'라고 질문했습니다. 간단하고 친절하게 답변해 주세요."
    try:
        response = llm.invoke(prompt)
        print(f"LangChain 응답: {response}")
        return response
    except Exception as e:
        print(f"LangChain 응답 생성 중 오류 발생: {e}")
        return "죄송합니다, 이해하지 못했습니다."

# TTS를 사용하여 응답 텍스트를 음성으로 변환하고, WAV 형식으로 저장
def convert_text_to_speech(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    try:
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        audio_content = response.audio_content

        # WAV 형식으로 변환 및 저장
        with wave.open("output.wav", 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000) # 24000 : 1배속 
            wav_file.writeframes(audio_content)

        # 파일을 읽어 WebSocket으로 전송할 데이터 준비
        with open("output.wav", "rb") as wav_file:
            wav_data = wav_file.read()

        print("TTS 변환 완료 및 WAV 파일 저장")
        return wav_data
    except Exception as e:
        print(f"TTS 변환 중 오류 발생: {e}")
        return None

# WebSocket을 통해 `output.wav` 파일을 전송하는 함수
def stream_wav_file(websocket, file_path):
    try:
        with wave.open(file_path, 'rb') as wav_file:
            # WAV 파일의 헤더와 데이터를 읽어 스트리밍
            chunk_size = 1024
            data = wav_file.readframes(chunk_size)
            while data:
                websocket.send_bytes(data)
                data = wav_file.readframes(chunk_size)
        print("WAV 파일 스트리밍 완료")
    except Exception as e:
        print(f"WAV 파일 스트리밍 중 오류 발생: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket 연결이 수립되었습니다.")

    audio_data = b""
    start_time = time.time()

    try:
        # 첫 번째로 JSON 메타 데이터를 수신
        try:
            message = await websocket.receive_json()
            print("JSON 메타 데이터 수신:", message)
        except Exception as e:
            print(f"JSON 데이터 수신 오류: {e}")

        # 음성 수집 및 처리 루프
        while True:
            message = await websocket.receive_bytes()

            # 빈 데이터 체크
            if message is None or len(message) == 0:
                continue

            # 오디오 데이터를 누적 저장
            audio_data += message

            # 5초 동안 데이터 수집 후 인식 요청 전송
            if time.time() - start_time >= 5:
                print("5초 동안 데이터 수집 완료, 음성 인식 시작")
                transcript = await process_audio_data(audio_data)
                if transcript:
                    # LangChain을 사용하여 응답 생성
                    response_text = generate_response(transcript)

                    # TTS로 응답 텍스트를 음성으로 변환 (MP3 형식)
                    audio_response = convert_text_to_speech(response_text)
                    if audio_response:
                        # WebSocket을 통해 TTS 오디오 응답 전송
                        await websocket.send_bytes(audio_response)

                # 오디오 데이터 초기화 및 타이머 리셋
                audio_data = b""
                start_time = time.time()
            # # `output.wav` 파일을 WebSocket으로 스트리밍
            # stream_wav_file(websocket, "output.wav")

    except WebSocketDisconnect:
        print("WebSocket 연결이 끊어졌습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

    print("WebSocket 연결이 종료되었습니다.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5005)

# 2차 코드
# Node.js로 LangChain 응답 전송 함수
# def send_response_to_node(text):
#     url = "https://d66d-222-112-27-104.ngrok-free.app/api/vonage/update-text"
#     data = {"text": text}
#     try:
#         response = requests.post(url, json=data)
#         if response.status_code == 200:
#             print("Node.js 서버로 응답 텍스트 전송 완료")
#         else:
#             print(f"Node.js 서버로 전송 실패: {response.status_code}")
#     except Exception as e:
#         print(f"Node.js 서버로 전송 중 오류 발생: {e}")

# # STT 요청을 처리하는 함수
# async def process_audio_data(audio_data):
#     if not audio_data:
#         print("수집된 오디오 데이터가 없습니다.")
#         return ""

#     print("음성 인식을 시작합니다...")
#     audio = speech.RecognitionAudio(content=audio_data)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=16000,
#         language_code="ko-KR"
#     )

#     try:
#         response = stt_client.recognize(config=config, audio=audio)
#         transcript = "".join([result.alternatives[0].transcript for result in response.results])
#         print(f"인식된 텍스트: {transcript}")
#         return transcript
#     except Exception as e:
#         print(f"음성 인식 중 오류 발생: {e}")
#         return ""

# # LangChain을 사용하여 응답 생성
# def generate_response(text):
#     prompt = f"사용자가 '{text}'라고 질문했습니다. 간단하게 답변해 주세요."
#     try:
#         response = llm.invoke(prompt)
#         print(f"LangChain 응답: {response}")
#         return response
#     except Exception as e:
#         print(f"LangChain 응답 생성 중 오류 발생: {e}")
#         return "죄송합니다, 이해하지 못했습니다."

# # WebSocket 엔드포인트
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("WebSocket 연결이 수립되었습니다.")

#     audio_data = b""
#     start_time = time.time()

#     try:
#         # JSON 메타 데이터 수신
#         try:
#             message = await websocket.receive_json()
#             print("JSON 메타 데이터 수신:", message)
#         except Exception as e:
#             print(f"JSON 데이터 수신 오류: {e}")

#         while True:
#             message = await websocket.receive_bytes()
#             if not message:
#                 continue

#             audio_data += message

#             # 5초 동안 데이터 수집 후 인식 요청 전송
#             if time.time() - start_time >= 5:
#                 transcript = await process_audio_data(audio_data)
#                 if transcript:
#                     response_text = generate_response(transcript)
#                     send_response_to_node(response_text)

#                 audio_data = b""
#                 start_time = time.time()

#     except WebSocketDisconnect:
#         print("WebSocket 연결이 끊어졌습니다.")
#     except Exception as e:
#         print(f"오류 발생: {e}")

#     print("WebSocket 연결이 종료되었습니다.")

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=5005)



# # PCM 데이터를 청크 단위로 WebSocket을 통해 전송
# async def send_pcm_data_in_chunks(websocket, pcm_data, chunk_size=1024):
#     try:
#         # 청크 단위로 PCM 데이터 전송
#         for i in range(0, len(pcm_data), chunk_size):
#             chunk = pcm_data[i:i + chunk_size]
#             await websocket.send_bytes(chunk)
#         print("PCM 데이터 청크 전송 완료")

#         # 무음 패딩 전송 (keep-alive)
#         silence_padding = generate_silence(200)  # 200ms 무음 패딩
#         await websocket.send_bytes(silence_padding)
#         print("무음 패딩 전송 완료")
#     except Exception as e:
#         print(f"PCM 데이터 청크 전송 중 오류 발생: {e}")
        
# # PCM 데이터를 추출하는 함수 (WAV 헤더 제거)
# def extract_pcm_data(wav_file_path):
#     try:
#         with wave.open(wav_file_path, 'rb') as wav_file:
#             channels = wav_file.getnchannels()
#             sample_width = wav_file.getsampwidth()
#             frame_rate = wav_file.getframerate()

#             # 형식 검증: 모노 채널, 16-bit 샘플 너비, 16000 Hz 샘플링 속도
#             if channels != 1 or sample_width != 2 or frame_rate != 16000:
#                 print("WAV 파일 형식이 올바르지 않습니다. 모노 채널, 16-bit, 16000 Hz 형식이어야 합니다.")
#                 return None

#             # PCM 데이터 추출 (WAV 헤더 제외)
#             pcm_data = wav_file.readframes(wav_file.getnframes())
#             print("PCM 데이터 추출 완료")
#             return pcm_data
#     except Exception as e:
#         print(f"PCM 데이터 추출 중 오류 발생: {e}")
#         return None


# # Silence 패딩 추가 함수 (무음 데이터 생성)
# def generate_silence(duration_ms, sample_rate=16000):
#     num_samples = int(duration_ms * sample_rate / 1000)
#     return b'\x00' * num_samples * 2  # 16-bit PCM, 모노 채널

# # PCM 데이터를 Signed 16-bit Little Endian 형식으로 변환
# def convert_to_signed_16bit_le(pcm_data):
#     try:
#         signed_pcm_data = b""
#         for sample in struct.iter_unpack("h", pcm_data):
#             int_sample = int(sample[0])
#             signed_pcm_data += struct.pack("<h", int_sample)

#         print("Signed 16-bit Little Endian 변환 완료")
#         return signed_pcm_data
#     except Exception as e:
#         print(f"PCM 데이터 변환 중 오류 발생: {e}")
#         return None

# 일정 시간 동안 오디오 데이터를 수집하고, 인식 요청을 보내는 함수
# async def process_audio_data(audio_data):
#     if len(audio_data) == 0:
#         print("수집된 오디오 데이터가 없습니다.")
#         return ""

#     print("음성 인식을 시작합니다...")
#     audio = speech.RecognitionAudio(content=audio_data)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=16000,
#         language_code="ko-KR"
#     )

#     try:
#         response = stt_client.recognize(config=config, audio=audio)
#         transcript = "".join([result.alternatives[0].transcript for result in response.results])
#         print(f"인식된 텍스트: {transcript}")
#         return transcript
#     except Exception as e:
#         print(f"음성 인식 중 오류 발생: {e}")
#         return ""

# # LangChain을 사용하여 응답 생성
# def generate_response(text):
#     prompt = f"사용자가 '{text}'라고 질문했습니다. 간단하고 친절하게 답변해 주세요."
#     try:
#         response = llm.invoke(prompt)
#         print(f"LangChain 응답: {response}")
#         return response
#     except Exception as e:
#         print(f"LangChain 응답 생성 중 오류 발생: {e}")
#         return "죄송합니다, 이해하지 못했습니다."

# # TTS 변환 함수 (재시도 로직 포함)
# def convert_text_to_speech(text):
#     synthesis_input = texttospeech.SynthesisInput(text=text)
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="ko-KR",
#         ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
#     )
#     audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

#     max_retries = 3
#     for attempt in range(max_retries):
#         try:
#             response = tts_client.synthesize_speech(
#                 input=synthesis_input, voice=voice, audio_config=audio_config
#             )
#             audio_content = response.audio_content

#             with wave.open("output.wav", 'wb') as wav_file:
#                 wav_file.setnchannels(1)
#                 wav_file.setsampwidth(2)
#                 wav_file.setframerate(16000)
#                 wav_file.writeframes(audio_content)

#             print("TTS 변환 완료 및 WAV 파일 저장")
#             return audio_content
#         except Exception as e:
#             print(f"TTS 변환 중 오류 발생: {e}")
#             if "503" in str(e):
#                 print("503 오류 발생, 재시도 중...")
#                 time.sleep(2)
#             else:
#                 return None
#     return None


# # WebSocket 처리 함수
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("WebSocket 연결이 수립되었습니다.")

#     audio_data = b""
#     start_time = time.time()

#     try:
#         message = await websocket.receive_json()
#         print("JSON 메타 데이터 수신:", message)

#         while True:
#             message = await websocket.receive_bytes()
#             if not message:
#                 continue

#             audio_data += message

#             if time.time() - start_time >= 5:
#                 transcript = await process_audio_data(audio_data)
#                 if transcript:
#                     response_text = generate_response(transcript)
#                     convert_text_to_speech(response_text)
#                     pcm_data = extract_pcm_data("output.wav")

#                     if pcm_data:
#                         signed_pcm_data = convert_to_signed_16bit_le(pcm_data)
#                         if signed_pcm_data:
#                             print("PCM 데이터 전송 시작")
#                             await websocket.send_bytes(signed_pcm_data)
#                             silence_padding = generate_silence(500)
#                             for _ in range(5):
#                                 await websocket.send_bytes(silence_padding)
#                                 await asyncio.sleep(0.5)

#                 audio_data = b""
#                 start_time = time.time()

#     except WebSocketDisconnect:
#         print("WebSocket 연결이 끊어졌습니다.")
#     except Exception as e:
#         print(f"오류 발생: {e}")

#     print("WebSocket 연결이 종료되었습니다.")

# Node.js로 LangChain 응답 전송 함수 (수정된 부분)
# def send_response_to_node(text):
#     url = "https://d66d-222-112-27-104.ngrok-free.app/api/vonage/update-text"  # Node.js 서버의 update-text 엔드포인트
#     data = {"text": text}
#     try:
#         response = requests.post(url, json=data)
#         if response.status_code == 200:
#             print("Node.js 서버로 응답 텍스트 전송 완료")
#         else:
#             print(f"Node.js 서버로 전송 실패: {response.status_code}")
#     except Exception as e:
#         print(f"Node.js 서버로 전송 중 오류 발생: {e}")

# # 일정 시간 동안 오디오 데이터를 수집하고, STT 요청을 보내는 함수
# async def process_audio_data(audio_data):
#     if len(audio_data) == 0:
#         print("수집된 오디오 데이터가 없습니다.")
#         return ""

#     print("음성 인식을 시작합니다...")
#     audio = speech.RecognitionAudio(content=audio_data)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=16000,
#         language_code="ko-KR"
#     )

#     try:
#         response = stt_client.recognize(config=config, audio=audio)
#         transcript = "".join([result.alternatives[0].transcript for result in response.results])
#         print(f"인식된 텍스트: {transcript}")
#         return transcript
#     except Exception as e:
#         print(f"음성 인식 중 오류 발생: {e}")
#         return ""

# # LangChain을 사용하여 응답 생성
# def generate_response(text):
#     prompt = f"사용자가 '{text}'라고 질문했습니다. 간단하게 답변해 주세요."
#     try:
#         response = llm.invoke(prompt)
#         print(f"LangChain 응답: {response}")
#         return response
#     except Exception as e:
#         print(f"LangChain 응답 생성 중 오류 발생: {e}")
#         return "죄송합니다, 이해하지 못했습니다."

# # WebSocket 엔드포인트
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("WebSocket 연결이 수립되었습니다.")

#     audio_data = b""
#     start_time = time.time()

#     try:
#         # 첫 번째로 JSON 메타 데이터를 수신
#         try:
#             message = await websocket.receive_json()
#             print("JSON 메타 데이터 수신:", message)
#         except Exception as e:
#             print(f"JSON 데이터 수신 오류: {e}")

#         # 음성 수집 및 처리 루프
#         while True:
#             message = await websocket.receive_bytes()

#             # 빈 데이터 체크
#             if message is None or len(message) == 0:
#                 continue

#             # 오디오 데이터를 누적 저장
#             audio_data += message

#             # 5초 동안 데이터 수집 후 인식 요청 전송
#             if time.time() - start_time >= 5:
#                 print("5초 동안 데이터 수집 완료, 음성 인식 시작")
#                 transcript = await process_audio_data(audio_data)
#                 if transcript:
#                     # LangChain을 사용하여 응답 생성
#                     response_text = generate_response(transcript)
#                     # Node.js로 텍스트 전송
#                     send_response_to_node(response_text)

#                 # 오디오 데이터 초기화 및 타이머 리셋
#                 audio_data = b""
#                 start_time = time.time()

#     except WebSocketDisconnect:
#         print("WebSocket 연결이 끊어졌습니다.")
#     except Exception as e:
#         print(f"오류 발생: {e}")

#     print("WebSocket 연결이 종료되었습니다.")

# if __name__ == "__main__":

# # if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=5005)
