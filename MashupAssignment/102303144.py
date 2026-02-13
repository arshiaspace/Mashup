import sys
import os
import shutil
from yt_dlp import YoutubeDL
from pydub import AudioSegment


def validate_inputs(args):
    if len(args) != 5:
        print("Usage: python 102303144.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        sys.exit(1)

    singer = args[1]

    try:
        num_videos = int(args[2])
        if num_videos <= 10:
            raise ValueError
    except ValueError:
        print("Error: NumberOfVideos must be an integer greater than 10.")
        sys.exit(1)

    try:
        duration = int(args[3])
        if duration <= 20:
            raise ValueError
    except ValueError:
        print("Error: AudioDuration must be an integer greater than 20 seconds.")
        sys.exit(1)

    output_file = args[4]
    if not output_file.endswith(".mp3"):
        print("Error: OutputFileName must end with .mp3")
        sys.exit(1)

    return singer, num_videos, duration, output_file


def create_directories():
    if os.path.exists("downloads"):
        shutil.rmtree("downloads")
    if os.path.exists("trimmed"):
        shutil.rmtree("trimmed")

    os.makedirs("downloads")
    os.makedirs("trimmed")


def download_videos(singer, num_videos):
    print(f"Downloading top {num_videos} videos of {singer}...")

    search_query = f"ytsearch{num_videos}:{singer} official video"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'noplaylist': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_query])


def trim_audios(duration):
    print(f"Trimming first {duration} seconds from each audio...")

    trimmed_files = []

    for file in os.listdir("downloads"):
        if file.endswith(".mp3"):
            file_path = os.path.join("downloads", file)

            try:
                audio = AudioSegment.from_mp3(file_path)
                trimmed_audio = audio[:duration * 1000]

                output_path = os.path.join("trimmed", file)
                trimmed_audio.export(output_path, format="mp3")
                trimmed_files.append(output_path)

            except Exception as e:
                print(f"Skipping file {file}: {e}")

    return trimmed_files


def merge_audios(files, output_file):
    print("Merging audio files...")

    if not files:
        print("Error: No audio files to merge.")
        sys.exit(1)

    final_audio = AudioSegment.empty()

    for file in files:
        audio = AudioSegment.from_mp3(file)
        final_audio += audio

    final_audio.export(output_file, format="mp3")
    print(f"\n✅ Mashup created successfully: {output_file}")


def main():
    try:
        singer, num_videos, duration, output_file = validate_inputs(sys.argv)

        create_directories()
        download_videos(singer, num_videos)
        trimmed_files = trim_audios(duration)
        merge_audios(trimmed_files, output_file)

    except Exception as e:
        print("An unexpected error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
