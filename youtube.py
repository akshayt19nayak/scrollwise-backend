import re
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

openai_client = OpenAI()

def get_video_id(youtube_url):
    # Extract the video ID from the YouTube URL
    video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
    return video_id.group(1) if video_id else None

def fetch_transcript(youtube_url, language='en'):
    # Get the video ID
    video_id = get_video_id(youtube_url)
    if not video_id:
        return "Invalid YouTube URL provided."

    try:
        # Fetch the transcript in the specified language
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        
        # Format the transcript text
        transcript = " ".join([item['text'] for item in transcript_data])
        return transcript

    except Exception as e:
        return f"An error occurred: {e}"
    
def summarize(youtube_url):
    transcript = fetch_transcript(youtube_url)
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {
          "role": "system",
          "content": [
            {
              "type": "text",
              "text": "You will be provided a transcript of a YouTube video. Summarize key insights covering all important points, assuming you are relaying them to a person who does not have the time to watch the video. The summary needs to be fewer than 1500 characters strictly! Also, do not include any \n in your output!"
            }
          ]
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": transcript
            }
          ]
        }
      ]
    )
    return completion.choices[0].message.content