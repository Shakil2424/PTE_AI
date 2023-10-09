import base64
import io
import random
import os
from spellchecker import SpellChecker
import language_tool_python
import myprosody as mysp
import string
import requests
from flask import Flask, jsonify, redirect, render_template, url_for, request
import speech_recognition as sr
from nltk.metrics.distance import edit_distance
from pydub import AudioSegment
from werkzeug.exceptions import BadRequestKeyError
from pyngrok import ngrok
import spacy
import string
import nltk
import re
import Levenshtein
import math
import difflib
import wave
from transformers import pipeline
app = Flask(__name__)
from collections import Counter
recognizer = sr.Recognizer()
from pyngrok import ngrok
from flask import Flask, render_template, request
import spacy
from nltk.tokenize import word_tokenize
import nltk
import spacy
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import librosa
import textdescriptives as td
app = Flask(__name__)


# Load necessary models and resources
folder_path="F:/Peter Pte/Peter's PTE AI/All_PTE_Combined"


nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe("textdescriptives/all")
ngrok_url = ""
# def start_ngrok():
#     ngrok_tunnel = ngrok.connect(5000)  # Replace 5000 with your Flask app's port
#     print("Ngrok Tunnel URL:", ngrok_tunnel.public_url)

@app.route('/')
def index():
      return render_template("Read_Aloud.html")
a=False
score = False
content_score = False
total_score=False
fluency_score = False
user_speech = False
reference_text = False
word_highlight = []
speed=False
stress=False
speaking=False
reading=False
reference=False
#-------------------------Read Aloud----------------------------

