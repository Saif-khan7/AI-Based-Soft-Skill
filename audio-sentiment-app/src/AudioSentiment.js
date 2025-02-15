import React, { useState, useRef } from 'react';

function AudioSentiment() {
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [sentiment, setSentiment] = useState('');
  const [language, setLanguage] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = []; // reset
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // When the recording stops, send the audio to the backend
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        try {
          const res = await fetch('http://localhost:5000/api/process-audio', {
            method: 'POST',
            body: formData
          });
          const data = await res.json();

          if (data.error) {
            console.error("Error processing audio:", data.error);
          } else {
            setTranscript(data.transcript);
            setSentiment(data.sentiment);
            setLanguage(data.language);
          }
        } catch (err) {
          console.error("Fetch error:", err);
        }
      };

      // Start
      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      console.error('Could not access microphone:', err);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  return (
    <div>
      <button onClick={recording ? stopRecording : startRecording}>
        {recording ? 'Stop Recording' : 'Start Recording'}
      </button>

      {language && (
        <p>
          <strong>Detected Language:</strong> {language}
        </p>
      )}

      <div style={{ marginTop: '1rem' }}>
        <h3>Transcript</h3>
        <p>{transcript || <em>No transcript yet.</em>}</p>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <h3>Sentiment Analysis</h3>
        <pre>{sentiment || <em>No sentiment data yet.</em>}</pre>
      </div>
    </div>
  );
}

export default AudioSentiment;
