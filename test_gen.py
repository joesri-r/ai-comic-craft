from app.image_generator import generate_image
res = generate_image("brave fox finding a magic portal in the forest", "brave fox", "Comic Book", panel_num=1)
print(res["data_uri"][:50])