@app.route('/Read_Aloud', methods=['GET', 'POST'])
def Read_Aloud():
    def evaluate_pronunciation(reference_text, user_speech):
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())


        reference_words = reference_text_clean.split()
        user_speech_words = user_speech_clean.split()


        wer = edit_distance(reference_words, user_speech_words) / len(reference_words)
        pronunciation_score = 1 - wer


        return pronunciation_score * 90

    def word_similarity(word1, word2):
        doc1 = nlp(word1)
        doc2 = nlp(word2)
        return doc1.similarity(doc2)

    def evaluate_content(reference_text, user_speech):
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())
        reference_words = reference_text_clean.split()
        user_speech_words = user_speech_clean.split()
        word_highlight = []
        def lcs(X, Y):
            m = len(X)
            n = len(Y)
            dp = [[0] * (n+1) for _ in range(m+1)]


            for i in range(1, m+1):
                for j in range(1, n+1):
                    if X[i-1] == Y[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])


            lcs_length = dp[m][n]
            lcs_words = []
            i, j = m, n
            while i > 0 and j > 0:
                if X[i-1] == Y[j-1]:
                    lcs_words.insert(0, X[i-1])
                    i -= 1
                    j -= 1
                elif dp[i-1][j] > dp[i][j-1]:
                    i -= 1
                else:
                    j -= 1


            return lcs_words

        # Get the Longest Common Subsequence (LCS) of the two texts
        lcs_words = lcs(reference_words, user_speech_words)

        # Find the error words by comparing LCS words with the reference words
        error_words = []
        i, j = 0, 0
        for word in reference_words:
            if i < len(lcs_words) and word == lcs_words[i]:
                i += 1
                word_highlight.append((word, "correct"))
            else:
                error_words.append(word)
                word_highlight.append((word,"error"))
        for i, (word, status) in enumerate(word_highlight):
            if status == "error":
                found_match = False
                for error_word in user_speech_words:
                    similarity = calculate_word_similarity(word, error_word)
                    if similarity > 0.7:
                        if reference_words.count(error_word) > 1:
                            word_highlight[i] = (word, "missing")
                        else:
                            word_highlight[i] = (word, "mispronounced")
                        found_match = True
                        break
                if not found_match:
                    word_highlight[i] = (word, "missing")
        user_word_counts = Counter(user_speech_words)
        lcs_word_counts = Counter(reference_words)
        # extra_words = [word for word, count in user_word_counts.items() if count > lcs_word_counts[word]]
        extra_words = []


        # Find extra words based on the conditions
        for word, count in user_word_counts.items():
            if count > lcs_word_counts[word]:
                has_similar_mispronounced_word = any(calculate_word_similarity(word, mis_word) > 0.7 for mis_word, status in word_highlight if status == "mispronounced")
                if not has_similar_mispronounced_word:
                    extra_words.extend([word] * (count - lcs_word_counts[word]))

        score = 90

        # Calculate the total number of words in the reference text
        total_reference_words = len(reference_text_clean)
        # Calculate the total number of words in the user speech
        total_user_words = len(user_speech_clean)

        # Calculate the penalty for each missing/extra word based on the total number of words
        penalty_per_word = 90 / total_reference_words

        # Deduct marks for each missing word
        for word, status in word_highlight:
            if status == "missing":
                # Deduct marks based on the total number of words
                word_penalty = penalty_per_word * len(word)
                score -= word_penalty

        # Deduct marks for extra words
        for word in extra_words:
            # Deduct marks based on the total number of words
            word_penalty = penalty_per_word * len(word)
            score -= word_penalty
        return score
    def calculate_word_similarity(word1, word2):
        return difflib.SequenceMatcher(None, word1, word2).ratio()


    def evaluate_fluency(speech,path):
        def count_repetitions(user_speech):
            words = user_speech.split()
            repetitions = 0
            for i in range(len(words) - 1):
                if words[i] == words[i + 1]:
                    repetitions += 1
            return repetitions

        def count_false_starts(user_speech):
            false_starts = 0
            sentences = user_speech.split('.')
            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) > 1 and words[0] == words[1]:
                    false_starts += 1
            return false_starts

        def count_long_pauses(user_speech, pause_threshold=2.0):
            long_pauses = 0
            words = user_speech.split()
            time_between_words = [len(word) / 3.5 for word in words]  # Assuming an average reading speed of 3.5 characters per second
            for i in range(len(words) - 1):
                if time_between_words[i + 1] - time_between_words[i] > pause_threshold:
                    long_pauses += 1
            return long_pauses

        def calculate_speech_rate_score(speech_rate):
            ideal_wps_min = 2.5
            ideal_wps_max = 3.5

            if speech_rate > ideal_wps_min and speech_rate < ideal_wps_max:
                score = 1.0
            elif speech_rate < ideal_wps_min:
                score = max(1.0 - ((ideal_wps_min - speech_rate) / ideal_wps_min), 0.0)
            else:
                score = max(1.0 - ((speech_rate - ideal_wps_max) / (ideal_wps_max)), 0.0)
            return score
        # Measure fluency using various metrics
        repetitions_score = 1.0 - (count_repetitions(speech) * 0.5)  # Adjust fluency based on repetitions
        false_starts_score = 1.0 - (count_false_starts(speech) * 0.5)  # Adjust fluency based on false starts
        long_pauses_score = 1.0 - (count_long_pauses(speech) * 0.5)  # Adjust fluency based on long pauses
        hesitations = speech.count("uh") + speech.count("um")
        disfluencies_score = 1.0 - ((hesitations) * 0.5)  # Adjust fluency based on disfluencies
        # Calculate the speech rate score
        speech_rate = calculate_speech_rate_score(mysp.myspsr(path,folder_path))
        print(repetitions_score)
        print(false_starts_score)
        print(long_pauses_score)
        print(disfluencies_score)
        print(speech_rate)
        # Adjust fluency score based on all the metrics
        final_fluency_score = (
            repetitions_score
            + false_starts_score
            + long_pauses_score
            + disfluencies_score
            + 4 * speech_rate
        ) / 8
        # Normalize the score to a scale of 0 to 90
        fluency_score_normalized = round(final_fluency_score * 90, 2)
        fluency_score_normalized=min(90, fluency_score_normalized)
        return fluency_score_normalized

    def read_aloud_score(reference_text, audio_file_path):
        # Convert audio file to WAV format
        wav_file_path = "converted_audio.wav"
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(wav_file_path, format="wav")
        print(audio_file_path)
        pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
        # Transcribe the audio
        transcription = pipe(audio_file_path)
        user_speech= transcription['text']
        a=user_speech
        #user_speech="the bill calls for the establishment of the national landslide hazard seduction program within one year of becoming law the program serves numerous functions including to identify and understand landslide hazards and risk reduced losses from landslides protect communities at risk of landslide hazards and improve communication and emergency preparedness"
        user_speech = user_speech.lower()
        print("User's speech:", user_speech)
        # Perform language processing to identify incorrect words
        # Amar
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())
        reference_words = reference_text_clean.split()
        user_words = user_speech_clean.split()
        word_highlight = []
        def find_error_words(reference_text, user_speech):
            reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
            user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())
            reference_words = reference_text_clean.split()
            user_speech_words = user_speech_clean.split()
            # Function to find the Longest Common Subsequence (LCS) of two lists
            def lcs(X, Y):
                m = len(X)
                n = len(Y)
                dp = [[0] * (n+1) for _ in range(m+1)]
                for i in range(1, m+1):
                    for j in range(1, n+1):
                        if X[i-1] == Y[j-1]:
                            dp[i][j] = dp[i-1][j-1] + 1
                        else:
                            dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                lcs_length = dp[m][n]
                lcs_words = []
                i, j = m, n
                while i > 0 and j > 0:
                    if X[i-1] == Y[j-1]:
                        lcs_words.insert(0, X[i-1])
                        i -= 1
                        j -= 1
                    elif dp[i-1][j] > dp[i][j-1]:
                        i -= 1
                    else:
                        j -= 1
                return lcs_words
            # Get the Longest Common Subsequence (LCS) of the two texts
            lcs_words = lcs(reference_words, user_speech_words)

            # Find the error words by comparing LCS words with the reference words
            error_words = []
            i, j = 0, 0
            for word in reference_words:
                if i < len(lcs_words) and word == lcs_words[i]:
                    i += 1
                    word_highlight.append((word, "correct"))
                else:
                    error_words.append(word)
                    word_highlight.append((word,"error"))
            for i, (word, status) in enumerate(word_highlight):
                if status == "error":
                    found_match = False
                    for error_word in user_speech_words:
                        similarity = calculate_word_similarity(word, error_word)
                        if similarity > 0.7:
                            if reference_words.count(error_word) > 1:
                                word_highlight[i] = (word, "missing")
                            else:
                                word_highlight[i] = (word, "mispronounced")
                            found_match = True
                            break
                    if not found_match:
                        word_highlight[i] = (word, "missing")
            return word_highlight


        def calculate_word_similarity(word1, word2):
            return difflib.SequenceMatcher(None, word1, word2).ratio()

        highlights = find_error_words(reference_text, user_speech)  
        # audio_path = "converted_audio.wav"
        speech = user_speech
        score = evaluate_pronunciation(reference_text, user_speech)
        score = round(score, 2)
        content_score = evaluate_content(reference_text, user_speech)
        content_score = round(content_score, 2)
        path="converted_audio.wav"
        fluency_score = evaluate_fluency(speech,path)
        # fluency_score = evaluate_fluency(wav_file_path, speech)
        if(fluency_score < 10):
            fluency_score=10
        if(content_score < 10):
            content_score=10
            fluency_score=10
            score=10
        if(score < 10):
            score=10
        total_score= (score+content_score+fluency_score) / 3
        total_score = round(total_score, 2)
        speed=round(((mysp.myspsr(path,folder_path))/2.5) * 100,2)
        if(speed<100):
            speed=speed-100
        print("Speed Score", speed)
        q_25=mysp.myspf0q25(path,folder_path)
        q_75=mysp.myspf0q75(path,folder_path)
        stress_sd=mysp.myspf0sd(path,folder_path)
        print(q_25)
        print(q_75)
        if stress_sd > 15:
            stress_score= round((15 - stress_sd),2)
        else:
            stress_score=100
        speaking=((fluency_score*80)/100)+((score*20)/100)
        reading=((content_score*80)/100)+((score*20)/100)
        print("Pronunciation score:", score)
        print("Content score:", content_score)
        print("Fluency score:", fluency_score)
        print("Speaking score:", speaking)
        print("Reading score:", reading)
        return score, content_score, user_speech, highlights, fluency_score, total_score,speed,stress_score,speaking,reading
    global a,score, content_score, user_speech, reference_text, word_highlight, fluency_score,total_score,speed,stress,speaking,reading
    if request.method == 'POST':
        # handle POST request here
        # reference_text = request.json['reference_text']
        # print(reference_text)
        audio = request.files['audio']

        if audio:
            audio_folder = os.path.join(app.root_path, 'audio')
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)
            # save the audio file to the 'audio' folder
            audio_path = os.path.join(audio_folder, audio.filename)
            audio.save(audio_path)
            # audio_path="I85.wav"
           # Evaluate pronunciation similarity
            reference_text = request.form.get('reference')
            #reference_text="An innovative new product or service can give a firm a head start over its rivals, which can be difficult for a new entrant to overcome. If the new technology is also patented, then other firms cannot simply copy its design. It is legally protected."
            score, content_score, user_speech, word_highlight, fluency_score,total_score,speed,stress,speaking,reading = read_aloud_score(reference_text, audio_path)
            a=True
        return render_template('score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,total_score=total_score, speed=speed,stress=stress,speaking=speaking,reading=reading)
    elif request.method == 'GET':
            if a is False:
                return render_template("Read_Aloud.html")
            else:
                a=False
                return render_template('score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,total_score=total_score, speed=speed,stress=stress,speaking=speaking,reading=reading)

#-------------------------Repeat Sentence----------------------------

@app.route('/Repeat_Sentence', methods=['GET', 'POST'])
def Repeat_Sentence():
    def evaluate_pronunciation(reference_text, user_speech):

        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())


        reference_words = reference_text_clean.split()
        user_speech_words = user_speech_clean.split()


        wer = edit_distance(reference_words, user_speech_words) / len(reference_words)
        pronunciation_score = 1 - wer


        return pronunciation_score * 90
    def word_similarity(word1, word2):
        doc1 = nlp(word1)
        doc2 = nlp(word2)
        return doc1.similarity(doc2)


    def evaluate_content(reference_text, user_speech):
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())
        reference_words = reference_text_clean.split()
        user_speech_words = user_speech_clean.split()
        word_highlight = []
        # def find_error_words(reference_text, user_speech):
        # reference_words = reference_text
        # user_speech_words = user_speech
        # Function to find the Longest Common Subsequence (LCS) of two lists
        def lcs(X, Y):
            m = len(X)
            n = len(Y)
            dp = [[0] * (n+1) for _ in range(m+1)]


            for i in range(1, m+1):
                for j in range(1, n+1):
                    if X[i-1] == Y[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])


            lcs_length = dp[m][n]
            lcs_words = []
            i, j = m, n
            while i > 0 and j > 0:
                if X[i-1] == Y[j-1]:
                    lcs_words.insert(0, X[i-1])
                    i -= 1
                    j -= 1
                elif dp[i-1][j] > dp[i][j-1]:
                    i -= 1
                else:
                    j -= 1
            return lcs_words

        # Get the Longest Common Subsequence (LCS) of the two texts
        lcs_words = lcs(reference_words, user_speech_words)


        # Find the error words by comparing LCS words with the reference words
        error_words = []
        i, j = 0, 0
        for word in reference_words:
            if i < len(lcs_words) and word == lcs_words[i]:
                i += 1
                word_highlight.append((word, "correct"))
            else:
                error_words.append(word)
                word_highlight.append((word,"error"))
        for i, (word, status) in enumerate(word_highlight):
            if status == "error":
                found_match = False
                for error_word in user_speech_words:
                    similarity = calculate_word_similarity(word, error_word)
                    if similarity > 0.7:
                        if reference_words.count(error_word) > 1:
                            word_highlight[i] = (word, "missing")
                        else:
                            word_highlight[i] = (word, "mispronounced")
                        found_match = True
                        break
                if not found_match:
                    word_highlight[i] = (word, "missing")
        user_word_counts = Counter(user_speech_words)
        lcs_word_counts = Counter(reference_words)
        # extra_words = [word for word, count in user_word_counts.items() if count > lcs_word_counts[word]]
        extra_words = []

        # Find extra words based on the conditions
        for word, count in user_word_counts.items():
            if count > lcs_word_counts[word]:
                has_similar_mispronounced_word = any(calculate_word_similarity(word, mis_word) > 0.7 for mis_word, status in word_highlight if status == "mispronounced")
                if not has_similar_mispronounced_word:
                    extra_words.extend([word] * (count - lcs_word_counts[word]))

        score = 90
        # Calculate the total number of words in the reference text
        total_reference_words = len(reference_text_clean)
        # Calculate the total number of words in the user speech
        total_user_words = len(user_speech_clean)


        # Calculate the penalty for each missing/extra word based on the total number of words
        penalty_per_word = 90 / total_reference_words


        # Deduct marks for each missing word
        for word, status in word_highlight:
            if status == "missing":
                # Deduct marks based on the total number of words
                word_penalty = penalty_per_word * len(word)
                score -= word_penalty


        # Deduct marks for extra words
        for word in extra_words:
            # Deduct marks based on the total number of words
            word_penalty = penalty_per_word * len(word)
            score -= word_penalty
        return score
    def calculate_word_similarity(word1, word2):
        return difflib.SequenceMatcher(None, word1, word2).ratio()


    def evaluate_fluency(speech,path):
        def count_repetitions(user_speech):
            words = user_speech.split()
            repetitions = 0


            for i in range(len(words) - 1):
                if words[i] == words[i + 1]:
                    repetitions += 1


            return repetitions

        def count_false_starts(user_speech):
            false_starts = 0
            sentences = user_speech.split('.')


            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) > 1 and words[0] == words[1]:
                    false_starts += 1


            return false_starts

        def count_long_pauses(user_speech, pause_threshold=2.0):
            long_pauses = 0
            words = user_speech.split()
            time_between_words = [len(word) / 3.5 for word in words]  # Assuming an average reading speed of 3.5 characters per second


            for i in range(len(words) - 1):
                if time_between_words[i + 1] - time_between_words[i] > pause_threshold:
                    long_pauses += 1


            return long_pauses

        def calculate_speech_rate_score(speech_rate):
            ideal_wps_min = 2.75
            ideal_wps_max = 2.95

            if speech_rate > ideal_wps_min and speech_rate < ideal_wps_max:
                score = 1.0
            elif speech_rate < ideal_wps_min:
                score = max(1.0 - ((ideal_wps_min - speech_rate) / ideal_wps_min), 0.0)
            else:
                score = max(1.0 - ((speech_rate - ideal_wps_max) / (ideal_wps_max)), 0.0)


            return score
        # Measure fluency using various metrics
        repetitions_score = 1.0 - (count_repetitions(speech) * 0.5)  # Adjust fluency based on repetitions
        false_starts_score = 1.0 - (count_false_starts(speech) * 0.5)  # Adjust fluency based on false starts
        long_pauses_score = 1.0 - (count_long_pauses(speech) * 0.5)  # Adjust fluency based on long pauses
        hesitations = speech.count("uh") + speech.count("um")
        disfluencies_score = 1.0 - ((hesitations) * 0.5)  # Adjust fluency based on disfluencies


        # Calculate the speech rate score
        speech_rate = calculate_speech_rate_score(mysp.myspsr(path,folder_path))
        print(repetitions_score)
        print(false_starts_score)
        print(long_pauses_score)
        print(disfluencies_score)
        print(speech_rate)
        # Adjust fluency score based on all the metrics
        final_fluency_score = (
            repetitions_score
            + false_starts_score
            + long_pauses_score
            + disfluencies_score
            + 4 * speech_rate
        ) / 8

        # Normalize the score to a scale of 0 to 90
        fluency_score_normalized = round(final_fluency_score * 90, 2)
        fluency_score_normalized=min(90, fluency_score_normalized)
        return fluency_score_normalized

    def repeat_sentence_score(reference_text, audio_file_path):
        # Convert audio file to WAV format
        wav_file_path = "converted_audio.wav"
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(wav_file_path, format="wav")
        print(audio_file_path)
        pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
        # Transcribe the audio
        transcription = pipe(audio_file_path)
        user_speech= transcription['text']
        a=user_speech
        #user_speech="the bill calls for the establishment of the national landslide hazard seduction program within one year of becoming law the program serves numerous functions including to identify and understand landslide hazards and risk reduced losses from landslides protect communities at risk of landslide hazards and improve communication and emergency preparedness"
        user_speech = user_speech.lower()
        print("User's speech:", user_speech)
        # Perform language processing to identify incorrect words
        # Amar
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())


        reference_words = reference_text_clean.split()
        user_words = user_speech_clean.split()


        word_highlight = []
        def find_error_words(reference_text, user_speech):
            reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
            user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())


            reference_words = reference_text_clean.split()
            user_speech_words = user_speech_clean.split()


            # Function to find the Longest Common Subsequence (LCS) of two lists
            def lcs(X, Y):
                m = len(X)
                n = len(Y)
                dp = [[0] * (n+1) for _ in range(m+1)]


                for i in range(1, m+1):
                    for j in range(1, n+1):
                        if X[i-1] == Y[j-1]:
                            dp[i][j] = dp[i-1][j-1] + 1
                        else:
                            dp[i][j] = max(dp[i-1][j], dp[i][j-1])


                lcs_length = dp[m][n]
                lcs_words = []
                i, j = m, n
                while i > 0 and j > 0:
                    if X[i-1] == Y[j-1]:
                        lcs_words.insert(0, X[i-1])
                        i -= 1
                        j -= 1
                    elif dp[i-1][j] > dp[i][j-1]:
                        i -= 1
                    else:
                        j -= 1


                return lcs_words


            # Get the Longest Common Subsequence (LCS) of the two texts
            lcs_words = lcs(reference_words, user_speech_words)


            # Find the error words by comparing LCS words with the reference words
            error_words = []
            i, j = 0, 0
            for word in reference_words:
                if i < len(lcs_words) and word == lcs_words[i]:
                    i += 1
                    word_highlight.append((word, "correct"))
                else:
                    error_words.append(word)
                    word_highlight.append((word,"error"))
            for i, (word, status) in enumerate(word_highlight):
                if status == "error":
                    found_match = False
                    for error_word in user_speech_words:
                        similarity = calculate_word_similarity(word, error_word)
                        if similarity > 0.7:
                            if reference_words.count(error_word) > 1:
                                word_highlight[i] = (word, "missing")
                            else:
                                word_highlight[i] = (word, "mispronounced")
                            found_match = True
                            break
                    if not found_match:
                        word_highlight[i] = (word, "missing")
            return word_highlight


        def calculate_word_similarity(word1, word2):
            return difflib.SequenceMatcher(None, word1, word2).ratio()


        def first_2_sec(wav_file_path):
            # Load the WAV file
            audio = sr.AudioFile(wav_file_path)

            with audio as source:
                # Record the first 2 seconds of audio
                audio_data = recognizer.record(source, duration=1)

            # Use a speech recognition engine to transcribe the audio
            try:
                text = recognizer.recognize_google(audio_data)
                return len(text.strip()) > 0  # Check if there's recognized text
            except sr.UnknownValueError:
                return False  # No speech detected
            except sr.RequestError:
                print("Could not request results. Check your internet connection.")
                return False

        highlights = find_error_words(reference_text, user_speech)  
        # audio_path = "converted_audio.wav"
        speech = user_speech
        score = evaluate_pronunciation(reference_text, user_speech)
        score = round(score, 2)
        content_score = evaluate_content(reference_text, user_speech)
        content_score = round(content_score, 2)
        path="converted_audio.wav"
        fluency_score = evaluate_fluency(speech,path)
        # fluency_score = evaluate_fluency(wav_file_path, speech)
        if(fluency_score < 10):
            fluency_score=10
        if(content_score < 10):
            content_score=10
            fluency_score=10
            score=10
        if(score < 10):
            score=10
        speaking= (score+content_score+fluency_score) / 3
        reading=(score+content_score) / 2
        speaking = round(speaking, 2)
        reading = round(reading, 2)
        if(first_2_sec(wav_file_path)):
            speaking=speaking
            reading=reading
        else:
            speaking=speaking-30
            reading=reading-30
        print("Pronunciation score:", score)
        print("Content score:", content_score)
        print("Fluency score:", fluency_score)
        return score, content_score, user_speech, highlights, fluency_score, speaking,reading
    global a,score, content_score, user_speech, reference_text, word_highlight, fluency_score,speaking,reading
    if request.method == 'POST':
        # handle POST request here
        # reference_text = request.json['reference_text']
        # print(reference_text)
        audio = request.files['audio']
        if audio:
            audio_folder = os.path.join(app.root_path, 'audio')
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)
            # save the audio file to the 'audio' folder
            audio_path = os.path.join(audio_folder, audio.filename)
            audio.save(audio_path)
            # audio_path="I85.wav"
           # Evaluate pronunciation similarity
            pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
            # Transcribe the audio
            transcription = pipe("static/repeat.mp3")
            reference_text= transcription['text']
            print(reference_text)
            #reference_text="An innovative new product or service can give a firm a head start over its rivals, which can be difficult for a new entrant to overcome. If the new technology is also patented, then other firms cannot simply copy its design. It is legally protected."
            score, content_score, user_speech, word_highlight, fluency_score,speaking,reading= repeat_sentence_score(reference_text, audio_path)
            a=True
        return render_template('repeat_score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,speaking=speaking,reading=reading)
    elif request.method == 'GET':
                if a is False:
                    print("here")
                    return render_template("Repeat_Sentence.html")
                else:
                    a=False
                    return render_template('repeat_score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,speaking=speaking,reading=reading)

#-------------------------Retell Lecture----------------------------

@app.route('/Retell_Lecture', methods=['GET', 'POST'])
def Retell_Lecture():
    def word_similarity(word1, word2):
        doc1 = nlp(word1)
        doc2 = nlp(word2)
        return doc1.similarity(doc2)


    def evaluate_content(reference_text, user_speech):
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())
        doc_summary = nlp(user_speech_clean)
        doc_reference = nlp(reference_text_clean)
        content_score = doc_summary.similarity(doc_reference) * 90  # Scaling the similarity score to range 0-2
        if(content_score>85):
            content_score=90
        else:
            content_score=content_score+5
        return content_score


    def evaluate_fluency(speech,path):
        def count_repetitions(user_speech):
            words = user_speech.split()
            repetitions = 0


            for i in range(len(words) - 1):
                if words[i] == words[i + 1]:
                    repetitions += 1


            return repetitions

        def count_false_starts(user_speech):
            false_starts = 0
            sentences = user_speech.split('.')


            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) > 1 and words[0] == words[1]:
                    false_starts += 1


            return false_starts

        def count_long_pauses(user_speech, pause_threshold=2.0):
            long_pauses = 0
            words = user_speech.split()
            time_between_words = [len(word) / 3.5 for word in words]  # Assuming an average reading speed of 3.5 characters per second


            for i in range(len(words) - 1):
                if time_between_words[i + 1] - time_between_words[i] > pause_threshold:
                    long_pauses += 1


            return long_pauses

        def calculate_speech_rate_score(speech_rate):
            ideal_wps_min = 2.5
            ideal_wps_max = 3.5

            if speech_rate > ideal_wps_min and speech_rate < ideal_wps_max:
                score = 1.0
            elif speech_rate < ideal_wps_min:
                score = max(1.0 - ((ideal_wps_min - speech_rate) / ideal_wps_min), 0.0)
            else:
                score = max(1.0 - ((speech_rate - ideal_wps_max) / (ideal_wps_max)), 0.0)


            return score
        # Measure fluency using various metrics
        repetitions_score = 1.0 - (count_repetitions(speech) * 0.5)  # Adjust fluency based on repetitions
        false_starts_score = 1.0 - (count_false_starts(speech) * 0.5)  # Adjust fluency based on false starts
        long_pauses_score = 1.0 - (count_long_pauses(speech) * 0.5)  # Adjust fluency based on long pauses
        hesitations = speech.count("uh") + speech.count("um")
        disfluencies_score = 1.0 - ((hesitations) * 0.5)  # Adjust fluency based on disfluencies


        # Calculate the speech rate score
        speech_rate = calculate_speech_rate_score(mysp.myspsr(path,folder_path))
        print(repetitions_score)
        print(false_starts_score)
        print(long_pauses_score)
        print(disfluencies_score)
        print(speech_rate)
        # Adjust fluency score based on all the metrics
        final_fluency_score = (
            repetitions_score
            + false_starts_score
            + long_pauses_score
            + disfluencies_score
            + 4 * speech_rate
        ) / 8

        # Normalize the score to a scale of 0 to 90
        fluency_score_normalized = round(final_fluency_score * 90, 2)
        fluency_score_normalized=min(90, fluency_score_normalized)
        return fluency_score_normalized

    def retell_lecture_score(reference_text, audio_file_path):
           # Convert audio file to WAV format
        wav_file_path = "converted_audio.wav"
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(wav_file_path, format="wav")
        print(audio_file_path)
        pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
        # Transcribe the audio
        transcription = pipe(wav_file_path)
        user_speech= transcription['text']
        print(user_speech)
        path="converted_audio.wav"  
        score = (mysp.mysppron(path,folder_path)*90)/100
        score = round(score, 2)
        content_score = evaluate_content(reference_text, user_speech)
        content_score = round(content_score, 2)
        fluency_score = evaluate_fluency(user_speech,path)
        # fluency_score = evaluate_fluency(wav_file_path, speech)
        if(content_score < 50):
            score=score-30
            fluency_score=fluency_score-30
        if(fluency_score < 10):
            fluency_score=10
        if(content_score < 10):
            content_score=10
            fluency_score=10
            score=10
        if(score < 10):
            score=10        
        total_score= (score+content_score+fluency_score) / 3
        total_score = round(total_score, 2)
        print("Pronunciation score:", score)
        print("Content score:", content_score)
        print("Fluency score:", fluency_score)
        return score, content_score, fluency_score, total_score
    global a,score, content_score, user_speech, reference_text, word_highlight, fluency_score,total_score
    if request.method == 'POST':
        # handle POST request here
        # reference_text = request.json['reference_text']
        # print(reference_text)
        audio = request.files['audio']
        if audio:
            audio_folder = os.path.join(app.root_path, 'audio')
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)
            # save the audio file to the 'audio' folder
            audio_path = os.path.join(audio_folder, audio.filename)
            audio.save(audio_path)
            # audio_path="I85.wav"
           # Evaluate pronunciation similarity
            reference_text = "There is a picture, sort of artist's impression, before the space age of what Venus might be like on its surface and so this was looking at the planet Venus, it was science fiction and science fact all the way up to 56 before the start of the space age but it wasn't completely disproved, this idea of a really sort of lush environment on Venus until 1967, which is when the first measurements in detail were done at Venus.So Mariner 4 and Mariner 5 confirmed the feeling from an earlier space mission that in fact the surface of Venus was not like this at all, but extremely hot and, and also that the clouds were made of sulfuric acid so there wasn't a nice water cycle like is going on in this picture and so, that it had to wait for these in situ measurements by spacecraft to actually do that and so Venus turned out not to be quite as Earth like as we thought and I'll sort of tell you about some of the latest results from Venus Express, which, which they actually there are some Earth like features, but to a large extent, it's not like the Earth. Okay, so a brief comparison between."
            #reference_text="An innovative new product or service can give a firm a head start over its rivals, which can be difficult for a new entrant to overcome. If the new technology is also patented, then other firms cannot simply copy its design. It is legally protected."
            score, content_score, fluency_score,total_score = retell_lecture_score(reference_text, audio_path)
            a=True
        return render_template('retell_describe_score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,total_score=total_score)
    elif request.method == 'GET':
                if a is False:
                    print("here")
                    return render_template("Retell_Lecture.html")
                else:
                    a=False
                    return render_template('retell_describe_score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,total_score=total_score)

#-------------------------Describe Image----------------------------

@app.route('/Describe_Image', methods=['GET', 'POST'])
def Describe_Image():
    def evaluate_content(reference_text, user_sentence):
        # Convert the user's sentence to lowercase for case-insensitive matching
        user_sentence = user_sentence.lower()
        
        # Split the user's sentence into words
        words = user_sentence.split()
        
        # Count the number of keywords found in the sentence
        keyword_count = sum(1 for word in words if word in reference_text)
        
        # Calculate the score as a percentage
        score = (keyword_count / (len(reference_text)-5)) * 90
        
        return score


    def evaluate_fluency(speech,path):
        def count_repetitions(user_speech):
            words = user_speech.split()
            repetitions = 0


            for i in range(len(words) - 1):
                if words[i] == words[i + 1]:
                    repetitions += 1


            return repetitions

        def count_false_starts(user_speech):
            false_starts = 0
            sentences = user_speech.split('.')


            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) > 1 and words[0] == words[1]:
                    false_starts += 1


            return false_starts

        def count_long_pauses(user_speech, pause_threshold=2.0):
            long_pauses = 0
            words = user_speech.split()
            time_between_words = [len(word) / 3.5 for word in words]  # Assuming an average reading speed of 3.5 characters per second


            for i in range(len(words) - 1):
                if time_between_words[i + 1] - time_between_words[i] > pause_threshold:
                    long_pauses += 1


            return long_pauses

        def calculate_speech_rate_score(speech_rate):
            ideal_wps_min = 2.5
            ideal_wps_max = 3.5

            if speech_rate > ideal_wps_min and speech_rate < ideal_wps_max:
                score = 1.0
            elif speech_rate < ideal_wps_min:
                score = max(1.0 - ((ideal_wps_min - speech_rate) / ideal_wps_min), 0.0)
            else:
                score = max(1.0 - ((speech_rate - ideal_wps_max) / (ideal_wps_max)), 0.0)


            return score
        # Measure fluency using various metrics
        repetitions_score = 1.0 - (count_repetitions(speech) * 0.5)  # Adjust fluency based on repetitions
        false_starts_score = 1.0 - (count_false_starts(speech) * 0.5)  # Adjust fluency based on false starts
        long_pauses_score = 1.0 - (count_long_pauses(speech) * 0.5)  # Adjust fluency based on long pauses
        hesitations = speech.count("uh") + speech.count("um")
        disfluencies_score = 1.0 - ((hesitations) * 0.5)  # Adjust fluency based on disfluencies


        # Calculate the speech rate score
        speech_rate = calculate_speech_rate_score(mysp.myspsr(path,folder_path))
        print(repetitions_score)
        print(false_starts_score)
        print(long_pauses_score)
        print(disfluencies_score)
        print(speech_rate)
        # Adjust fluency score based on all the metrics
        final_fluency_score = (
            repetitions_score
            + false_starts_score
            + long_pauses_score
            + disfluencies_score
            + 4 * speech_rate
        ) / 8

        # Normalize the score to a scale of 0 to 90
        fluency_score_normalized = round(final_fluency_score * 90, 2)
        fluency_score_normalized=min(90, fluency_score_normalized)
        return fluency_score_normalized

    def describe_image_score(reference_text, audio_file_path):
        # Convert audio file to WAV format
    # Convert audio file to WAV format
        wav_file_path = "converted_audio.wav"
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(wav_file_path, format="wav")
        print(audio_file_path)
        pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
        # Transcribe the audio
        transcription = pipe(wav_file_path)
        user_speech= transcription['text']
        path="converted_audio.wav"
        score = (mysp.mysppron(path,folder_path)*90)/100
        score = round(score, 2)
        content_score = evaluate_content(reference_text, user_speech)
        content_score = round(content_score, 2)
        fluency_score = evaluate_fluency(user_speech,path)
        if(fluency_score < 10):
            fluency_score=10
        if(content_score < 10):
            content_score=10
            fluency_score=10
            score=10
        if(score < 10):
            score=10        
        # fluency_score = evaluate_fluency(wav_file_path, speech)
        total_score= (score+content_score+fluency_score) / 3
        total_score = round(total_score, 2)
        print("Pronunciation score:", score)
        print("Content score:", content_score)
        print("Fluency score:", fluency_score)
        return score, content_score, fluency_score, total_score
    global a,score, content_score, user_speech, reference_text, word_highlight, fluency_score,total_score
    if request.method == 'POST':
        # handle POST request here
        # reference_text = request.json['reference_text']
        # print(reference_text)
        audio = request.files['audio']


        if audio:
            audio_folder = os.path.join(app.root_path, 'audio')
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)
            # save the audio file to the 'audio' folder
            audio_path = os.path.join(audio_folder, audio.filename)
            audio.save(audio_path)
            # audio_path="I85.wav"
           # Evaluate pronunciation similarity
            reference_text = {"supply", "chain", "management", "picture", "figure", "five", "key", "steps", "conclusion", "impact", "result", "component", "manufacturer", "retailer", "consumer"}
            # reference_text = "This is a diagram showing the different components of a supply chain. It includes raw materials, management, components, manufacturers, supermarkets, retailers, and consumers. The image also contains text and has a graphic design."
            #reference_text="An innovative new product or service can give a firm a head start over its rivals, which can be difficult for a new entrant to overcome. If the new technology is also patented, then other firms cannot simply copy its design. It is legally protected."
            score, content_score, fluency_score,total_score = describe_image_score(reference_text, audio_path)
            a=True
        return render_template('retell_describe_score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,total_score=total_score)
    elif request.method == 'GET':
                if a is False:
                    print("here")
                    return render_template("Describe_Image.html")
                else:
                    a=False
                    return render_template('retell_describe_score.html', score=score, content_score=content_score, user_speech=user_speech, reference_text=reference_text, word_highlight=word_highlight, fluency_score=fluency_score,total_score=total_score)


#-------------------------Short Answer----------------------------

@app.route('/Short_Answer', methods=['GET', 'POST'])
def Short_Answer():
    def evaluate_content(reference_text, user_speech):
        reference_text_clean = re.sub(r'[^\w\s]', '', reference_text.lower())
        user_speech_clean = re.sub(r'[^\w\s]', '', user_speech.lower())
        # reference_words = reference_text_clean.split()
        # user_speech_words = user_speech_clean.split()
            # Compare the summary and reference for content relevance
        # Measure the similarity of the summary and reference using spaCy
        doc_summary = nlp(user_speech_clean)
        doc_reference = nlp(reference_text_clean)
        content_score = doc_summary.similarity(doc_reference)  # Scaling the similarity score to range 0-2
        if content_score > 0.9:
            content_score=1
        else:
            content_score=0
        return content_score
        
    def short_answer_score(reference_text, audio_file_path):
        # Convert audio file to WAV format
        wav_file_path = "converted_audio.wav"
        audio = AudioSegment.from_file(audio_file_path)
        audio.export(wav_file_path, format="wav")
        print(audio_file_path)
        pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
        # Transcribe the audio
        transcription = pipe(wav_file_path)
        user_speech= transcription['text']
        a=user_speech
        print("---------------------"+a+"--------------------")
        #user_speech="the bill calls for the establishment of the national landslide hazard seduction program within one year of becoming law the program serves numerous functions including to identify and understand landslide hazards and risk reduced losses from landslides protect communities at risk of landslide hazards and improve communication and emergency preparedness"
        user_speech = user_speech.lower()
        print("User's speech:", user_speech)
        # Perform language processing to identify incorrect words
        # Amar
        content_score = evaluate_content(reference_text, user_speech)
        content_score = round(content_score, 2)
        print("Content score:", content_score)
        return content_score

    global a,score, content_score, user_speech, reference_text, word_highlight, fluency_score,total_score
    if request.method == 'POST':
        # handle POST request here
        # reference_text = request.json['reference_text']
        # print(reference_text)
        audio = request.files['audio']

        if audio:
            audio_folder = os.path.join(app.root_path, 'audio')
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)
            # save the audio file to the 'audio' folder
            audio_path = os.path.join(audio_folder, audio.filename)
            audio.save(audio_path)
            # audio_path="I85.wav"
            # pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
            # # Transcribe the audio
            # transcription = pipe("templates/Darwin.mp3")
            # reference = transcription['text']
           # Evaluate pronunciation similarity
            reference_text = "Poverty"
            #reference_text="An innovative new product or service can give a firm a head start over its rivals, which can be difficult for a new entrant to overcome. If the new technology is also patented, then other firms cannot simply copy its design. It is legally protected."
            content_score= short_answer_score(reference_text, audio_path)
            a=True
        return render_template('short_score.html', content_score=content_score)
    elif request.method == 'GET':
                if a is False:
                    print("here")
                    return render_template("Short_Answer.html")
                else:
                    a=False
                    return render_template('short_score.html', content_score=content_score)


