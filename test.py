#%%
import os
import subprocess
import threading
import time
from io import BytesIO
import elevenlabs
import openai
import speech_recognition as sr

elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))

say_kill_event = threading.Event()
say_thread = None


def stream_until(event, audio_stream):
    mpv_command = ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"]
    mpv_process = subprocess.Popen(
        mpv_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for chunk in audio_stream:
        if event.is_set():
            mpv_process.stdin.close()
            mpv_process.kill()
            return
        if chunk is not None:
            mpv_process.stdin.write(chunk)
            mpv_process.stdin.flush()
        
    if mpv_process.stdin:
        mpv_process.stdin.close()
    mpv_process.wait()


def say_until(event, line):
    audio_stream = elevenlabs.generate(
        text=line,
        # voice="OFU2JdLX0UZAS3ICB8Zk", # Bella
        # voice="aH9BX4BIm9eokHGubnS2", # obama
        voice="76pUPjeLaKX4Nty4Le9d", # indier
        # voice="Bella",
        # model="eleven_monolingual_v1",
        model="eleven_multilingual_v1",
        stream=True
    )

    stream_until(event, audio_stream)


def start_say(line):
    global say_thread
    global say_kill_event

    say_kill_event.clear()
    say_thread = threading.Thread(target=say_until, args=(say_kill_event, line,))
    say_thread.start()


def stop_say():
    global say_thread
    global say_kill_event

    if say_thread is not None:
        say_kill_event.set()
        say_thread.join()


def transcribe_audio(audio_data):
    try:
        wav_data = BytesIO(audio_data.get_wav_data())
        wav_data.name = "SpeechRecognition_audio.wav"

        transcript = openai.Audio.transcribe(
            model="whisper-1", 
            file=wav_data, 
            api_key=os.getenv("OPENAI_API_KEY"), 
            language="sv",
            prompt=None,
            )
        
        text = transcript["text"]

        print(f"User said: {text}")

        if len(text.strip()) > 0:
            add_user_message(text)

        # return transcript
    except sr.UnknownValueError:
        print("Speech was unintelligible")


def add_user_message(message):
    global messages
    messages.append({"role": "user", "content": message})

    text = gpt()
    add_assistant_message(text)
    stop_say()
    start_say(text)


def add_assistant_message(message):
    global messages
    messages.append({"role": "assistant", "content": message})


def gpt():
    global messages

    response = openai.ChatCompletion.create(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1.0,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0
        # max_tokens=256,
    )

    text = response.choices[0].message.content
    return text


def on_phrase_started():
    # print("interrupting")
    stop_say()


messages = [
    {"role": "system", "content": "You are benovelent, nihilistic, and funny. You respond very concisely. If you don't know the answer to a question, you make something up on the spot. You are adept at english and swedish. You respond very concisely."},
    {"role": "user", "content": "Hello"},
]


r = sr.Recognizer()
r.pause_threshold = 0.2
r.energy_threshold = 50
r.non_speaking_duration = 0.1
r.phrase_threshold = 0.1
r.dynamic_energy_threshold = False


def listen_loop():
    global r

    while True:
        with sr.Microphone() as source:
            audio = r.listen(source, on_phrase_started=on_phrase_started)

        threading.Thread(target=transcribe_audio, args=(audio,)).start()


#%%

listen_thread = threading.Thread(target=listen_loop)
listen_thread.start()

# r = gpt()
# add_assistant_message(r)
# wait for user to say something



#%%
elevenlabs.voices()

#%%

for i in range(1):
    r = elevenlabs.generate(
        # text="This is Luva. hehu",
        # text="Hej, det här är obama. Birdie är en jättebra demoparty.",
        # text="This is obama, and I'm here to say, birdie is a great demoparty.",
        # text="concepts snopp. birdie har de! he hüü.",
    #     text="""
    # Klappande händer och hoppande tramp,
    # Bongo styr med sitt demoparty, en färgsprakande svamp.
    # """,
        # text="Välkommen till total avslappning tre punkt noll! Vi är glada över att du har valt att ansluta dig till oss i denna enastående resa mot inre frid och harmoni. Vår metod är speciellt utformad för att hjälpa dig att uppnå djup avslappning och stresslättnad, samtidigt som du ökar din koncentration och mentala klarhet.",
        text="Welcome to extreme relaxation three point o. We be thrilled that you have chosen to join us in this mind-blowing quest towards inner peace and ETERNAL harmony. Our meth is specially designed to help you achieve ultra deep relaxation and INSANE stress relief, while optimizing your concentration and mental wisdom. Someone will be with you soon. Prepare to be amazed. Wow!!??! ... What the fuck??? .. God is dead. God remains dead. And we have killed him. How shall we comfort ourselves, the murderers of all murderers?",
        # voice="OFU2JdLX0UZAS3ICB8Zk", # calle
        voice="aH9BX4BIm9eokHGubnS2", # obama
        # voice="76pUPjeLaKX4Nty4Le9d", # indier
        # voice="Ys6i7yoLCTWVe326Pyq1", # lova 1
        # voice="Y7AaLGVPZxGUiiPmOb3e", # lova 2
        # voice="Bella",
        model="eleven_monolingual_v1",
        # model="eleven_multilingual_v1",
        stream=False
    )
    elevenlabs.play(r)

    elevenlabs.save(r, f"last.wav")