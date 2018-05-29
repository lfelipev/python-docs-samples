import RPi.GPIO as GPIO
import time
import pyaudio
import wave
import io
import os
import threading
import thread
import datetime

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

#PYAUDIO variables
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "resources/file.wav"

#Buttons variables
GPIO.setmode(GPIO.BCM)

GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

keywords_play = ['toque', 'play', 'teste', 'tocar']
keywords_stop = ['stop', 'pare']

#Global checking variables
isplaying = False
mythread = None

def play_wav(music_name, chunk_size=CHUNK):
    '''
    Play (on the attached system sound device) the WAV file
    named wav_filename.
    '''
    global isplaying
    wav_filename = 'resources/' 

    if ('1' in music_name or 'um' in music_name):
        wav_filename = wav_filename + 'jingle.wav'
    elif ('2' in music_name or 'dois' in music_name):
        wav_filename = wav_filename + 'Coca-Cola.wav'
    elif ('3' in music_name or 'tres' in music_name):
        wav_filename = wav_filename + 'Kazoo.wav'
    elif ('4' in music_name or 'quatro' in music_name):
        wav_filename = wav_filename + 'Roll.wav'
    
    try:
        print 'Trying to play file ' + wav_filename
        wf = wave.open(wav_filename, 'rb')
    except IOError as ioe:
        sys.stderr.write('IOError on file ' + wav_filename + '\n' + \
        str(ioe) + '. Skipping.\n')
        return
    except EOFError as eofe:
        sys.stderr.write('EOFError on file ' + wav_filename + '\n' + \
        str(eofe) + '. Skipping.\n')
        return

    # Instantiate PyAudio.
    p = pyaudio.PyAudio()

    # Open stream.
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk_size)
    while len(data) > 0 and isplaying:
        stream.write(data)
        data = wf.readframes(chunk_size)

    # Stop stream.
    stream.stop_stream()
    stream.close()

    # Close PyAudio.
    p.terminate()

#Stop stream

def play():
    global mythread
    global isplaying
    #Play
    if not(isplaying):
        isplaying = True
        mythread = threading.Thread(target=loopPlay)
        mythread.start()
        
#Stop
def stop():
    global mythread
    global isplaying
    
    #Play
    if (isplaying):
        isplaying = False
        #mythread.join()

def loopPlay():
    while isplaying:
        print('playing audio file')
        play_wav()

# start Recording
def startRecording():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)
    print "recording..."
    frames = []
     
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print "finished recording"
     
     
    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()
     
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

#audio result
def speechToText():
    
    # Instantiates a client
    client = speech.SpeechClient()

    # The name of the audio file to transcribe
    file_name = os.path.join(
        os.path.dirname(__file__),
        'resources',
        'file.wav')

    # Loads the audio into memory
    with io.open(file_name, 'rb') as audio_file:
        print("Loading audio file...")
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code='pt-BR')

    # Detects speech in the audio file
    print("Detecting speech...")
    response = client.recognize(config, audio)

    
    for result in response.results:
        return result.alternatives[0].transcript

def fileLog(message):
    dt = datetime.datetime.now()
    file = open('python-docs-samples/interations.txt','a')
    file.write(message + ' ' + dt.strftime("%Y-%m-%d %H:%M") + '\n')
    file.close()

def buttonThread():
    print("starting button thread")
    while(isplaying):
        input_state = GPIO.input(18)
        if input_state == False:
            startRecording()
            audio_result = speechToText()
            if any(word in audio_result for word in keywords_stop):
                print('Stop accepted!')
                fileLog(audio_result)
                stop()
            else:
                 print('Command not found!!')    
            time.sleep                    

def mainThread():
    global isplaying
    #Button interaction
    print("starting main thread")
    while True:
        input_state = GPIO.input(18)
        if input_state == False:
            print('Listening.....')
            startRecording()
            audio_result = speechToText()
            print(isplaying)
            if not(isplaying):
                if any(word in audio_result for word in keywords_play):
                    print('Play accepted!')
                    fileLog(audio_result)
                    isplaying = True
                    thread.start_new_thread(buttonThread, ())
                    play_wav(audio_result)
                else:
                    print('Command not found!2')
            time.sleep(0.2)

mainThread()