#-------------------------Summarize Text----------------------------

@app.route('/Summarize_Text', methods=['GET', 'POST'])
def Summarize_Text():
    def score_summary(summary, reference):
        # Split the summary into sentences
        sentences = nltk.tokenize.sent_tokenize(summary)

        if len(sentences) > 1:
            # If there are multiple sentences, calculate only the Content score
            content_score = calculate_content_score(summary, reference)

            # Return individual scores and overall score
            scores = {
                'Content': content_score,
                'Form': 0,
                'Grammar': 0,
                'Vocabulary': 0,
                'Overall': content_score
            }
        else:
            # If there is only one sentence, calculate scores for all factors
            content_score = round(calculate_content_score(summary, reference),2)
            form_score = calculate_form_score(summary)
            grammar_score = calculate_grammar_score(summary)
            vocabulary_score = calculate_vocabulary_score(summary)

            # Calculate overall score
            if form_score > 0:

                overall_score = (content_score + form_score + grammar_score + vocabulary_score)
            else:
                grammar_score=0
                vocabulary_score=0
                overall_score = (content_score + form_score + grammar_score + vocabulary_score)

            # Return individual scores and overall score
            scores = {
                'Content': content_score,
                'Form': form_score,
                'Grammar': grammar_score,
                'Vocabulary': vocabulary_score,
                'Overall': overall_score
            }

        return scores

    # Example scoring functions

    def calculate_content_score(summary, reference):
        # Compare the summary and reference for content relevance
        # Measure the similarity of the summary and reference using spaCy
        doc_summary = nlp(summary)
        doc_reference = nlp(reference)
        content_score = doc_summary.similarity(doc_reference) * 2  # Scaling the similarity score to range 0-2
        summary_length = len(word_tokenize(summary))
        if summary_length < 6 or summary_length > 74:
            content_score=0
        elif summary_length >5 and summary_length < 50:
            content_score= max(content_score-1,0)
        return content_score

    def calculate_form_score(summary):
        # Check if the summary is in all uppercase
        if summary.isupper():
            return 0
        if summary.count(".") > 1:
            return 0
        # Evaluate the form and structure of the summary
        # Score based on the length of the summary
        summary_length = len(word_tokenize(summary))
        if summary_length >= 5 and summary_length <= 74:
            form_score = 1
        # elif summary_length < 50 and summary_length > 5:
        #     # Calculate partial marks based on proximity to 50
        #     form_score = summary_length / 50
        else:
            form_score = 0

        return form_score


    def calculate_grammar_score(summary):
        tool = language_tool_python.LanguageTool('en-US')  # Specify the language (e.g., 'en-US' for American English)

        matches = tool.check(summary)
        for match in matches:
            print(match.replacements)
        print(len(matches))
        score=max(0,2-len(matches))
        return score

    def calculate_vocabulary_score(summary):
        # Evaluate the vocabulary usage and richness of the summary
        # Score based on the number of unique words in the summary
        unique_words = set(word_tokenize(summary))
        vocabulary_score = len(unique_words) / 5  # Scaling the unique word count to range 0-2
        vocabulary_score = min(2, vocabulary_score)  # Cap the score at 2
        return vocabulary_score
    reference = '''
    If women are so far ahead of men, why are they so far behind? Reports from both sides of the Atlantic show that female students dominate university courses, yet women still do not make it to the top. A report on inequality in the UK said last week that girls had better educational results than boys at 16, went to university in greater numbers and achieved better degrees once they got there. "More women now have higher education qualifications than men in every age group up to age 44," the report said. \n

    In the US, 57 per cent of college graduates in 2006-07 were women. Women form the majority of all graduates under 45. Yet few women make it to the boards of companies in either country. In the UK, the proportion of women on FTSE 100 boards rose fractionally from 11.7 per cent to 12.2 per cent last year, according to the Cranfield University School of Management, but that was only because of a fall in the size of the boards.

    In the US, women accounted for 15.2 per cent of board seats on Fortune 500 companies, according to Catalyst, the research organization, which said the numbers had barely budged for five years. The hopeful way of looking at this is that the rising generation of female graduates has yet to reach director age. Give it 10 years and they will dominate boards as they do universities. If that were true, however, we would surely see the number of women director numbers moving up by now. The first year that women college graduates outnumbered men in the US was 1982. These graduates must be entering their 50s – prime director age.
    '''

    summary = request.args.get('summary', '')
    scores = score_summary(summary, reference) if summary else None
    return render_template('Summarize_Text.html', passage=reference, summary=summary, scores=scores)


