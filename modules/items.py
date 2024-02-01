import os
import json
import shutil
import pathlib
import secrets

geyser_item_mapping = {
    "format_version": 1,
    "items": {
    }
}
item_textures = {
    "resource_pack_name": "tumera",
    "texture_name": "atlas.items",
    "texture_data": {
    }
}

def convert_predicates(berp, jerp, attachable_material):
    item_model_path = os.path.join(jerp, "assets", "minecraft", "models", "item")
    for root, dirs, files in os.walk(item_model_path):
        for file in files:
            model_path = os.path.join(root, file)
            model = json.load(open(model_path, 'r'))
            if "parent" not in model:
                continue
            if "overrides" in model:
                override_dict = model['overrides']
                for cmd in override_dict:
                    if "custom_model_data" not in cmd['predicate']:
                        continue
                    defined_item_name = "tumera_" + str(secrets.token_hex(4))
                    material = "minecraft:" + str(pathlib.Path(model_path).stem)
                    cmd_value = cmd['predicate']['custom_model_data']
                    add_to_geyser_mapping(defined_item_name, material, cmd_value)
                    overriden_model = cmd['model']
                    model_namespace = overriden_model.split(":")[0]
                    overriden_model_path = os.path.join(jerp, "assets", model_namespace, "models", overriden_model.split(":")[1]) + ".json"
                    overriden_model_data = json.load(open(overriden_model_path, 'r'))
                    handle_overriden_model(jerp, berp, defined_item_name, overriden_model_data, attachable_material)
    json.dump(geyser_item_mapping, open(os.path.join(berp, "geyser_item_mappings.json"), 'w'))
    json.dump(item_textures, open(os.path.join(berp, "textures", "item_texture.json"), 'w'))
    
def add_to_geyser_mapping(name, material, cmd_value):
    if material not in geyser_item_mapping['items']:
        geyser_item_mapping['items'][material] = []
    item_mapping = {
        "name": name,
        "allow_offhand": True,
        "icon": name,
        "custom_model_data": cmd_value
    }
    geyser_item_mapping['items'][material].append(item_mapping)
    
def add_to_bedrock_rp(name, texture_file_name):
    item_manifest = {
        "textures": [
            "textures/items/" + texture_file_name
        ]
    }
    item_textures['texture_data'][name] = item_manifest
    
def handle_overriden_model(jerp, berp, name, model_data, attachable_material):
    # Handle parented models
    # This way it will work even for stacked parented models (though I'm not sure who'd do that.)
    if "parent" in model_data and "textures" not in model_data and "overrides" not in model_data:
        model_namespace = model_data['parent'].split(":")[0]
        parented_model = os.path.join(jerp, "assets", model_namespace, "models", model_data['parent'].split(":")[1]) + ".json"
        handle_overriden_model(jerp, berp, name, json.load(open(parented_model, 'r')), attachable_material)
    parent_model = model_data['parent'].replace("minecraft:", "")
    if "block" in parent_model:
        # We ain't dealing with with block models.
        return
    overriden_texture = model_data['textures']['layer0']
    overriden_texture_path = os.path.join(jerp, "assets", overriden_texture.split(":")[0], "textures", overriden_texture.split(":")[1]) + ".png"
    shutil.copyfile(overriden_texture_path, os.path.join(berp, "textures", "items", pathlib.Path(overriden_texture_path).stem) + ".png")
    add_to_bedrock_rp(name, pathlib.Path(overriden_texture_path).stem)
    match(parent_model):
        case _:
            print("")
            