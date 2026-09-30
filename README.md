# Triangle Grid Renderer

A small Pygame and PyOpenGL prototype for a pannable grid of independently coloured, lit triangles.

## Run

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Use the arrow keys to pan and Escape to quit. The 80 by 60 cell grid extends beyond the initial window. Triangle geometry and RGB6 base colours are uploaded once; a separate normalized 8-bit vertex buffer carries per-triangle lighting and is smoothly animated on a subset of faces. The shaders target GLSL 1.40 for compatibility with OpenGL 3.1 systems.