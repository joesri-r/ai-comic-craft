def build_comic_layout(story: list, generated_images: list) -> list:
    """
    Merge the generated story and generated images into a final layout structure.
    
    :param story: List of dictionaries containing the story details per panel.
    :param generated_images: List of image paths for the panels.
    :return: List of dictionaries with combined panel data.
    """
    layout = []
    
    # Ensure we have matching lengths
    num_panels = min(len(story), len(generated_images))
    
    for i in range(num_panels):
        panel_data = story[i].copy()
        panel_data["image_path"] = generated_images[i]
        layout.append(panel_data)
        
    return layout