#-------------------------Write Essay----------------------------
@app.route('/Write_Essay', methods=['GET', 'POST'])
def Write_Essay():
    def score_summary(summary, reference):
        # If there is only one sentence, calculate scores for all factors
        content_score = calculate_content_score(summary, reference)
        form_score = calculate_form_score(summary)
        grammar_score = calculate_grammar_score(summary)
        vocabulary_score = calculate_vocabulary_score(summary)
        spelling_score=calculate_spelling_score(summary)
        linguistic_score=calculate_linguistic_score(summary)
        structure_score=count_paragraphs(summary)
        # Calculate overall score
        if form_score == 2:
            overall_score = (content_score + form_score + grammar_score + vocabulary_score + spelling_score + linguistic_score + structure_score)
        else:
            content_score=content_score/2
            grammar_score=grammar_score/2
            vocabulary_score=vocabulary_score/2
            spelling_score=spelling_score/2
            linguistic_score=linguistic_score/2
            structure_score=structure_score/2
            overall_score = (content_score + form_score + grammar_score + vocabulary_score + spelling_score + linguistic_score + structure_score)

        # Return individual scores and overall score
        scores = {
            'Content': content_score,
            'Form': form_score,
            'Grammar': grammar_score,
            'Vocabulary': vocabulary_score,
            'Spelling': spelling_score,
            'Linguistic': linguistic_score,
            'Structure': structure_score,
            'Overall': overall_score
        }

        return scores

    # Example scoring functions

    def calculate_content_score(summary, reference):
        # Compare the summary and reference for content relevance
        # Measure the similarity of the summary and reference using spaCy
        doc_summary = nlp(summary)
        doc_reference = nlp(reference)
        content_score = doc_summary.similarity(doc_reference) * 3  # Scaling the similarity score to range 0-2
        return round(content_score,2)

    def calculate_form_score(summary):
        # Check if the summary is in all uppercase
        if summary.isupper():
            return 0

        # Evaluate the form and structure of the summary
        # Score based on the length of the summary
        summary = re.sub(r'[^\w\s]', '', summary.lower())
        summary_length = len(word_tokenize(summary))
        print("Summary Length")
        print(summary_length)
        if summary_length >= 200 and summary_length <= 300:
            form_score = 2
            return form_score
        # elif summary_length < 50 and summary_length > 5:
        #     # Calculate partial marks based on proximity to 50
        #     form_score = summary_length / 50
        elif summary_length >= 120 and summary_length <= 199:
            form_score = 1
            return form_score
        elif summary_length >= 301 and summary_length <= 380:    
            form_score = 1
            return form_score
        else:
            form_score=0
            return form_score


    def calculate_grammar_score(summary):
        tool = language_tool_python.LanguageTool('en-US')  # Specify the language (e.g., 'en-US' for American English)

        matches = tool.check(summary)
        for match in matches:
            print(match.replacements)
        print(len(matches))
        score=max(0,2-len(matches))
        return score

    def calculate_vocabulary_score(summary):
        # Evaluate the vocabulary usage and richness of the summary
        # Score based on the number of unique words in the summary
        unique_words = set(word_tokenize(summary))
        vocabulary_score = len(unique_words) / 15  # Scaling the unique word count to range 0-2
        vocabulary_score = min(2, vocabulary_score)  # Cap the score at 2
        return vocabulary_score

    def calculate_spelling_score(summary):
        print(summary)
        spell = SpellChecker()
        words = word_tokenize(summary)
        misspelled = spell.unknown(words)
        print(misspelled)
        num_misspelled = len(misspelled)
        if num_misspelled == 0:
            spelling_score = 2
        elif num_misspelled == 1:
            spelling_score = 1
        else:
            spelling_score = 0
        return spelling_score
    def count_paragraphs(summary):
        paragraphs = summary.split("\n")
        non_empty_paragraphs = [p for p in paragraphs if p.strip()]
        print("aragrahs")
        print(len(non_empty_paragraphs))
        if(len(non_empty_paragraphs)==4):
            score=2
        else:
            score=0
        return score
    def calculate_linguistic_score(summary):
        doc = nlp(summary)
        readability_scores = doc._.readability
        flesch_reading_ease = readability_scores['flesch_reading_ease']
        print(flesch_reading_ease)
        if(flesch_reading_ease < 40):
            score=2
        elif(flesch_reading_ease<60):
            score=1
        else:
            score=0
        return score
    reference = '''
In today's globalized world, multilingualism is often celebrated as a valuable skill. However, there are situations in which learning a new foreign language may be deemed unimportant. One such scenario involves individuals whose immediate job roles and professional environments do not necessitate language acquisition.

Consider a professional working in a highly specialized technical field. Their daily tasks revolve around intricate technical knowledge, and their work primarily involves interactions within a small team of colleagues who share the same native language. In this context, the importance of learning a new foreign language diminishes significantly.

Firstly, job requirements are pivotal. If the job entails no international clientele or communication with non-native speakers, there is little incentive for the individual to invest time and effort in language acquisition.

Secondly, limited interaction with non-native speakers further reduces the significance of learning a new language. Effective collaboration, information sharing, and problem-solving can be achieved using the native language within a homogeneous professional environment.

Additionally, time constraints and priorities influence this perception. Learning a new language demands a substantial time commitment. If the individual's profession necessitates continuous skill enhancement, they may prioritize honing their technical expertise over acquiring language skills that offer no immediate professional advantage.

Finally, personal interests also play a role. Some individuals may lack genuine curiosity about languages and cultures outside their immediate surroundings. Without a personal drive to explore foreign languages for travel, leisure, or enrichment, they may consider language acquisition an unimportant endeavor.

In conclusion, while language proficiency is undoubtedly valuable, its importance varies depending on one's career, personal goals, and professional context. For those in specialized fields with limited international interactions, the unimportance of learning a new foreign language is a rational choice, allowing them to focus on their primary areas of expertise and immediate priorities.
    '''
    summary = request.args.get('summary', '')
    scores = score_summary(summary, reference) if summary else None
    if reference == summary:
        return render_template('Write_Essay.html', passage=reference, summary=summary, scores=scores, template="Template Detected")
    else:
        return render_template('Write_Essay.html', passage=reference, summary=summary, scores=scores)

