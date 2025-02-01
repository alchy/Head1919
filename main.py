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
            if line.startswith("v "):  # Načítáme definici vrcholu
                parts = line.strip().split()
                # Převedeme souřadnice na float
                vertex = list(map(float, parts[1:4]))
                vertices.append(vertex)
            elif line.startswith("f "):  # Načítáme definici obličeje
                parts = line.strip().split()
                # Indexy v souboru OBJ začínají od 1, proto odečítáme 1
                face = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                faces.append(face)
    return vertices, faces


def compile_display_list(vertices, faces):
    """
    Vytvoří OpenGL display list, který obsahuje příkazy pro vykreslení modelu.
    Display list je kompilován pouze jednou, což zvyšuje výkon vykreslování.
    """
    model_list = glGenLists(1)
    glNewList(model_list, GL_COMPILE)

    # Nastavíme barvu modelu na zelenou
    glColor3f(0.2, 0.6, 0.2)

    glBegin(GL_TRIANGLES)
    for face in faces:
        # Pokud má obličej přesně 3 vrcholy, vykreslíme jej přímo.
        # Jinak provedeme triangulaci pomocí vytváření vějířové struktury (fan)
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
    - W posouvá kameru vpřed (směrem ke středu)
    - S posouvá kameru vzad
    - Q posouvá kameru nahoru
    - E posouvá kameru dolů
    - A posouvá kameru doleva
    - D posouvá kameru doprava
    Kamera se neustále dívá na střed (0, 0, 0).

    Parametry:
    - camera_pos: aktuální pozice kamery ve 3D prostoru
    - speed: rychlost pohybu kamery
    """
    keys = pygame.key.get_pressed()

    # Spočítáme vektor směrem ze současné pozice kamery k bodu (0, 0, 0)
    dir_to_center = [-camera_pos[0], -camera_pos[1], -camera_pos[2]]
    # Vypočteme délku vektoru (euclidovská norma)
    length = math.sqrt(sum(d * d for d in dir_to_center))
    # Normalizujeme vektor, aby měl jednotkovou délku
    norm_dir = [d / length for d in dir_to_center] if length != 0 else [0, 0, 0]

    # Pohyb vpřed a vzad podél směru ke středu
    if keys[pygame.K_w]:
        camera_pos = [camera_pos[i] + norm_dir[i] * speed for i in range(3)]
    if keys[pygame.K_s]:
        camera_pos = [camera_pos[i] - norm_dir[i] * speed for i in range(3)]

    # Pohyb nahoru a dolů podél osy Y
    if keys[pygame.K_q]:
        camera_pos[1] += speed
    if keys[pygame.K_e]:
        camera_pos[1] -= speed

    # Pohyb doleva a doprava podél osy X
    if keys[pygame.K_a]:
        camera_pos[0] += speed
    if keys[pygame.K_d]:
        camera_pos[0] -= speed

    return camera_pos


def render_text(x, y, text_string, font_name="Arial", font_size=18):
    """
    Vykreslí text pomocí OpenGL.
    Text je zobrazen bílou barvou na černém pozadí.
    Pygame vytváří textový povrch, který následně vykreslíme pomocí glDrawPixels.

    Parametry:
    - x, y: pozice v okně (v pixelech; počátek v levém dolním rohu)
    - text_string: textový řetězec k zobrazení
    - font_name, font_size: vlastnosti písma použitého pro vykreslení textu
    """
    text_color = (255, 255, 255)         # Bílá barva textu
    background_color = (0, 0, 0)           # Černé pozadí

    font = pygame.font.SysFont(font_name, font_size)
    text_surface = font.render(text_string, True, text_color, background_color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)

    # Nastavíme pozici, kde se má text vykreslit. glWindowPos2d počítá s levým dolním rohem.
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def render_scene(model_list):
    """
    Vykreslí 3D scénu voláním display listu obsahujícího model.
    """
    glCallList(model_list)


def render_camera_coordinates(camera_pos, display_size):
    """
    Vykreslí aktuální souřadnice kamery jako textový overlay v levém horním rohu okna.
    """
    text = f"Camera: x={camera_pos[0]:.2f}, y={camera_pos[1]:.2f}, z={camera_pos[2]:.2f}"
    render_text(10, display_size[1] - 30, text)


def initialize():
    """
    Inicializuje Pygame, OpenGL a nastaví perspektivu.
    Nastavení OpenGL zahrnuje povolení depth testu a back face culling,
    což umožňuje vykreslit pouze viditelné části modelu.
    """
    pygame.init()
    display_size = (800, 600)
    pygame.display.set_mode(display_size, DOUBLEBUF | OPENGL)
    pygame.font.init()  # Inicializace písma pro vykreslování textu

    # Povolení depth testu, aby OpenGL dokázalo správně řešit překrývání objektů
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)

    # Povolení culling (skrytí zadních ploch modelu)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)

    # Nastavení clear color na tmavě šedou, která zlepší kontrast vykresleného modelu
    glClearColor(0.1, 0.1, 0.1, 1.0)

    # Nastavení viewportu odpovídajícího velikosti okna
    glViewport(0, 0, display_size[0], display_size[1])

    # Nastavíme projekční matici pro perspektivní zobrazení
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, display_size[0] / display_size[1], 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)

    return display_size


def main():
    """
    Hlavní funkce programu.
    - Inicializuje prostředí a OpenGL nastavení.
    - Načte 3D model ze souboru OBJ a převede ho do display listu.
    - Spouští hlavní smyčku, kde aktualizuje pozici kamery,
      vykresluje scénu a zobrazuje text s informacemi o kameře.
    """
    display_size = initialize()

    # Parametry pro perspektivu
    fov = 45           # Zorné pole (field of view)
    near_val = 0.1     # Near clipping plane: objekty blíže než 0.1 jednotky budou oříznuty
    far_val = 500.0    # Far clipping plane: objekty dále než 500 jednotek nebudou vykresleny

    # Nastavení perspektivy s upravitelnými clipping planes
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, display_size[0] / display_size[1], near_val, far_val)
    glMatrixMode(GL_MODELVIEW)

    # Počáteční pozice kamery, umístěná podél osy Z
    camera_pos = [0, 0, 50]

    # Načteme model z OBJ souboru a vytvoříme z něj display list
    vertices, faces = load_obj("model.obj")
    model_list = compile_display_list(vertices, faces)

    # Nastavíme režim vykreslování na drátový model (wireframe)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    # Hodiny pro řízení snímkové frekvence
    clock = pygame.time.Clock()
    running = True
    while running:
        # Smyčka zpracování událostí, např. zavření okna
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Aktualizace pozice kamery podle stisknutých kláves
        camera_pos = update_camera(camera_pos, speed=0.5)

        # Vyčistíme color a depth buffer, aby se zobrazil nový snímek
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Nastavení kamery: pozice kamery, bod, na který se dívá (střed scény) a směr "nahoru"
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  0, 0, 0,
                  0, 1, 0)

        # Vykreslíme model a text s informacemi o kameře
        render_scene(model_list)
        render_camera_coordinates(camera_pos, display_size)

        # Vykreslíme obsah na obrazovku a omezíme snímkovou frekvenci na 60 FPS
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()