import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random


def load_obj(filename):
    """
    Loads a .obj file and returns a list of vertices and face indices.
    This simple parser expects the file to contain vertex (v) and face (f) definitions,
    without normals or texture coordinates.
    """
    vertices = []
    faces = []
    with open(filename, "r") as file:
        for line in file:
            if line.startswith("v "):  # Process vertex definitions
                parts = line.strip().split()
                vertex = list(map(float, parts[1:4]))
                vertices.append(vertex)
            elif line.startswith("f "):  # Process face definitions
                parts = line.strip().split()
                # Expect only indices (assuming CCW winding order)
                face = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                faces.append(face)
    return vertices, faces


def compile_display_list(vertices, faces):
    """
    Creates an OpenGL display list for the model.
    Each polygon is drawn using a color chosen from a curated palette of harmonious colors.
    Compiling the model into a display list speeds up rendering.
    """
    # Define a palette of harmonious, muted colors (RGB values in range 0.0 to 1.0)
    color_palette = [
        (0.70, 0.50, 0.30),  # warm earth tone
        (0.60, 0.55, 0.45),  # soft beige
        (0.65, 0.60, 0.50),  # muted olive
        (0.55, 0.55, 0.65),  # cool gray-blue
        (0.60, 0.70, 0.60)  # gentle green
    ]

    model_list = glGenLists(1)
    glNewList(model_list, GL_COMPILE)
    glBegin(GL_TRIANGLES)
    for face in faces:
        # Choose a random color from the palette for this polygon
        r, g, b = random.choice(color_palette)
        glColor3f(r, g, b)
        # If the face is already a triangle, draw it directly
        if len(face) == 3:
            for vertex_index in face:
                glVertex3fv(vertices[vertex_index])
        else:
            # If the face has more than three vertices, split it into triangles (triangle fan)
            for i in range(1, len(face) - 1):
                glVertex3fv(vertices[face[0]])
                glVertex3fv(vertices[face[i]])
                glVertex3fv(vertices[face[i + 1]])
    glEnd()
    glEndList()
    return model_list


def update_camera(camera_pos, speed=0.5):
    """
    Updates the camera position based on key presses:
    - W moves the camera forward (towards the origin)
    - S moves the camera backward (away from the origin)
    - A moves the camera upward
    - D moves the camera downward
    The camera always looks at the center (0, 0, 0).
    """
    keys = pygame.key.get_pressed()
    # Compute vector from the camera to the center (origin)
    dir_to_center = [-camera_pos[0], -camera_pos[1], -camera_pos[2]]
    length = math.sqrt(dir_to_center[0] ** 2 + dir_to_center[1] ** 2 + dir_to_center[2] ** 2)
    norm_dir = [d / length for d in dir_to_center] if length != 0 else [0, 0, 0]

    # Move forward and backward in the direction of the center
    if keys[pygame.K_w]:
        camera_pos = [camera_pos[i] + norm_dir[i] * speed for i in range(3)]
    if keys[pygame.K_s]:
        camera_pos = [camera_pos[i] - norm_dir[i] * speed for i in range(3)]

    # Move upward and downward along the Y-axis
    if keys[pygame.K_a]:
        camera_pos[1] += speed
    if keys[pygame.K_d]:
        camera_pos[1] -= speed

    return camera_pos


def render_text(x, y, text_string, font_name="Arial", font_size=18, text_color=(255, 255, 255, 255)):
    """
    Renders text using OpenGL. It utilizes pygame.font to generate a text surface,
    then converts it to a texture and renders it via glDrawPixels.

    Parameters:
    - x, y: Position in window (in pixels; origin is at the lower left)
    - text_string: The text to display
    - font_name, font_size: Font properties
    - text_color: Color of the text (RGBA)
    """
    font = pygame.font.SysFont(font_name, font_size)
    text_surface = font.render(text_string, True, text_color[:3])
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def render_scene(model_list):
    """
    Renders the 3D scene using the compiled display list.
    """
    glCallList(model_list)


def render_camera_coordinates(camera_pos, display_size):
    """
    Renders the current camera coordinates in the top-left corner.
    Converts coordinates to ensure correct display positioning.
    """
    text = f"Camera: x={camera_pos[0]:.2f}, y={camera_pos[1]:.2f}, z={camera_pos[2]:.2f}"
    render_text(10, display_size[1] - 30, text)


def initialize():
    """
    Inicializuje Pygame, nastaví okno a OpenGL perspektivu, povolí hloubkový test,
    rušení zadních stran (backface culling) a zapne osvětlení s nastaveným světlem.
    """
    pygame.init()
    display_size = (800, 600)
    pygame.display.set_mode(display_size, DOUBLEBUF | OPENGL)
    pygame.font.init()

    # Nastavení perspektivy s parametrizovanými klipovacími rovinami
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    fov = 45
    near_val = 0.1  # Blízká klipovací rovina
    far_val = 50.0  # Vzdálená klipovací rovina
    gluPerspective(fov, display_size[0] / display_size[1], near_val, far_val)
    glMatrixMode(GL_MODELVIEW)

    # Povolení hloubkového testu
    glEnable(GL_DEPTH_TEST)

    # Povolení rušení zadních stran
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)

    # Zapnutí osvětlení
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)  # Zapneme první světlo

    # Povolení použití vertex barev jako materiálových vlastností
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Nastavení parametrů světla
    ambient_light = [0.2, 0.2, 0.2, 1.0]  # Ambientní světlo (měkké ozáření)
    diffuse_light = [0.8, 0.8, 0.8, 1.0]  # Difuzní světlo (hlavní zdroj světla)
    specular_light = [1.0, 1.0, 1.0, 1.0]  # Spekulární složka světla (odlesky)
    light_position = [10.0, 10.0, 10.0, 1.0]  # Pozice světla ve scéně

    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse_light)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular_light)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)

    return display_size

def main():
    # Initialize and configure OpenGL
    display_size = initialize()

    # Starting camera position
    camera_pos = [0, 0, 10]

    # Load the model and compile it into a display list
    vertices, faces = load_obj("model.obj")
    model_list = compile_display_list(vertices, faces)

    # Set polygon mode to fill
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update camera position based on key presses
        camera_pos = update_camera(camera_pos, speed=0.5)

        # Clear the screen and set up the camera view
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
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