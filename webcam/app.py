from flask import Flask, render_template, request, redirect, jsonify
import os
import face_recognition
from PIL import Image
from retrying import retry
import requests
import cv2


app = Flask(__name__)

ngrok_URL = 'https://5ec0-103-109-52-23.ngrok-free.app'  # ngrok URL
API_URL = f'{ngrok_URL}/api/v1'


# Retry 3 times with 2 seconds delay
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def send_file(file_path, upload_url):
    file = open(file_path, 'rb')
    response = requests.post(upload_url, files={'file': file}, timeout=60)  # Timeout after 60 seconds
    file.close()
    response.raise_for_status()  # Raise exception if status code is not 200

    return response


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/failure')
def failure():
    return render_template('failure.html')

@app.route('/capture', methods=['POST'])
def capture():
    # Get the captured image from the request
    captured_image = request.files['image']

    # Save the captured image to a folder
    captured_image.save('static/captured.jpg')

    # Load the captured image for face recognition
    captured_image = face_recognition.load_image_file('static/captured.jpg')

    # ====================================================================================================
    # Send image file
    image_file_path = 'static/captured.jpg'
    image_upload_url = f'{API_URL}/image'

    response = send_file(image_file_path, image_upload_url)
    response = response.json()
    print(response)
    # ====================================================================================================

    if response['face_match_status']==True:
        return jsonify({'redirect_url': '/success'})
    else:
        print(response['face_match_status'])
        return jsonify({'redirect_url': '/failure'})



if __name__ == '__main__':
    app.run(debug=True)
