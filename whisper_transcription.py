# Helper unction to download MP3s
def DownloadMP3(url):
    
    
    from bs4 import BeautifulSoup
    import requests
    import urllib.request
    import re
        
    doc = requests.get(url)

    with open('temp.mp3', 'wb') as f:
            f.write(doc.content)

    soup = BeautifulSoup(doc.content, 'html.parser', from_encoding="iso-8859-1")

    for a in soup.find_all('a', href=re.compile(r'http.*\.mp3')):
        filename = a['href'][a['href'].rfind("/")+1:]
        doc = requests.get(a['href'])
        with open(filename, 'wb') as f:
            f.write(doc.content)
    return True

# Helper function to segment MP3 files
# This will temporarily save the files in whatever directory you place this file,
# but they will be overwritten and can be deleted when the function is done running
def SegmentMP3(path = 'temp.mp3'):
    
    """
    Function that takes an MP3 from a filepath and segments it into eight equal pieces
    Assume path is "temp.mp3" unless stated otherwise.
    """
    
    from pydub import AudioSegment

    # Segment the audio - these are long podcasts, so I am splitting into eighths
    sound = AudioSegment.from_mp3(path)

    audio_length = len(sound) # This will give a big number that represents number of total milleseconds
    eighth = audio_length/8
    quarter = audio_length/4
    half = audio_length/2

    E1 = sound[:eighth]
    E2 = sound[eighth:quarter]
    E3 = sound[quarter:quarter+eighth]
    E4 = sound[quarter+eighth:half]
    E5 = sound[half:half+eighth]
    E6 = sound[half+eighth:half+quarter]
    E7 = sound[half+quarter:audio_length-eighth]
    E8 = sound[audio_length-eighth:]

    segments = [E1, E2, E3, E4, E5, E6, E7, E8]
    titles = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', "E7", "E8"]

    # Save the 4 segments as separate MP3s (Q1.mp3, Q2.mp3, and so on) - these will be overwritten continuously to save space

    k = 0
    for segment in segments:  
        segment.export(titles[k] + ".mp3", format="mp3")
        k += 1

    return True

# Helper function to transcribe MP3 segments created by SegmentMP3
def TranscribeMP3():
    
    """
    Funtion that analyzes the segments created by SegmentMP3 and 
    produces a transcript for the entire podcast episode.
    """
    
    # Whisper documentation: https://github.com/openai/whisper
    import whisper
    
    titles = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', "E7", "E8"]
    files = [i + ".mp3" for i in titles]
    
    transcriptions = []
    for i in files:
        model = whisper.load_model("tiny") # using tiny model to save time
        transcript = model.transcribe(i, fp16=False, language = "English")
        transcriptions.append(transcript['text'])


        # Combine the transcribed segments into a single string
    
    transcript = ' '.join(transcriptions)
        
    return transcript
     
    
# Helper function to batch the data into 10 groupings
def DataBatch(urls):
    total = len(urls)
    ten_p = int(total*.1)
    
    batchces = [urls[:ten_p], urls[ten_p:ten_p*2], urls[ten_p*2:ten_p*3], urls[ten_p*3:ten_p*4], urls[ten_p*4:ten_p*5],
                urls[ten_p*5:ten_p*6], urls[ten_p*6:ten_p*7], urls[ten_p*7:ten_p*8], urls[ten_p*8:ten_p*9], urls[ten_p*9:]]
    return batchces


# MAIN FUNCTION - combines the previous 4 helper functions to batch the data and then dowload
# and transcribe en mass. Returns a df with url matched to the transcription.
# ERROR HANDLING - if the function fails mid run, it will return the results that it has
# to that point and tell you which one it failed on.

def MP3Transcribe(urls):
    import pandas as pd
    
    print('Batching the data.', end='\r')
    batches = DataBatch(urls)
 
    """
    A function that transcribes MP3 files from the internet.
    Returns a df containing each url matched to its transcription.
    urls: a list of links to MP3 files
    """
    k = 0
    transcriptions = []
    for batch in batches: # batches make things work better and enable us to "save progress"
        for url in batch:
            try:
                DownloadMP3(url)
                SegmentMP3()
                transcriptions.append(TranscribeMP3())
                k = k+1
                print(str(k) + ' out of ' + str(len(urls)) + ' podcasts transcribed in this batch.', end = '\r')
            
            except:
                print('Function failed transcribing MP3 number ' + str(k) + '. Remaining URLs will have -99 for transcript.')
                for i in range(len(urls)-len(transcriptions)):
                    transcriptions.append(-99)
                df = pd.DataFrame({'url':urls, 'transcription':transcriptions})
                
                return df
                
    df = pd.DataFrame({'url':urls, 'transcription':transcriptions})
    
    return df
    
