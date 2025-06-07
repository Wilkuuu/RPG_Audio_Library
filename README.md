# RPG Audio Manager

A web application for managing and playing audio samples for RPG sessions. This tool helps Dungeon Masters create immersive audio experiences by managing background music and one-shot sound effects.

## Features

- Upload and manage audio samples (MP3, WAV, OGG)
- Mark samples as one-shot or loop
- Create and save scenes with multiple audio samples
- Play individual samples or entire scenes
- Modern, responsive UI
- Dockerized setup for easy deployment

## Prerequisites

- Docker and Docker Compose
- Modern web browser with Web Audio API support

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rpg-audio-manager
```

2. Create the audio_files directory:
```bash
mkdir audio_files
```

3. Start the application using Docker Compose:
```bash
docker-compose up --build
```

4. Access the application at `http://localhost:5000`

## Usage

### Managing Samples

1. Click the "Upload Sample" button to add new audio files
2. Provide a name, category, and select whether it's a one-shot sample
3. Upload MP3, WAV, or OGG files
4. Use the play button to test samples
5. Delete samples using the trash icon

### Creating Scenes

1. Navigate to the "Scenes" tab
2. Click "Create Scene" to make a new scene
3. Add a name and description
4. Select samples to include in the scene
5. Save the scene for later use

## Development

The application consists of:
- Flask backend API
- MongoDB database
- HTML/JavaScript frontend
- Docker configuration

### Project Structure

```
.
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── templates/         # Frontend templates
│   └── index.html    # Main application page
└── audio_files/      # Directory for uploaded audio files
```

## License

MIT License