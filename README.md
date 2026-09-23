# ComicCraft - AI Comic Story Creator

ComicCraft is a full-stack Python web application that uses Google's Gemini models and Stable Diffusion to generate completely original, 5-panel comic stories based on user prompts.

## Features

- **Story Generation:** Uses `gemini-1.5-flash` to generate a 5-panel outline, and `gemini-1.5-pro` to write narration and dialogue.
- **Image Generation:** Uses `Stable Diffusion v1.5` to generate unique comic panel images. Supports both CUDA GPU and CPU fallback.
- **PDF Export:** Uses `fpdf2` to lay out the images and text into a downloadable PDF.
- **Demo Mode:** Allows testing the entire UI and workflow without API keys or GPU.

## Technology Stack

- **Backend:** FastAPI, Python 3.11+, Uvicorn
- **AI:** Google Generative AI (Gemini), Hugging Face Diffusers (Stable Diffusion)
- **PDF:** FPDF2
- **Frontend:** HTML5, CSS3, Vanilla JS, Jinja2 Templates

## Project Structure

```text
comiccraft/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes.py
│   ├── gemini_flash.py
│   ├── gemini_pro.py
│   ├── image_generator.py
│   ├── layout_builder.py
│   ├── exporters.py
│   └── config.py
├── templates/
├── static/
├── requirements.txt
├── .env
├── .env.example
├── README.md
└── run.bat
```

## Setup & Installation

### 1. Requirements
Ensure you have Python 3.11+ installed on your system.

### 2. Setup API Keys
Get your API keys:
- **Gemini API Key:** From Google AI Studio (https://aistudio.google.com/)
- **Hugging Face Token:** From Hugging Face Settings (https://huggingface.co/settings/tokens)

### 3. Configuration
Copy `.env.example` to `.env` and fill in your keys.

```env
GEMINI_API_KEY=your_gemini_key_here
HF_API_KEY=your_hf_token_here
IMAGE_MODEL_ID=runwayml/stable-diffusion-v1-5
IMAGE_GENERATION_ENABLED=true
DEMO_MODE=true
```

## Running the Application (Windows)

The easiest way to run the application on Windows is using the provided `run.bat` script.

1. Double click `run.bat` or run it from the command line:
```cmd
run.bat
```

This script will automatically:
- Create a Python virtual environment (`env`)
- Activate it
- Install all dependencies from `requirements.txt`
- Start the FastAPI server using `uvicorn`

2. Open your browser and go to:
```text
http://127.0.0.1:8000
```

3. Swagger UI is available at:
```text
http://127.0.0.1:8000/docs
```

## Testing DEMO_MODE

By default, the `.env` file sets `DEMO_MODE=true`. This allows you to test the complete workflow (form submission, loading screen, comic layout, PDF export) without making real API calls. Placeholder data and images will be used.

## Switching to Real AI Mode

Once you have verified the UI works in Demo Mode:
1. Open `.env`
2. Change `DEMO_MODE=true` to `DEMO_MODE=false`
3. Ensure `GEMINI_API_KEY` and `HF_API_KEY` are valid.
4. Restart the server.

## CPU vs GPU Image Generation

Stable Diffusion image generation requires significant compute. The application will automatically detect if a CUDA-compatible GPU is available (`torch.cuda.is_available()`).

- **If CUDA is available:** Image generation will be fast.
- **If CUDA is not available:** Image generation will fall back to CPU. **This can be extremely slow.** Ensure you have patience when testing on CPU.

## Common Errors & Solutions

- **CUDA Out of Memory:** Close other applications using GPU memory.
- **Missing API Keys Error:** Ensure `DEMO_MODE=false` and keys are correctly placed in `.env`.
- **Image Generation Hangs:** CPU generation can take minutes per image. Watch your terminal for progress.
- **PDF Encoding Errors:** FPDF2 handles most text, but exotic unicode characters may be stripped.

## API Compatibility Notes
The original project specified "Gemini Flash" and "Gemini Pro". This implementation uses `gemini-1.5-flash` and `gemini-1.5-pro` via the `google-generativeai` SDK, which are the current recommended standard models.
