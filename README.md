# Music Mashup Generator  
## Predictive Analysis – Mashup Assignment  

**Name:** Arshia Anand  
**Roll Number:** 102303144  

---

#  Project Overview

This project implements a **Music Mashup Generator** in two formats:

---

##  Program 1 – Command Line Application

A Python script that:

- Downloads **N YouTube videos** of a singer  
- Converts them to MP3  
- Trims first **Y seconds**  
- Merges them into one mashup file  

---

## Program 2 – Web Service Application

A deployed web-based mashup generator that:

- Accepts user input via a web form  
- Generates mashup on server  
- Sends the output as a ZIP file to user email  

---

# Technologies Used

## Backend
- Python  
- yt-dlp  
- pydub  
- requests  
- FFmpeg  

## Frontend
- HTML  
- CSS  
- JavaScript (Fetch API)  

## Deployment
- Vercel Serverless Functions  

---

# Program 1 – Command Line Mashup

## File Name

- 102303144.py

---

## How to Run

```bash
python 102303144.py "<SingerName>" <NumberOfVideos> <AudioDuration> <OutputFileName>
```

## Example
```bash
python 102303144.py "Sharry Maan" 15 30 mashup.mp3
```

## What It Does

- Downloads top N YouTube videos of the given singer
- Converts audio to MP3
- Cuts first Y seconds from each file
- Merges all trimmed audios
- Produces a single output MP3

## Input Validation
- Singer Name: Required
- Number of Videos: Integer > 10
- Duration: Integer > 20
- Output File: Must end with .mp3

## Setup for Program 1
1. Install Python
Install Python 3.10 or 3.11

2. Install FFmpeg
Download from:
https://www.gyan.dev/ffmpeg/builds/
Add the bin folder to your system PATH.

3. Install Required Libraries
pip install yt-dlp pydub


# Program 2 – Web Mashup Service

## Frontend Features
- Responsive UI
- Input validation
- Loader animation
- Error handling
- Success messages

## API Endpoint
### GET Request
/api/mashup

### Response:
{
  "message": "Mashup API - Use POST method with JSON data",
  "status": "running"
}

### POST Request
/api/mashup

### JSON Input Format:
{
  "singer": "Arijit Singh",
  "num_videos": 12,
  "duration": 25,
  "email": "user@email.com"
}

## Email Delivery
Mashup is converted into mashup.mp3
Compressed into mashup.zip
Sent via Resend API

## Requires environment variable:
RESEND_API_KEY=your_api_key

## Author
- Arshia Anand
- Roll Number: 102303144

## Conclusion

This project demonstrates a complete end-to-end audio processing pipeline, combining multimedia processing, backend development, and deployment into a functional mashup generation system.

It highlights practical implementation of Python libraries, API development, validation mechanisms, and automated file handling — successfully fulfilling all assignment requirements for both CLI and Web Service formats.


