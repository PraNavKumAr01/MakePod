import json
from pydub import AudioSegment
import io
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from deepgram.client import DeepgramClient, SpeakOptions
import os
from dotenv import load_dotenv
import random

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["DEEPGRAM_API_KEY"] = os.environ.get("DEEPGRAM_API_KEY")

VOICES = {
    "female": ["aura-stella-en", "aura-athena-en", "aura-hera-en"],
    "male": ["aura-orion-en", "aura-arcas-en", "aura-perseus-en"]
}

def get_response(query, num_speakers, male_count, female_count):
    llm = ChatGroq(temperature=0.4, model_name="llama3-70b-8192")

    prompt = PromptTemplate(
        input_variables=["user_query", "num_speakers", "male_count", "female_count"],
        template="""
        Generate a podcast script based on this topic: {user_query}
        
        The podcast should have {num_speakers} speakers, with {male_count} male and {female_count} female speakers.
        
        The script should be in the following JSON format:
        {{
          "podcast": {{
            "title": "Title of the podcast",
            "speakers": [
              {{"id": "S1", "gender": "male/female"}},
              {{"id": "S2", "gender": "male/female"}},
              // ... up to the specified number of speakers
            ],
            "segments": [
              {{
                "speaker": "S1",
                "text": "Speaker's dialogue..."
              }},
              // ... more segments
            ]
          }}
        }}
        
        Ensure that the script has a natural conversation flow and uses all specified speakers.
        Please start directly with the json file no text before or after the json.
        """
    )

    chain = prompt | llm
    response = chain.invoke({
        "user_query": query,
        "num_speakers": num_speakers,
        "male_count": male_count,
        "female_count": female_count
    })
    
    return json.loads(response.content)

def text_to_speech(transcript, voice_code):
    try:
        deepgram = DeepgramClient()
        speak_options = {"text": transcript}

        options = SpeakOptions(
            model=voice_code,
            encoding="linear16",
            container="wav"
        )

        response = deepgram.speak.v("1").stream(speak_options, options)

        return response.stream.getvalue()

    except Exception as e:
        print(f"Exception: {e}")

def generate_podcast(topic, num_speakers, male_count, female_count):
    # Generate script
    script = get_response(topic, num_speakers, male_count, female_count)
    return script
    
    # Assign voices to speakers
    speaker_voices = {}
    male_voices = VOICES["male"].copy()
    female_voices = VOICES["female"].copy()
    random.shuffle(male_voices)
    random.shuffle(female_voices)
    
    for speaker in script['podcast']['speakers']:
        if speaker['gender'] == 'male':
            speaker_voices[speaker['id']] = male_voices.pop()
        else:
            speaker_voices[speaker['id']] = female_voices.pop()
    
    # Group segments by speaker
    speaker_segments = {}
    for segment in script['podcast']['segments']:
        speaker = segment['speaker']
        if speaker not in speaker_segments:
            speaker_segments[speaker] = []
        speaker_segments[speaker].append(segment)
    
    # Generate audio for each speaker
    speaker_audio = {}
    for speaker, segments in speaker_segments.items():
        combined_text = " ".join([segment['text'] for segment in segments])
        audio_bytes = text_to_speech(combined_text, speaker_voices[speaker])
        speaker_audio[speaker] = AudioSegment.from_wav(io.BytesIO(audio_bytes))
    
    # Stitch audio segments together
    final_audio = AudioSegment.silent(duration=0)
    for segment in script['podcast']['segments']:
        speaker = segment['speaker']
        audio_chunk = speaker_audio[speaker][:len(speaker_audio[speaker])]
        final_audio += audio_chunk
        speaker_audio[speaker] = speaker_audio[speaker][len(audio_chunk):]
    
    # Export final audio
    output_path = "generated_podcast.mp3"
    final_audio.export(output_path, format="mp3")
    
    return output_path, script['podcast']['title']

# Example usage
topic = "AI in todays world" #input("Enter the podcast topic: ")
num_speakers = 3 #int(input("Enter the total number of speakers (1-6): "))
male_count = 1 #int(input("Enter the number of male speakers: "))
female_count = 2 #int(input("Enter the number of female speakers: "))

podcast_title = generate_podcast(topic, num_speakers, male_count, female_count)
print(json.dumps(podcast_title, indent = 3))
#print(f"Podcast '{podcast_title}' generated and saved as: {podcast_file}")