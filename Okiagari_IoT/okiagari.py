import os
import time
import random
from lib_rpi.rpi_ws281x import PixelStrip, Color
from library.__led__ import colorWipe, color_rainbow
import RPi.GPIO as GPIO
from pydub import AudioSegment
import requests
import datetime
import asyncio

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

#pathの定義
voicevox_core_path = "/home/pi/Okiagari_IoT/voicevox_core-0.11.4/example/python/"
audio_path = "/home/pi/AizuHack2023/Okiagari_IoT/audio"
music_path = "/home/pi/AizuHack2023/Reminder_flask_server/musics/"

#定型文の定義
recent_sentence1 = AudioSegment.from_wav(f"{audio_path}/sentence/直近5件のタスクをお伝えします。-1.wav")
recent_sentence2 = AudioSegment.from_wav(f"{audio_path}/sentence/現在のタスクは、-1.wav")
recent_sentence3 = AudioSegment.from_wav(f"{audio_path}/sentence/です。-1.wav")

#応援の定型文の定義(Path)
encourage_audio_paths = [
    f"{audio_path}/encourage/頑張ってください。-1.wav",
    f"{audio_path}/encourage/応援しています。-1.wav",
    f"{audio_path}/encourage/ファイトです！。-1.wav"
]

speaker_id = 1  # ずんだもんのスピーカーID

#PIN 17のボタンの処理
#直近の5件のタスクを音声でおしえてくれる
def execute_recent_task():  
    print("タスクを流します")
    recent_tasks = get_tasks()
    tasks_audio = generete_tasks_voice(recent_tasks)
    
    sentence = recent_sentence1 + recent_sentence2 + tasks_audio + recent_sentence3
    # 結合されたサウンドを保存
    sentence.export("audio/recent/tasks_sentence.wav", format="wav")
    #音楽の再生
    os.system(f"su pi -c \"aplay {audio_path}/recent/tasks_sentence.wav\"")
    
    #応援文の作成
    audio = random.choice(encourage_audio_paths)
    AudioSegment.from_wav(audio)
    os.system(f"su pi -c \"aplay {audio}\"")

global single_task_audio
#PIN 23のボタンの処理
#流れている音声を中止して、現在のタスクを音声でおしえてくれる
async def execute_stop_task():
    
    #音楽の停止
    os.system("su pi -c 'killall aplay'")
    #アナウンスの再生
    #現在のタスクを取得中です。しばらくお待ちください。

    sentence = recent_sentence2 + single_task_audio + recent_sentence3
    sentence.export("audio/recent/single_task_sentence.wav", format="wav")

    os.system(f"su pi -c \"aplay {audio_path}/recent/single_task_sentence.wav\"")
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
def play_music(filename):
    print('音楽を再生しました')

    os.system(f"su pi -c \"aplay {music_path}{filename}\"")
    
#LEDの消灯
def turn_off():
    print('LEDを消灯しました')
    colorWipe(strip, Color(0, 0, 0)) 
    colorWipe(strip, Color(0, 0, 0))  

#最新のタスクの音声合成
def generete_single_task_voice(recent_task):
        task_name = f"{recent_task['name']}"
        command = f"cd {voicevox_core_path} && su pi -c 'python3 run.py --text '{task_name}', ' --speaker_id {speaker_id}'"
        os.system(command)

        single_task_audio = AudioSegment.from_wav(f"{voicevox_core_path}" + task_name + "-1.wav")
        single_task_audio.export("audio/recent/recent_tasks.wav", format="wav")

        return single_task_audio


#最新の5個のタスクの音声合成
def generete_tasks_voice(recent_tasks):
        recent_5_tasks = recent_tasks[:5]   # 最新の5件のタスクを取得
        recent_5_tasks_name = f"{recent_5_tasks[0]['name']}, {recent_5_tasks[1]['task_name']}, {recent_5_tasks[2]['name']}, {recent_5_tasks[3]['name']}, {recent_5_tasks[4]['name']}"
        # recent_5_tasksの音声合成 5個一気に音声合成する
        command = f"cd {voicevox_core_path} && su pi -c 'python3 run.py --text '{recent_5_tasks_name}', ' --speaker_id {speaker_id}'"
        os.system(command)

        tasks_audio = AudioSegment.from_wav(f"{voicevox_core_path}" + recent_5_tasks_name + "-1.wav")
        tasks_audio.export("audio/recent/recent_tasks.wav", format="wav")

        return tasks_audio


#タスクの取得
def get_tasks():
    server_url = '192,168.10.108:8000/notification' #サーバーのURL
    response = requests.get(server_url)
    if response.status_code == 200:
        tasks_data = response.json()
        return tasks_data
    else:
        print('タスクの取得に失敗しました')

#最新のタスクの取得
def get_recent_tasks():
    server_url = '192,168.10.108:8000/notification' #サーバーのURL
    response = requests.get(server_url)
    if response.status_code == 200:
        tasks_data = response.json()
        return tasks_data
    else:
        print('最新のタスクの取得に失敗しました')


async def main():
    while True:

        #締め切り時間を過ぎたら音楽を流す処理
        task = get_recent_tasks()
        recent_task = task
        recent_until_time = task['notice']
        current_time = datetime.datetime.now()
        until_time = datetime.datetime.strptime(recent_until_time, '%Y-%m-%d %H:%M:%S')

        time_difference = until_time - current_time

        if time_difference.total_seconds() < 0:
            filepath = ''
            color_rainbow(strip)
            await asyncio.gather(play_music(filepath), generete_single_task_voice(recent_task["file_name"])) 
            time.sleep(20)
            turn_off() 

asyncio.run(main())   

   
 