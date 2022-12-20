bl_info = {
        "name": "glTF node inheritance extensions",
        "description": "Add support for explicitly exporting node TSR inheritance properties in glTF files",
        "author": "NL Alterman",
        "version": (1, 0),
        "blender": (3, 1, 0),
        "location": "",
        "warning": "", # used for warning icon and text in add-ons panel
        "wiki_url": "",
        "tracker_url": "https://github.com/naclomi/blender-gltf-inheritance-addon/issues",
        "support": "COMMUNITY",
        "category": "Import-Export"
        }

import bpy

if locals().get('loaded'):
    loaded = False
    from importlib import reload
    from sys import modules

    modules[__name__] = reload(modules[__name__])
    for name, module in modules.items():
        if name.startswith(f"{__package__}."):
            globals()[name] = reload(module)
    del reload, modules

glTF_extension_name = "EXT_node_tsr_inheritance"

class glTF2ImportUserExtension:
    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        from io_scene_gltf2.blender.imp.gltf2_blender_vnode import VNode
        self.extensions = [Extension(name=glTF_extension_name, extension={}, required=True)]
        self.VNode = VNode
        self.supported_inheritances = {"translation", "scale", "rotation"}

    def gather_import_scene_after_nodes_hook(self, gltf_scene, blender_scene, gltf):
        for arma in gltf.vnodes.values():
            if arma.is_arma:
                blender_arma = arma.blender_object

                # Find all bones for this arma
                bone_ids = []
                def visit(idx):  # Depth-first walk
                    if gltf.vnodes[idx].type == self.VNode.Bone:
                        bone_ids.append(idx)
                        for child in gltf.vnodes[idx].children:
                            visit(child)
                for child in arma.children:
                    visit(child)

                bpy.ops.object.mode_set(mode="OBJECT")

                for idx in bone_ids:
                    node = gltf.data.nodes[idx]
                    vnode = gltf.vnodes[idx]
                    if node.extensions is not None:
                        if glTF_extension_name in node.extensions:
                            inheritances = node.extensions[glTF_extension_name]
                            pbone = blender_arma.pose.bones[vnode.blender_bone_name]
                            if not inheritances.get("rotation", True):
                                pbone.bone.use_inherit_rotation = False
                            if not inheritances.get("scale", True):
                                pbone.bone.inherit_scale = "NONE"
                            if not inheritances.get("translation", True):
                                raise Exception("Add-on does not support inheritance property 'translation':false")
                            leftovers = inheritances.keys() - self.supported_inheritances
                            if len(leftovers) > 0:
                                raise Exception("Add-on does not support inheritance properties: {:}".format(",".join(leftovers)))

class glTF2ExportUserExtension:
    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.changed_values = []


    def preserve_value(self, object, attr):
        self.changed_values.append((object, attr, getattr(object, attr)))

    def gather_gltf_extensions_hook(self, export_settings, gltf):
        # This is the last hook that runs, where we want to reset
        # any blender object values we temporarily changed
        # TODO: It seems undocumented, make sure it's ok to use
        bpy.ops.object.mode_set(mode="OBJECT")
        for object, attr, value in self.changed_values:
            setattr(object, attr, value)

    def gather_joint_hook(self, gltf2_node, blender_bone, export_settings):
        bpy.ops.object.mode_set(mode="OBJECT")

        inherit_rotation = blender_bone.bone.use_inherit_rotation
        inherit_scale = blender_bone.bone.inherit_scale != "NONE"
        if not inherit_rotation or not inherit_scale:
            ext_props = {}
            if not inherit_rotation:
                ext_props["rotation"] = False

            if not inherit_scale:
                ext_props["scale"] = False

            # Temporarily change all inheritance properties to true, to
            # prevent the vanilla glTF exporter plugin code from baking the
            # inheritance properties directly into the animation data
            # TODO: double-check this actually produces the desired results
            self.preserve_value(blender_bone.bone, "use_inherit_rotation")
            blender_bone.bone.use_inherit_rotation = True
            self.preserve_value(blender_bone.bone, "inherit_scale")
            blender_bone.bone.inherit_scale = "FULL"

            gltf2_node.extensions[glTF_extension_name] = self.Extension(
                name=glTF_extension_name,
                extension=ext_props,
                required=True
            )

def register():
    from io_scene_gltf2 import bl_info as base_info
    required_ver = (1,8,19)
    if base_info["version"] < required_ver:
        ver_str = ".".join(str(n) for n in required_ver)
        raise Exception("This addon requires the official glTF2 extension with version >= {:}".format(ver_str))

def unregister():
    pass

if __name__ == '__main__':
    register()