#-------------------------Summarize Spoken----------------------------

@app.route('/Summarize_Spoken', methods=['GET', 'POST'])
def Summarize_Spoken():
    def score_summary(summary, reference):
        # Split the summary into sentences
        sentences = nltk.tokenize.sent_tokenize(summary)

        # if len(sentences) > 1:
        #     # If there are multiple sentences, calculate only the Content score
        #     content_score = calculate_content_score(summary, reference)

        #     # Return individual scores and overall score
        #     scores = {
        #         'Content': content_score,
        #         'Form': 0,
        #         'Grammar': 0,
        #         'Vocabulary': 0,
        #         'Spelling' : 0,
        #         'Overall': content_score
        #     }
        # else:
        # If there is only one sentence, calculate scores for all factors
        content_score = calculate_content_score(summary, reference)
        form_score = calculate_form_score(summary)
        grammar_score = calculate_grammar_score(summary)
        vocabulary_score = calculate_vocabulary_score(summary)
        spelling_score = calculate_spelling_score(summary)
        # Calculate overall score
        if form_score > 0:

            overall_score = (content_score + form_score + grammar_score + vocabulary_score + spelling_score)
        else:
            grammar_score=0
            vocabulary_score=0
            overall_score = (content_score + form_score + grammar_score + vocabulary_score + spelling_score)

        # Return individual scores and overall score
        scores = {
            'Content': content_score,
            'Form': form_score,
            'Grammar': grammar_score,
            'Vocabulary': vocabulary_score,
            'Spelling': spelling_score,
            'Overall': overall_score
        }

        return scores

    # Example scoring functions

    def calculate_content_score(summary, reference):
        # Compare the summary and reference for content relevance
        # Measure the similarity of the summary and reference using spaCy
        doc_summary = nlp(summary)
        doc_reference = nlp(reference)
        content_score = doc_summary.similarity(doc_reference) * 2  # Scaling the similarity score to range 0-2
        return content_score

    def calculate_form_score(summary):
        # Check if the summary is in all uppercase
        if summary.isupper():
            return 0

        # Evaluate the form and structure of the summary
        # Score based on the length of the summary
        summary_length = len(word_tokenize(summary))
        print("summary length")
        print(summary_length)
        if summary_length >= 50 and summary_length <= 70:
            form_score = 2
        # elif summary_length < 50 and summary_length > 5:
        #     # Calculate partial marks based on proximity to 50
        #     form_score = summary_length / 50
        elif summary_length < 50:
            form_score = 1
        elif summary_length > 70:
            form_score=0

        return form_score


    def calculate_grammar_score(summary):
        tool = language_tool_python.LanguageTool('en-US')  # Specify the language (e.g., 'en-US' for American English)

        matches = tool.check(summary)
        for match in matches:
            print(match.replacements)
        print(len(matches))
        score=max(0,2-len(matches))
        return score

    def calculate_vocabulary_score(summary):
        # Evaluate the vocabulary usage and richness of the summary
        # Score based on the number of unique words in the summary
        unique_words = set(word_tokenize(summary))
        vocabulary_score = len(unique_words) / 5  # Scaling the unique word count to range 0-2
        vocabulary_score = min(2, vocabulary_score)  # Cap the score at 2
        return vocabulary_score

    def calculate_spelling_score(summary):
        summary = re.sub(r'[^\w\s]', '', summary.lower())
        print(summary)
        spell = SpellChecker()
        words = word_tokenize(summary)
        misspelled = spell.unknown(words)
        print(misspelled)
        num_misspelled = len(misspelled)
        if num_misspelled == 0:
            spelling_score = 2
        elif num_misspelled == 1:
            spelling_score = 1
        else:
            spelling_score = 0
        
        # misspelled_words_with_suggestions = {word: spell.candidates(word) for word in misspelled}
        # print(misspelled_words_with_suggestions)
        return spelling_score
    summary = request.args.get('summary', '')
    # pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
    # # Transcribe the audio
    # transcription = pipe("converted_audio.wav")
    # reference = transcription['text']
    reference="In The Origin of Species, Darwin provided abundant evidence that life on Earth has evolved over time, and he proposed natural selection as the primary mechanism for that change. He observed that individuals differ in their inherited traits and that selection ads on such differences, leading to evolutionary change. Although Darwin realised that variation in heritable traits is a prerequisite for evolution, he did not know precisely how organisms pass heritable traits to their offspring. Just a few years after Darwin published The Origin of Species, Gregor Mendel wrote a groundbreaking paper on inheritance in pea plants. In that paper, Mendel proposed a model of inheritance in which organisms transmit discrete heritable units (now called genes) to their offspring. Although Darwin did not know about genes, Menders paper set the stage for understanding the genetic differences on which evolution is based."
    # print(summary)
    scores = score_summary(summary, reference) if summary else None
    return render_template('Summarize_Spoken.html', summary=summary, scores=scores)

