import os
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

from pathlib import Path

router = APIRouter()

# Setup templates with absolute path (required for Vercel serverless)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def _generate_all_panel_images(outline, character_description, art_style):
    """Generate images for all panels sequentially with time budget awareness for Vercel."""
    import time
    import os

    # Vercel has strict timeouts: 10s hobby, 60s pro. Budget accordingly.
    is_vercel = bool(os.getenv("VERCEL"))
    max_total_seconds = 50 if is_vercel else 300  # leave 10s buffer on Vercel
    start_time = time.time()

    results = []
    for idx, panel in enumerate(outline):
        elapsed = time.time() - start_time
        remaining = max_total_seconds - elapsed

        # If running low on time, use demo placeholders for remaining panels
        if remaining < 8:
            print(f"[routes] Time budget low ({remaining:.1f}s left). Using placeholder for Panel {idx + 1}.")
            from app.image_generator import generate_image, _make_demo_placeholder
            import tempfile, uuid, base64
            filename = f"panel_{int(time.time())}_{idx + 1}_{uuid.uuid4().hex[:6]}.png"
            filepath = os.path.join(tempfile.gettempdir(), "comiccraft", "panels", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            _make_demo_placeholder(filepath, idx + 1, panel.get("image_prompt", ""))
            try:
                with open(filepath, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    data_uri = f"data:image/png;base64,{b64}"
            except Exception:
                data_uri = ""
            results.append({"file_path": filepath, "data_uri": data_uri})
            continue

        img_prompt = panel.get("image_prompt", character_description)
        path = generate_image(img_prompt, character_description, art_style, panel_num=idx + 1)
        results.append(path)

    return results

@router.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@router.post("/generate", response_class=HTMLResponse)
async def generate_comic_html(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):
    try:
        # 1. Generate Outline
        outline = generate_outline(story_prompt, character_name, setting, tone, art_style)
        
        # 2. Generate Story
        story = generate_story(story_prompt, character_name, setting, tone, art_style, outline)
        
        # 3. Generate Images (in parallel)
        character_description = f"{character_name} in {setting}"
        generated_images = _generate_all_panel_images(outline, character_description, art_style)
            
        # 4. Build Layout
        layout = build_comic_layout(story, generated_images)
        
        # 5. Save PDF
        pdf_filepath = save_pdf(layout)
        
        # 6. Convert PDF to base64 for download link
        import base64
        import os
        try:
            with open(pdf_filepath, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
                pdf_data_uri = f"data:application/pdf;base64,{pdf_b64}"
            pdf_filename = os.path.basename(pdf_filepath)
        except Exception as e:
            print(f"Error encoding PDF base64: {e}")
            pdf_data_uri = ""
            pdf_filename = "comic.pdf"
        
        return templates.TemplateResponse(
            request,
            "comic_preview.html",
            {
                "panels": layout,
                "pdf_filename": pdf_filename,
                "pdf_data_uri": pdf_data_uri
            }
        )
        
    except Exception as e:
        print(f"Error during generation: {e}")
        return templates.TemplateResponse(request, "error.html", {"error_message": str(e)})

class ComicRequest(BaseModel):
    story_prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str

@router.post("/generate-comic/json")
async def generate_comic_json(req: ComicRequest):
    try:
        outline = generate_outline(req.story_prompt, req.character_name, req.setting, req.tone, req.art_style)
        story = generate_story(req.story_prompt, req.character_name, req.setting, req.tone, req.art_style, outline)
        
        character_description = f"{req.character_name} in {req.setting}"
        generated_images = _generate_all_panel_images(outline, character_description, req.art_style)
            
        layout = build_comic_layout(story, generated_images)
        pdf_filename = save_pdf(layout)
        
        return {
            "success": True,
            "layout": layout,
            "pdf_filename": pdf_filename,
            "pdf_url": f"/download/{pdf_filename}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/test-image")
async def test_image(prompt: str):
    try:
        img_path = generate_image(prompt, "Test Character", "Comic Book")
        return {"success": True, "image_path": img_path}
    except Exception as e:
        return {"success": False, "error": str(e)}



@router.get("/download/{filename}")
async def download_pdf(filename: str):
    # Security: Prevent path traversal
    safe_name = os.path.basename(filename)
    file_path = BASE_DIR / "static" / "exports" / safe_name
    
    if file_path.exists():
        return FileResponse(path=str(file_path), filename=safe_name, media_type='application/pdf')
    else:
        return RedirectResponse(url="/")

@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request):
    return templates.TemplateResponse(request, "export_success.html")
