from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import os
import speech_recognition as sr
from pydub import AudioSegment
import threading
import time

app = Flask(__name__, static_folder='static', template_folder='templates')

# Ensure 'uploads' directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to delete the transcription file after 5 minutes
def delete_transcription_after_delay():
    time.sleep(300)  # Sleep for 300 seconds (5 minutes)
    if os.path.exists("transcribe.txt"):
        try:
            os.remove("transcribe.txt")
            print("transcribe.txt deleted after 5 minutes of inactivity")
        except Exception as e:
            print(f"Error deleting transcribe.txt: {e}")

# Function to convert MP4 to WAV
def convert_mp4_to_wav(mp4_file_path, output_wav_path):
    audio = AudioSegment.from_file(mp4_file_path, format="mp4")
    audio.export(output_wav_path, format="wav")
    return output_wav_path

# Function to transcribe audio from a WAV file
def transcribe_audio(wav_file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(wav_file_path)
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

    # Schedule deletion of transcribe.txt after 5 minutes
    threading.Thread(target=delete_transcription_after_delay).start()

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

        # Convert MP4 to WAV if necessary
        if file.filename.endswith('.mp4'):
            wav_file_path = file_path.replace('.mp4', '.wav')
            convert_mp4_to_wav(file_path, wav_file_path)
            print(f"MP4 file converted to WAV: {wav_file_path}")
        else:
            wav_file_path = file_path  # Use the uploaded file directly if it's not MP4

        # Transcribe the file
        transcription_file = transcribe_audio(wav_file_path)

        # Delete the uploaded audio/video file and converted WAV files (if any) after transcription
        os.remove(file_path)
        if file.filename.endswith('.mp4'):
            os.remove(wav_file_path)

        # Return success response
        return jsonify({
            'transcription': transcription_file
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
