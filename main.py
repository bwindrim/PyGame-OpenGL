"""Render a pannable, per-triangle-lit grid with Pygame and OpenGL."""

import math
import sys

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader


WINDOW_SIZE = (640, 480)
CELL_SIZE = (32, 16)
GRID_SIZE = (80, 60)
PAN_SPEED = 600.0

VERTEX_SHADER = """#version 140
in vec3 in_position;
in vec3 in_base_colour;
in float in_lighting;

uniform vec2 camera_position;
uniform vec2 viewport_size;

out vec3 base_colour;
out float lighting;

void main() {
    vec2 screen_position = in_position.xy - camera_position;
    vec2 clip_position = (screen_position / viewport_size) * 2.0 - 1.0;
    clip_position.y = -clip_position.y;
    gl_Position = vec4(clip_position, in_position.z, 1.0);
    base_colour = in_base_colour;
    lighting = in_lighting;
}
"""

FRAGMENT_SHADER = """#version 140
in vec3 base_colour;
in float lighting;
out vec4 fragment_colour;

void main() {
    fragment_colour = vec4(base_colour * lighting, 1.0);
}
"""


def make_grid() -> tuple:
    """Build triangle vertices, base light levels, animation flags, and phases."""
    rng = np.random.default_rng(2026)
    triangles = []
    levels = []

    def add_triangle(
        points: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]
    ) -> None:
        """Append one triangle with its own RGB6 colour and light level."""
        colour = rng.integers(0, 64, size=3).astype(np.float32) / 63.0
        for x, y in points:
            triangles.append((x, y, 0.0, *colour))
        levels.append(int(rng.integers(4, 17)))

    cell_width, cell_height = CELL_SIZE
    for row in range(GRID_SIZE[1]):
        for column in range(GRID_SIZE[0]):
            left = column * cell_width
            top = row * cell_height
            top_left = (left, top)
            top_right = (left + cell_width, top)
            bottom_left = (left, top + cell_height)
            bottom_right = (left + cell_width, top + cell_height)

            if (column + row) % 2 == 0:
                add_triangle((top_left, top_right, bottom_left))
                add_triangle((top_right, bottom_right, bottom_left))
            else:
                add_triangle((top_left, top_right, bottom_right))
                add_triangle((top_left, bottom_right, bottom_left))

    vertices = np.asarray(triangles, dtype=np.float32)
    base_levels = np.asarray(levels, dtype=np.float32)
    animated = rng.random(len(base_levels)) < 0.06
    phases = rng.uniform(0.0, math.tau, size=len(base_levels)).astype(np.float32)
    return vertices, base_levels, animated, phases


def create_shader_program() -> int:
    """Compile and link the vertex and fragment shaders."""
    program = glCreateProgram()
    vertex_shader = compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
    fragment_shader = compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glBindAttribLocation(program, 0, "in_position")
    glBindAttribLocation(program, 1, "in_base_colour")
    glBindAttribLocation(program, 2, "in_lighting")
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        message = glGetProgramInfoLog(program).decode("utf-8", "replace")
        raise RuntimeError(f"Shader link failed: {message}")
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    return program


def main() -> int:
    """Create the OpenGL window and run the interactive grid renderer."""
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
    pygame.display.set_mode(WINDOW_SIZE, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    pygame.display.set_caption("Pygame + OpenGL Triangle Grid")

    glDisable(GL_MULTISAMPLE)
    glDisable(GL_BLEND)
    glDisable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glClearDepth(1.0)
    glClearColor(0.055, 0.065, 0.075, 1.0)

    vertices, base_levels, animated, phases = make_grid()
    triangle_count = len(base_levels)
    vertex_count = len(vertices)
    lighting_data = np.rint(base_levels / 16.0 * 255.0).astype(np.uint8)
    vertex_lighting = np.repeat(lighting_data, 3)

    program = create_shader_program()
    vao = glGenVertexArrays(1)
    vertex_buffer = glGenBuffers(1)
    glBindVertexArray(vao)

    glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    stride = 6 * vertices.itemsize
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))

    lighting_buffer = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, lighting_buffer)
    glBufferData(GL_ARRAY_BUFFER, vertex_lighting.nbytes, vertex_lighting, GL_DYNAMIC_DRAW)
    glEnableVertexAttribArray(2)
    glVertexAttribPointer(2, 1, GL_UNSIGNED_BYTE, GL_TRUE, 0, ctypes.c_void_p(0))

    glUseProgram(program)
    camera_uniform = glGetUniformLocation(program, "camera_position")
    viewport_uniform = glGetUniformLocation(program, "viewport_size")

    clock = pygame.time.Clock()
    camera_x = 0.0
    camera_y = 0.0
    world_width = GRID_SIZE[0] * CELL_SIZE[0]
    world_height = GRID_SIZE[1] * CELL_SIZE[1]
    running = True

    while running:
        # Limit long frame times so a pause does not cause a large camera jump.
        delta_time = min(clock.tick(120) / 1000.0, 0.05)

        # Handle window events, including resize and requests to quit.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                glViewport(0, 0, *event.size)

        # Move the camera from the currently held arrow keys.
        keys = pygame.key.get_pressed()
        horizontal = float(keys[pygame.K_RIGHT]) - float(keys[pygame.K_LEFT])
        vertical = float(keys[pygame.K_DOWN]) - float(keys[pygame.K_UP])
        camera_x += horizontal * PAN_SPEED * delta_time
        camera_y += vertical * PAN_SPEED * delta_time

        # Keep the viewport inside the grid, including after a window resize.
        viewport_width, viewport_height = pygame.display.get_window_size()
        camera_x = min(max(camera_x, 0.0), max(0.0, world_width - viewport_width))
        camera_y = min(max(camera_y, 0.0), max(0.0, world_height - viewport_height))

        # Animate selected triangle lights and upload the updated 8-bit values.
        elapsed = pygame.time.get_ticks() / 1000.0
        levels = base_levels.copy()
        levels[animated] = 4.0 + 12.0 * (
            0.5 + 0.5 * np.sin(elapsed * 2.0 + phases[animated])
        )
        lighting_data = np.rint(levels / 16.0 * 255.0).astype(np.uint8)
        vertex_lighting = np.repeat(lighting_data, 3)
        glBindBuffer(GL_ARRAY_BUFFER, lighting_buffer)
        glBufferSubData(GL_ARRAY_BUFFER, 0, vertex_lighting.nbytes, vertex_lighting)

        # Clear the frame, apply the camera uniforms, draw the grid, and present.
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(program)
        glUniform2f(camera_uniform, camera_x, camera_y)
        glUniform2f(viewport_uniform, viewport_width, viewport_height)
        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLES, 0, vertex_count)
        pygame.display.flip()

    glDeleteBuffers(1, [vertex_buffer])
    glDeleteBuffers(1, [lighting_buffer])
    glDeleteVertexArrays(1, [vao])
    glDeleteProgram(program)
    pygame.quit()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        pygame.quit()
        raise error