#-------------------------Spelling----------------------------

@app.route('/Spelling', methods=['GET', 'POST'])
def Spelling():
    word_spellings = {
    "apples": ["apples", "aples", "appels", "apsles"],
    "banana": ["banana", "bannana", "bananna", "bananah"],
    "chocolate": ["chocolate", "choclate", "chocolat", "chocolote"],
    "elephant": ["elephant", "elephent", "eliphant", "ellefant"],
    "guitar": ["guitar", "gutar", "guitare", "geetar"],
    "happiness": ["happiness", "hapiness", "happyness", "happines"],
    "jazz": ["jazz", "jaz", "jazzz", "jazze"],
    "knowledge": ["knowledge", "knawledge", "nolege", "knowlege"],
    "mountain": ["mountain", "mountin", "mounten", "moutain"],
    "penguin": ["penguin", "pengwin", "penguen", "pengin"],
    "umbrella": ["umbrella", "umbralla", "umbrala", "umberella"],
    "volcano": ["volcano", "volkano", "vulcano", "volcanoe"],
    "wonderful": ["wonderful", "wonderfull", "wonderphul", "wonderfulle"],
    "zeppelin": ["zeppelin", "zeplin", "zeppelin", "zepplin"],
    "restaurant": ["restaurant", "restuarant", "resturant", "restraurant"],
}
    word = None  # Initialize the word variable here
    options = []  # Initialize the options variable here

    if request.method == "POST":
        selected_spelling = request.form.get("selected_spelling")
        correct_spelling = request.form.get("correct_spelling")
        result = "Correct! You chose the right spelling." if selected_spelling == correct_spelling else "Incorrect. Try again."
    else:
        word = random.choice(list(word_spellings.keys()))
        correct_spelling = random.choice(word_spellings[word])
        incorrect_spellings = [spelling for spelling in random.sample(word_spellings[word], 4) if spelling != correct_spelling]
        options = [correct_spelling] + incorrect_spellings
        random.shuffle(options)
        result = None

    return render_template("Spelling.html", word=word, options=options, correct_spelling=correct_spelling, result=result)

