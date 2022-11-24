# Blender GLTF Node Inheritance Extension

Adds support for glTF 2.0 'EXT_transformation_inheritance' extension, which allows models to specify skeletal bones that do not inherit the transformations of their parent

Currently supports scale and rotation, but not translation (as there is no simple analogue in Blender armatures)

Requres GLTF importer/exporter plugin with a version >= 1.8.19 (packaged with Blender 3.1)
