import os
import tempfile

from flask import Flask, request, jsonify
import whisper
from transformers import pipeline
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 1) Load the Whisper model (change "base" to another size if desired).
model = whisper.load_model("base")

# 2) Load the sentiment pipeline (SamLowe/roberta-base-go_emotions is one option).
sentiment_analysis = pipeline(
    "sentiment-analysis",
    model="SamLowe/roberta-base-go_emotions",
    framework="pt",
)

def analyze_sentiment(text):
    """Run text through the Hugging Face sentiment pipeline and return a dict of sentiment->score."""
    results = sentiment_analysis(text)
    return {r["label"]: r["score"] for r in results}

def get_sentiment_emoji(sentiment):
    """Map certain sentiments to emojis for fun."""
    emoji_mapping = {
        "disappointment": "😞",
        "sadness": "😢",
        "annoyance": "😠",
        "neutral": "😐",
        "disapproval": "👎",
        "realization": "😮",
        "nervousness": "😬",
        "approval": "👍",
        "joy": "😄",
        "anger": "😡",
        "embarrassment": "😳",
        "caring": "🤗",
        "remorse": "😔",
        "disgust": "🤢",
        "grief": "😥",
        "confusion": "😕",
        "relief": "😌",
        "desire": "😍",
        "admiration": "😌",
        "optimism": "😊",
        "fear": "😨",
        "love": "❤️",
        "excitement": "🎉",
        "curiosity": "🤔",
        "amusement": "😄",
        "surprise": "😲",
        "gratitude": "🙏",
        "pride": "🦁"
    }
    return emoji_mapping.get(sentiment, "")

def display_sentiment_results(sentiment_scores, option="Sentiment + Score"):
    """
    Convert the sentiment dict into human-readable lines.
    option can be "Sentiment Only" or "Sentiment + Score".
    """
    output_lines = []
    for sentiment, score in sentiment_scores.items():
        emoji = get_sentiment_emoji(sentiment)
        if option == "Sentiment Only":
            output_lines.append(f"{sentiment} {emoji}")
        else:  # "Sentiment + Score"
            output_lines.append(f"{sentiment} {emoji}: {score:.2f}")

    return "\n".join(output_lines)

def inference(audio_file_path, sentiment_option="Sentiment + Score"):
    """Use Whisper to transcribe the file, detect language, and run sentiment analysis on the result."""
    # Load audio and pad/trim to 30 seconds if needed
    audio = whisper.load_audio(audio_file_path)
    audio = whisper.pad_or_trim(audio)

    # Compute the log-Mel spectrogram
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # Language detection
    _, probs = model.detect_language(mel)
    detected_lang = max(probs, key=probs.get)

    # Transcription
    options = whisper.DecodingOptions(fp16=False)  # CPU-safe
    result = whisper.decode(model, mel, options)
    transcript = result.text

    # Sentiment analysis
    scores = analyze_sentiment(transcript)
    sentiment_text = display_sentiment_results(scores, sentiment_option)

    return detected_lang.upper(), transcript, sentiment_text

@app.route("/api/process-audio", methods=["POST"])
def process_audio():
    """Handles audio uploads for transcription and sentiment analysis."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    audio_file = request.files["audio"]
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        lang, transcript, sentiment_output = inference(tmp_path)
        return jsonify({
            "language": lang,
            "transcript": transcript,
            "sentiment": sentiment_output
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
