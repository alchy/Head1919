import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math


def load_obj(filename):
    """
    Načte soubor .obj a vrátí seznam vrcholů a indexů obličejů.
    Tento jednoduchý parser očekává, že soubor obsahuje pouze definice vrcholů (v)
    a obličejů (f) bez normál nebo texturovacích koeficientů.
    """
    vertices = []
    faces = []
    with open(filename, "r") as file:
        for line in file:
            if line.startswith("v "):  # načítání vrcholů
                parts = line.strip().split()
                vertex = list(map(float, parts[1:4]))
                vertices.append(vertex)
            elif line.startswith("f "):  # načítání obličejů
                parts = line.strip().split()
                # Očekáváme pouze čísla reprezentující indexy
                face = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                faces.append(face)
    return vertices, faces


def compile_display_list(vertices, faces):
    """
    Vytvoří OpenGL display list, který ukládá vykreslení modelu.
    Díky tomu se vykreslování zrychlí, protože model je kompilován pouze jednou.
    """
    model_list = glGenLists(1)
    glNewList(model_list, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for face in faces:
        # Pokud obličej nemá přesně 3 vrcholy, rozdělíme jej na trojúhelníky
        if len(face) == 3:
            for vertex_index in face:
                glVertex3fv(vertices[vertex_index])
        else:
            for i in range(1, len(face) - 1):
                glVertex3fv(vertices[face[0]])
                glVertex3fv(vertices[face[i]])
                glVertex3fv(vertices[face[i + 1]])
    glEnd()
    glEndList()
    return model_list


import pygame
import math

def update_camera(camera_pos, speed=0.5):
    """
    Aktualizuje pozici kamery na základě stisknutých kláves:
    - W posune kameru vpřed (blíže ke středu)
    - S posune kameru vzad (dál od středu)
    - Q posune kameru nahoru
    - E posune kameru dolů
    - A posune kameru vlevo
    - D posune kameru vpravo
    Kamera se stále dívá na střed (0, 0, 0)
    """
    keys = pygame.key.get_pressed()

    # Vypočítáme směr od kamery ke středu
    dir_to_center = [-camera_pos[0], -camera_pos[1], -camera_pos[2]]
    length = math.hypot(*dir_to_center)
    norm_dir = [d / length for d in dir_to_center] if length != 0 else [0, 0, 0]

    # Pohyb vpřed a vzad ve směru ke středu
    if keys[pygame.K_w]:
        camera_pos = [camera_pos[i] + norm_dir[i] * speed for i in range(3)]
    if keys[pygame.K_s]:
        camera_pos = [camera_pos[i] - norm_dir[i] * speed for i in range(3)]

    # Pohyb nahoru a dolů (podle osy Y)
    if keys[pygame.K_q]:
        camera_pos[1] += speed
    if keys[pygame.K_e]:
        camera_pos[1] -= speed

    # Vleno a vpravo (podle osy X)
    if keys[pygame.K_a]:
        camera_pos[0] += speed
    if keys[pygame.K_d]:
        camera_pos[0] -= speed

    return camera_pos


def render_text(x, y, text_string, font_name="Arial", font_size=18):
    """
    Vykreslí text pomocí OpenGL.
    Text se vykreslí s bílou barvou, přičemž pozadí bitmapy bude černé.
    Použijeme pygame.font k vygenerování textové plochy, kterou následně vykreslíme pomocí glDrawPixels.

    Parametry:
    - x, y: pozice v okně (v pixelech; počátek je v levém dolním rohu)
    - text_string: řetězec textu, který chceme vykreslit
    - font_name, font_size: vlastnosti použitého písma
    """
    # Nastavení bílého textu a černého pozadí
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)

    font = pygame.font.SysFont(font_name, font_size)
    # Vyrenderujeme text s černým pozadím
    text_surface = font.render(text_string, True, text_color, background_color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)

    # Nastavíme pozici vykreslení; glWindowPos2d bere počátek v levém dolním rohu
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def render_scene(model_list):
    """
    Vykreslí 3D scénu obsahující model, jehož vykreslení je uloženo v display listu.
    """
    glCallList(model_list)


def render_camera_coordinates(camera_pos, display_size):
    """
    Vykreslí text s aktuálními souřadnicemi kamery.
    Text je umístěn v levém horním rohu.
    """
    text = f"Camera: x={camera_pos[0]:.2f}, y={camera_pos[1]:.2f}, z={camera_pos[2]:.2f}"
    # Přepočet: x = 10 px od levého okraje, y = display_height - 30 px od spodního okraje
    render_text(10, display_size[1] - 30, text)


def initialize():
    """
    Inicializuje Pygame, OpenGL a nastavení perspektivy.
    """
    pygame.init()
    display_size = (800, 600)
    pygame.display.set_mode(display_size, DOUBLEBUF | OPENGL)
    pygame.font.init()  # nutné pro vykreslení textu

    # Nastavíme perspektivu
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, display_size[0] / display_size[1], 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    return display_size


def main():
    display_size = initialize()

    # Nastavení parametrů pohledu
    fov = 45           # zorné pole
    near_val = 0.5     # near clipping plane: objekty blíže než 0.5 jednotky budou oříznuty
    far_val = 500.0     # far clipping plane: objekty dále než 50 jednotek nebudou vykresleny

    # Nastavení perspektivy s možností úpravy near a far
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, display_size[0] / display_size[1], near_val, far_val)
    glMatrixMode(GL_MODELVIEW)

    # Výchozí pozice kamery
    camera_pos = [0, 0, 50]

    # Načtení modelu a vytvoření display listu
    vertices, faces = load_obj("model.obj")
    model_list = compile_display_list(vertices, faces)

    # Nastavení režimu drátového zobrazení
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Aktualizace pozice kamery na základě stisků kláves
        camera_pos = update_camera(camera_pos, speed=0.5)

        # Překreslení celé scény
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # Kamera se nachází v camera_pos a směřuje do středu (0, 0, 0)
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0, 0, 0,
                  0, 1, 0)

        render_scene(model_list)
        render_camera_coordinates(camera_pos, display_size)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()