# Pygame + OpenGL Triangle-Grid Renderer

## Goal

Build a small Python renderer using **Pygame + PyOpenGL**.

The renderer displays a potentially large, pannable grid of fixed-size rectangular cells. Each cell consists of two right-angled triangles.

The initial implementation should use modern OpenGL (VAOs/VBOs and GLSL shaders), not legacy `glBegin()`/`glEnd()` rendering.

Keep the first implementation deliberately small and understandable.

## Grid geometry

Each grid cell is:

- 32 pixels wide
- 16 pixels high
- composed of two right-angled triangles

Each cell has a 1-bit diagonal-direction flag selecting between:

```text
+----------------+       +----------------+
|              / |       | \              |
|           /    |       |    \           |
|        /       |       |       \        |
|     /          |       |          \     |
|  /             |       |             \  |
+----------------+       +----------------+
```

The geometry is fixed except that the diagonal direction may occasionally change.

The overall grid may be considerably larger than the window.

## Coordinate system and camera

Use pixel-like world coordinates:

- X increases to the right.
- Y increases downwards.
- Cell `(column,row)` starts at `(column * 32, row * 16)`.

The window is a viewport onto this larger world.

Maintain a camera position:

```python
camera_x
camera_y
```

Panning should change the camera/view transformation, not rebuild the geometry.

Use an **orthographic projection**. There is no perspective.

Eventually the renderer will have a quasi-isometric appearance, but screen/world mapping remains orthographic.

## Triangle base colours

Each triangle has its own static base RGB colour.

Each RGB component is logically 6 bits:

```text
R = 0..63
G = 0..63
B = 0..63
```

Base colours normally remain unchanged after the grid has been constructed.

## Lighting

Lighting is **per triangle**, not per vertex or per pixel.

Each triangle has a nominal lighting level in the range:

```text
1..16
```

Level 16 represents full brightness.

Allow level 0 internally as well, representing complete darkness.

The displayed colour is conceptually:

```text
display_colour = base_colour × brightness
```

where:

```text
brightness = lighting / 16
```

The multiplication should be performed by the GPU shader rather than recalculating base colours on the CPU.

Lighting may change rapidly and should support smooth transitions rather than visibly stepping through only 16 brightness levels.

It is therefore reasonable for the renderer to represent dynamic lighting internally with greater precision (for example an 8-bit 0..255 value), while the application's logical lighting levels remain 0..16.

Keep static base-colour data separate from dynamic lighting data so that lighting animation does not require rebuilding geometry or base colours.

## Depth

Although rendering is currently essentially 2D, allow vertices to acquire a Z coordinate.

Application-level depth can be represented as an 8-bit logical value:

```text
0..255
```

Use a conventional OpenGL framebuffer depth buffer; a 16-bit depth buffer is sufficient.

The depth buffer is needed only for subsequent rendering/visibility. The application will not need to read depth values back.

Request the depth buffer before creating the Pygame OpenGL window, e.g.:

```python
pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 16)
```

The initial background grid may all use the same Z value.

## Future texturing

The triangle faces will eventually support simple textures.

Requirements will be:

- 1:1 texel-to-screen-pixel mapping
- no perspective
- crisp pixel rendering
- `GL_NEAREST` filtering
- probably no mipmapping

Texture coordinates will interpolate normally across a triangle.

Do **not** complicate the initial implementation by adding unused UV attributes yet, but structure the renderer so that adding them later is straightforward.

## OpenGL architecture

Use modern OpenGL:

- VAO
- VBOs
- GLSL vertex shader
- GLSL fragment shader
- `glDrawArrays(GL_TRIANGLES, ...)` or an equivalently simple modern approach

Do not use legacy immediate-mode OpenGL.

The initial implementation should favour simplicity over aggressive optimisation.

The fixed geometry and base colours may live in static GPU buffers.

Dynamic per-triangle lighting should be stored separately so it can be changed efficiently without modifying static geometry/base-colour data.

A texture or other suitable GPU buffer may be used for the dynamic lighting values.

The renderer should ideally draw the complete background with a very small number of draw calls, preferably one.

OpenGL clipping may initially be relied upon for geometry outside the viewport. CPU-side visible-cell culling is unnecessary unless grid size later makes it worthwhile.

## Pygame responsibilities

Use Pygame for:

- OpenGL window/context creation
- event handling
- keyboard/mouse input
- timing
- buffer swapping
- later, possibly audio

Use OpenGL for rendering.

## First milestone

Create the smallest useful working prototype that:

1. Opens a Pygame/OpenGL window.
2. Creates a reasonably sized test grid larger than the window.
3. Generates the two triangles for every 32×16 cell.
4. Gives each triangle an independently chosen RGB6 base colour.
5. Supports both diagonal orientations.
6. Renders the grid using modern OpenGL.
7. Allows smooth camera panning with the cursor keys.
8. Implements per-triangle lighting in the shader.
9. Demonstrates smooth animated lighting on some triangles.
10. Creates a 16-bit depth buffer, even if meaningful depth differences are not yet used.
11. Maintains pixel-sharp geometry without antialiasing or filtering that would blur cell boundaries.

Keep the code well structured, but avoid building a large framework. The purpose of this milestone is to establish and understand the rendering architecture before adding foreground objects or texturing.