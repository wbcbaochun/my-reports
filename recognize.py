#!/usr/bin/env python3
import speech_recognition as sr
import sys

def transcribe_wav(wav_file):
    r = sr.Recognizer()
    with sr.AudioFile(wav_file) as source:
        audio = r.record(source)
    
    try:
        text = r.recognize_google(audio, language='zh-CN')
        return text
    except sr.UnknownValueError:
        return "无法识别音频"
    except sr.RequestError as e:
        return f"Google Speech Recognition服务错误: {e}"

if __name__ == "__main__":
    text = transcribe_wav("audio.wav")
    print(text)