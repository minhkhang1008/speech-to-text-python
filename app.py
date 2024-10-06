from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import os
import speech_recognition as sr
from pydub import AudioSegment
import threading
import time

app = Flask(__name__)

# Ensure 'uploads' directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to delete transcribe.txt after 10 minutes if not downloaded
def delete_transcribe_after_delay():
    time.sleep(600)  # Sleep for 600 seconds (10 minutes)
    if os.path.exists("transcribe.txt"):
        try:
            os.remove("transcribe.txt")
            print("transcribe.txt deleted after 10 minutes of inactivity")
        except Exception as e:
            print(f"Error deleting transcribe.txt: {e}")

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    chunks = [audio[i:i + 60000] for i in range(0, len(audio), 60000)]  # 60s chunks

    full_transcription = []
    for i, chunk in enumerate(chunks):
        chunk_filename = f"chunk_{i}.wav"
        chunk.export(chunk_filename, format="wav")
        with sr.AudioFile(chunk_filename) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            full_transcription.append(text)
        except sr.UnknownValueError:
            full_transcription.append("[Unrecognized Audio]")
        except sr.RequestError as e:
            full_transcription.append(f"[API Error: {e}]")
        finally:
            os.remove(chunk_filename)

    # Save transcription to file
    transcription_file = "transcribe.txt"
    with open(transcription_file, "w") as f:
        f.write(" ".join(full_transcription))
    
    # Schedule deletion of transcribe.txt after 10 minutes if not downloaded
    threading.Thread(target=delete_transcribe_after_delay).start()

    return transcription_file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if there's an existing transcribe.txt and delete it before uploading a new file
        if os.path.exists("transcribe.txt"):
            os.remove("transcribe.txt")
            print("Old transcribe.txt deleted before processing new file")

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save the uploaded file to the server
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Get the size of the file in MB (rounded up)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        file_size_mb_rounded = round(file_size_mb)

        # Transcribe the file
        transcription_file = transcribe_audio(file_path)

        # Delete the uploaded audio file after transcription
        os.remove(file_path)

        # Return the file size along with the transcription file path
        return jsonify({
            'transcription': transcription_file,
            'file_size_mb': file_size_mb_rounded
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_transcription():
    try:
        transcription_file = "transcribe.txt"
        if os.path.exists(transcription_file):
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(transcription_file)  # Delete the transcription file after sending it
                except Exception as error:
                    print(f"Error removing file: {error}")
                return response
            
            return send_file(transcription_file, as_attachment=True)
        else:
            return jsonify({'error': 'Transcription file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
