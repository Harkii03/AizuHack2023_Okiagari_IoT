import argparse
from typing import Optional

import core
import soundfile

# 音声合成を行うモジュールのインポート
from forwarder import Forwarder


def generate_audio(text, speaker_id):
    use_gpu = False  # GPUを使用しない
    f0_speaker_id = None  # 基本周波数の発話者IDを指定しない
    f0_correct = 0  # 基本周波数の補正値を0に設定
    root_dir_path = "../../release"  # VOICEVOX COREのルートディレクトリのパスを指定
    cpu_num_threads = 0  # CPUスレッド数を指定

    # コアの初期化
    core.initialize(root_dir_path, use_gpu, cpu_num_threads)

    # 音声合成処理モジュールの初期化
    forwarder = Forwarder(
        yukarin_s_forwarder=core.yukarin_s_forward,
        yukarin_sa_forwarder=core.yukarin_sa_forward,
        decode_forwarder=core.decode_forward,
    )

    # 音声合成
    wave = forwarder.forward(
        text=text,
        speaker_id=speaker_id,
        f0_speaker_id=f0_speaker_id if f0_speaker_id is not None else speaker_id,
        f0_correct=f0_correct,
    )

    # 保存
    soundfile.write(f"{text}-{speaker_id}.wav", data=wave, samplerate=24000)

    core.finalize()


# コマンドライン引数としてテキストとスピーカーIDを指定する
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--speaker_id", type=int, required=True)
    args = parser.parse_args()

    generate_audio(args.text, args.speaker_id)
