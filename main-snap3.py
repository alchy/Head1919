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


def update_camera(camera_pos, speed=0.5):
    """
    Aktualizuje pozici kamery na základě stisknutých kláves:
    - W posune kameru vpřed (blíže ke středu)
    - S posune kameru vzad (dál od středu)
    - A posune kameru nahoru
    - D posune kameru dolů
    Kamera se stále dívá na střed (0, 0, 0)
    """
    keys = pygame.key.get_pressed()

    # Vypočítáme směr od kamery ke středu
    dir_to_center = [-camera_pos[0], -camera_pos[1], -camera_pos[2]]
    length = math.sqrt(dir_to_center[0] ** 2 + dir_to_center[1] ** 2 + dir_to_center[2] ** 2)
    norm_dir = [d / length for d in dir_to_center] if length != 0 else [0, 0, 0]

    # Pohyb vpřed a vzad ve směru ke středu
    if keys[pygame.K_w]:
        camera_pos = [camera_pos[i] + norm_dir[i] * speed for i in range(3)]
    if keys[pygame.K_s]:
        camera_pos = [camera_pos[i] - norm_dir[i] * speed for i in range(3)]

    # Pohyb nahoru a dolů (podle osy Y)
    if keys[pygame.K_a]:
        camera_pos[1] += speed
    if keys[pygame.K_d]:
        camera_pos[1] -= speed

    return camera_pos


def render_text(x, y, text_string, font_name="Arial", font_size=18, text_color=(255, 255, 255, 255)):
    """
    Vykreslí text pomocí OpenGL. Funkce využívá pygame.font k vygenerování textové plochy,
    kterou následně převádí na texturu a vykreslí pomocí glDrawPixels.

    Parametry:
    - x, y: pozice v okně (v pixelech; počátek je v levém dolním rohu)
    - text_string: řetězec textu, který chceme vykreslit
    - font_name, font_size: vlastnosti použitého písma
    - text_color: barva textu (RGBA)
    """
    font = pygame.font.SysFont(font_name, font_size)
    # Vytvoříme povrch pro text (přičemž alfa složka je zachována)
    text_surface = font.render(text_string, True, text_color[:3])
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
    Vykreslí text s aktuálními souřadnicemi kamery do levého horního rohu.
    (Při vykreslování pomocí glWindowPos2d počítáme s počátkem v levém dolním rohu,
    proto přepočítáme souřadnice tak, aby text byl umístěn v levém horním rohu.)
    """
    text = f"Camera: x={camera_pos[0]:.2f}, y={camera_pos[1]:.2f}, z={camera_pos[2]:.2f}"
    # Přepočet: x = 10 px od levého okraje, y = display_height - 30 px od spodního okraje
    render_text(10, display_size[1] - 30, text)


def main():
    # Inicializace Pygame a nastavení okna
    pygame.init()
    display_size = (800, 600)
    pygame.display.set_mode(display_size, DOUBLEBUF | OPENGL)

    # Inicializace fontu (nutné před první renderací textu)
    pygame.font.init()

    # Nastavení perspektivy
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, display_size[0] / display_size[1], 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    # Výchozí pozice kamery
    camera_pos = [0, 0, 10]

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