# GLB Asset Validator & Batch Exporter (Blender `bpy`)

[![Blender 4.0+](https://img.shields.io/badge/Blender-4.0%2B-orange?logo=blender)](https://www.blender.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A lightweight, production-grade Blender 4.0+ pipeline add-on that audits mesh hygiene and automates per-asset `.glb` (glTF binary) batch exporting for real-time 3D engines (Unreal Engine 5, Unity, Godot, and WebGL/Three.js).

---

## 🎯 Features

- **Pre-Export Scene Hygiene Checks:**
  - **Unapplied Transforms:** Flags meshes with unapplied scale (non-`1.0`) or rotation (non-`0.0`) to avoid scaling bugs in real-time game engines.
  - **Missing UV Maps:** Identifies meshes lacking UV channels required for PBR texturing and lightmapping.
  - **Topology Audit via `bmesh`:**
    - Detects **Non-Manifold Edges** (open boundaries, internal faces, or wire edges).
    - Detects **N-gons** (faces with 5 or more vertices) to ensure clean triangulation and shading fidelity.
- **Interactive Viewport Diagnosis:**
  - Lists every flagged object with its specific defect in the N-Panel (`View3D > Sidebar > Pipeline`).
  - One-click viewport selection and focus to quickly isolate and fix problematic assets.
- **Batch `.glb` Exporter:**
  - Exports each mesh in the active collection as an individual `.glb` file.
  - Automatically handles coordinate conversion, normals, vertex colors/texcoords, and PBR materials.
  - Safely auto-creates the destination directory if it doesn't already exist.

---

## 📦 Installation

1. Download [`glb_asset_validator.py`](glb_asset_validator.py).
2. Open Blender (**4.0 or newer**).
3. Navigate to **Edit > Preferences > Add-ons**.
4. Click the top-right dropdown / **Install...** (or arrow icon) and select `glb_asset_validator.py`.
5. Check the box to enable **Import-Export: GLB Asset Validator & Batch Exporter**.
6. In the 3D Viewport, press `N` to open the sidebar, then click the **Pipeline** tab.

---

## 🚀 Usage Guide

### 1. Validate Active Collection
1. Organize the assets you want to export into a Blender collection.
2. Select the collection in the **Outliner** to make it active.
3. In the 3D Viewport sidebar (`N` panel), open **Pipeline > GLB Asset Validator**.
4. Click **Validate Active Collection**.
5. If issues exist, they will be listed with an inspect button:
   - Click the **Select** icon next to any issue to isolate and select that mesh in the viewport.

### 2. Batch Export
1. Enter your target output folder path in the **Output** field (e.g., `//exports/` or an absolute path like `/Users/name/Projects/Exports`).
2. Click **Batch Export Collection to GLB**.
3. Each mesh will be exported individually with its object name (e.g., `Hero_Sword.glb`, `Rock_01.glb`).

---

## 🔍 Validation Rules

| Check | Failure Condition | Why It Matters |
| :--- | :--- | :--- |
| **Scale** | `(scale - (1, 1, 1)).length > 0.0001` | Non-uniform or unapplied scale breaks physics colliders and instanced transforms in game engines. |
| **Rotation** | `rotation_euler.length > 0.0001` | Unapplied rotation leads to incorrect orientation and pivot offsets on engine import. |
| **UV Map** | `len(obj.data.uv_layers) == 0` | Meshes without UV coordinates cannot render texture maps or baked lightmaps. |
| **Non-Manifold** | `edge.is_manifold == False` | Causes lighting artifacts, physics simulation failure, and 3D printing errors. |
| **N-gons** | `len(face.verts) > 4` | Unpredictable automated triangulation can produce bad shading, shading pinching, and deform glitches. |

---

## 🛠️ Technical Details

- **Blender API:** Blender Python API (`bpy`, `bmesh`, `mathutils`).
- **UI Category:** `VIEW_3D > UI > Pipeline`.
- **glTF Exporter Integration:** Leverages Blender's native `io_scene_gltf2` exporter operator (`bpy.ops.export_scene.gltf`).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