#-------------------------Listening----------------------------

@app.route('/Listening', methods=['GET', 'POST'])
def Listening():
    summary = request.args.get('summary', '')
    # Define an array of four strings
    word_array = ["rational.mp3", "announcement.mp3", "configuration.mp3"]

    # Generate a random index
    random_index = random.randint(0, len(word_array) - 1)

    # Use the random index to choose a word
    random_word = word_array[random_index]

    print("Random word:", random_word)
    if(summary==""):
        scores=""
        return render_template('Listening.html', summary=summary, scores=scores,file=random_word)    
    # pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
    # Transcribe the audio
    a=request.args.get('audio', '')
    reference=a.strip(".mp3")
    summary = re.sub(r'[^\w\s]', '', summary.lower())
    print(reference)
    print(summary)
    if(reference==summary):
        scores="Correct"
    else:
        scores="Wrong"
    
    # print(summary)
    
    return render_template('Listening.html', summary=summary, scores=scores,file=random_word)

#-------------------------Speech----------------------------

@app.route('/Speech', methods=['GET', 'POST'])
def Speech():
    global reference
    if request.method == 'POST':
        # handle POST request here
        # reference_text = request.json['reference_text']
        # print(reference_text)
        audio = request.files['audio']
        print("ok")
        if audio:
            audio_folder = os.path.join(app.root_path, 'audio')
            if not os.path.exists(audio_folder):
                os.makedirs(audio_folder)
            # save the audio file to the 'audio' folder
            audio_path = os.path.join(audio_folder, audio.filename)
            audio.save(audio_path)
            wav_file_path = "converted_audio.wav"
            audio = AudioSegment.from_file(audio_path)
            audio.export(wav_file_path, format="wav")
            pipe = pipeline("automatic-speech-recognition", model="Wav2Vec2")
            transcription = pipe(wav_file_path)
            reference = transcription['text']
            print(reference)
        return render_template('Speech.html', speech=reference)
    elif request.method == 'GET':
        if reference is False:
            print("a")
            return render_template('Speech.html',speech="")
        else:
            a=reference
            reference=False
            return render_template('Speech.html',speech=a)
          

if __name__ == '__main__':
    # from threading import Thread
    # Thread(target=start_ngrok).start()


    app.run(port=5000, debug=True)



