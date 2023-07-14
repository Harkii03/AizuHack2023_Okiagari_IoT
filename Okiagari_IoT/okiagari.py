import os
import time
import random
from lib_rpi.rpi_ws281x import PixelStrip, Color
from library.__led__ import colorWipe, hex_to_rgb, color_rainbow
import RPi.GPIO as GPIO
from pydub import AudioSegment
import requests
import datetime

# LED strip configuration:
LED_COUNT = 16        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Create NeoPixel object with appropriate configuration.
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

#定型文の定義
recent_sentence1 = AudioSegment.from_wav("/home/pi/Okiagari_IoT/audio/sentence/直近5件のタスクをお伝えします。-1.wav")
recent_sentence2 = AudioSegment.from_wav("/home/pi/Okiagari_IoT/audio/sentence/現在のタスクは、-1.wav")
recent_sentence3 = AudioSegment.from_wav("/home/pi/Okiagari_IoT/audio/sentence/です。-1.wav")

#応援の定型文の定義(Path)
encourage_audio_paths = [
    "/home/pi/Okiagari_IoT/audio/encourage/頑張ってください。-1.wav",
    "/home/pi/Okiagari_IoT/audio/encourage/応援しています。-1.wav",
    "/home/pi/Okiagari_IoT/audio/encourage/ファイトです！。-1.wav"
]

voicevox_core_path = "/home/pi/Okiagari_IoT/voicevox_core-0.11.4/example/python/"

#PIN 17のボタンの処理
#直近の5件のタスクを音声でおしえてくれる
def execute_recent_task(task_data):  
    print("ボタンが押されました")
    recent_task = task_data  
    speaker_id = 1  # ずんだもんのスピーカーID

    # タスクの音声合成
    command = f"cd {voicevox_core_path} && su pi -c 'python3 run.py --text \"{recent_task}\" --speaker_id {speaker_id}'"
    os.system(command)
    task = AudioSegment.from_wav(f"{voicevox_core_path}" + recent_task + "-1.wav")
    sentence = recent_sentence1 + recent_sentence2 + task + recent_sentence3
    # 結合されたサウンドを保存
    sentence.export("audio/recent/sentence.wav", format="wav")
    #音楽の再生
    os.system("su pi -c \"aplay /home/pi/Okiagari_IoT/audio/recent/sentence.wav\"")
    time.sleep(3)
    
    #応援文の作成
    audio = random.choice(encourage_audio_paths)
    AudioSegment.from_wav(audio)
    os.system(f"su pi -c \"aplay {audio}\"")


#PIN 23のボタンの処理
#流れている音声を中止して、現在のタスクを音声でおしえてくれる
def execute_stop_task():
    recent_task = task_data[0] 
    speaker_id = 1 #ずんだもんのスピーカーID
    
    os.system("su pi -c \"killall aplay\"")

    command = f"cd {voicevox_core_path} && su pi -c 'python3 run.py --text \"{recent_task}\" --speaker_id {speaker_id}'"
    os.system(command)
    task = AudioSegment.from_wav(f"{voicevox_core_path}" + recent_task + "-1.wav")
    sentence = recent_sentence2 + task + recent_sentence3
    sentence.export("audio/recent/sentence.wav", format="wav")

    os.system("su pi -c \"aplay /home/pi/Okiagari_IoT/audio/recent/sentence.wav\"")
    time.sleep(3)
    
    #応援文の作成
    audio = random.choice(encourage_audio_paths)
    AudioSegment.from_wav(audio)
    os.system(f"su pi -c \"aplay {audio}\"")

#GPIOの設定
BUTTON1_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BUTTON1_PIN, GPIO.FALLING, callback=execute_recent_task, bouncetime=200)

BUTTON2_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BUTTON2_PIN, GPIO.FALLING, callback=execute_stop_task, bouncetime=200)

#音楽の再生
def play_music():
    print('音楽を再生しました')

    # POSTリクエストから音楽のIDを取得
    music = get_set_music()
    music.export("audio/music/music.wav", format="wav")

    #音楽の再生
    os.system("su pi -c \"aplay /home/pi/Okiagari_IoT/audio/music/music.wav\"")
    

#色の変更
def change_color():
    print('色を変更しました')
    color = get_set_color() #color code を取得
    #色の文字列をRGBに変換
    rgb = hex_to_rgb(color)
    #色を表示    
    colorWipe(strip, Color(rgb[0], rgb[1], rgb[2]))


def turn_off():
    print('LEDを消灯しました')
    colorWipe(strip, Color(0, 0, 0))  


#タスクの取得
def get_recent_tasks():
    server_url = '' #サーバーのURL
    response = requests.get(server_url)
    if response.status_code == 200:
        global task_data
        task_data = response.json()
    else:
        print('タスクの取得に失敗しました')

#曲の取得
def get_set_music():
    server_url = '' #サーバーのURL
    response = requests.get(server_url)
    if response.status_code == 200:
        music_data = response.json()
        music = AudioSegment.from_wav(f"audio/music/{music_data['music_name']}")
        return music
    else:
        print('音楽の取得に失敗しました')

#色の取得
def get_set_color():
    server_url = '' #サーバーのURL
    response = requests.get(server_url)
    if response.status_code == 200:
        color_data = response.json()
        return color_data['color']
    else:
        print('色の取得に失敗しました')



while True:
    
    get_recent_tasks()
    current_time = datetime.datetime.now()

    for task in task_data:
        deadline = datetime.datetime.strptime(task['deadline'], '%Y-%m-%d %H:%M:%S')

        # タスクの締め切り時間との差を計算
        time_difference = deadline - current_time

        
        if 3 <= time_difference.total_seconds() // 3600 < 4:
            play_music()

        
        if 1 <= time_difference.total_seconds() // 3600 < 2:
            play_music()
                
        if 30 <= time_difference.total_seconds() // 60 < 31:
            play_music()

        
        if 10 <= time_difference.total_seconds() // 60 < 11:
            play_music()

        
        if 5 <= time_difference.total_seconds() // 60 < 6:
            play_music()
            color_rainbow()

    time.sleep(5)
    