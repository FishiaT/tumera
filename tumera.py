# tumera - work-in-progress resource pack converter for Geyser
# usage: python3 tumera.py <path to resource pack>

import os
import sys
import zipfile
import json
import shutil
import pathlib
import uuid

# Script config
bedrock_rp_dir = "converted"
working_dir = "temp"

# Converted pack info
output_file = "converted.mcpack"
pack_name = ""
pack_description = ""

def load_pack(pack):
    global pack_name
    global pack_description
    packfile = zipfile.ZipFile(pack, 'r')
    if not "pack.mcmeta" in packfile.namelist():
        print("error: not a valid java edition resource pack, aborting...")
        exit(1)
    pack_name = str(pathlib.Path(pack).stem).replace(" ", "_")
    pack_description = json.loads(packfile.read("pack.mcmeta").decode('utf-8'))['pack']['description']
    print("pack name: " + pack_name)
    print("pack description: " + pack_description)
    return packfile

def generate_base_rp(rpdir):
    header_uuid = str(uuid.uuid4())
    module_uuid = str(uuid.uuid4())
    manifest = {
	    "format_version": 2,
	    "header": {
		    "name": pack_name,
		    "description": pack_description,
		    "uuid": header_uuid,
		    "version": [1, 0, 0],
		    "min_engine_version": [1, 18, 3]
	    },
	    "modules": [
	    	{
	    		"type": "resources",
	    		"uuid": module_uuid,
	     		"version": [1, 0, 0]
	    	}
	    ]    
    }
    manifest_path = os.path.join(rpdir, "manifest.json")
    open(manifest_path, 'w').write(json.dumps(manifest))
    os.mkdir(os.path.join(rpdir, "attachables"))
    os.mkdir(os.path.join(rpdir, "animations"))
    os.mkdir(os.path.join(rpdir, "textures"))
    os.mkdir(os.path.join(rpdir, "textures", "items"))
    os.mkdir(os.path.join(rpdir, "textures", "blocks"))
    os.mkdir(os.path.join(rpdir, "texts"))
    os.mkdir(os.path.join(rpdir, "models"))
    lang_dir = os.path.join(rpdir, "texts")
    en_lang_file = f"pack.name = {pack_name}\npack.description = {pack_description}"
    lang_file = ["en_US"]
    open(os.path.join(lang_dir, "en_US.lang"), 'w').write(en_lang_file)
    open(os.path.join(lang_dir, "languages.json"), 'w').write(json.dumps(lang_file))

def convert():
    geyser_item_mapping = {
        "format_version": 1,
        "items": {
        }
    }
    geyser_block_mapping = {
        "format_version": 1,
        "blocks": {
        }
    }
    item_textures = {
        "resource_pack_name": pack_name,
        "texture_name": "atlas.items",
        "texture_data": {
        }
    }
    terrain_textures = {
	    "resource_pack_name": pack_name,
	    "texture_name": "atlas.terrain",
	    "padding": 8,
	    "num_mip_levels": 4,
	    "texture_data": {
	    }
    }
    jrp = os.path.join(working_dir, "pack")
    lang_dir = os.path.join(bedrock_rp_dir, "texts")
    item_model_path = os.path.join(jrp, "assets", "minecraft", "models", "item")
    blockstate_path = os.path.join(jrp, "assets", "minecraft", "blockstates")
    if os.path.isdir(item_model_path):
        print("converting item predicates...")
        current_index = 1
        for root, dirs, files in os.walk(item_model_path):
            for file in files:
                model_path = os.path.join(root, file)
                model_data = json.load(open(model_path, 'r'))
                print("processing: " + model_path)
                if not "parent" in model_data:
                    # probably custom 3D model, or invalid JSON
                    continue
                if "overrides" in model_data:
                    override_dict = model_data['overrides']
                    for i in override_dict:
                        if not "custom_model_data" in i['predicate']:
                            continue
                        material_name = "minecraft:" + str(pathlib.Path(model_path).stem)
                        if not material_name in geyser_item_mapping['items']:
                            geyser_item_mapping['items'][material_name] = []
                        defined_item_name = "tumera_item_" + str(current_index)
                        item_mapping = {
                            "name": defined_item_name,
                            "allow_offhand": True,
                            "icon": defined_item_name,
                            "custom_model_data": i['predicate']['custom_model_data']
                        }
                        geyser_item_mapping['items'][material_name].append(item_mapping)
                        overriden_model_id = i['model']
                        namespace = ""
                        if not ":" in overriden_model_id:
                            namespace = "minecraft"
                        else:
                            namespace = overriden_model_id.split(":")[0]
                        overriden_model_path = str(os.path.join(jrp, "assets", namespace, "models", overriden_model_id.split(":")[1]) + ".json").replace("/", "\\")
                        overriden_model = json.load(open(overriden_model_path, 'r'))
                        if "textures" in overriden_model:
                            overriden_texture = overriden_model['textures']['layer0']
                            tex_namespace = overriden_texture.split(":")[0]
                            tex_file = overriden_texture.split(":")[1]
                            texture_path = str(os.path.join(jrp, "assets", tex_namespace, "textures", tex_file) + ".png").replace("/", "\\")
                            shutil.copyfile(texture_path, os.path.join(bedrock_rp_dir, "textures", "items", pathlib.Path(texture_path).stem) + ".png")
                            item_manifest = {
                                "textures": [
                                    "textures/items/" + pathlib.Path(texture_path).stem
                                ]
                            }
                            item_textures['texture_data'][defined_item_name] = item_manifest
                        elif "parent" in overriden_model and not "textures" in overriden_model and not "overrides" in overriden_model:  
                            print("todo: handle parented models: " + overriden_model_path)
                        lang_append = "\nitem." + pack_name + ":" + defined_item_name + ".name=" + defined_item_name
                        open(os.path.join(lang_dir, "en_US.lang"), 'a').write(lang_append)
                        current_index += 1
    if os.path.isdir(blockstate_path):
        print("converting blockstate overrides...")
        current_index = 1
        for root, dirs, files in os.walk(blockstate_path):
            for file in files:
                blockstate_path = os.path.join(root, file)
                blockstate_data = json.load(open(blockstate_path, 'r'))
                print("processing: " + blockstate_path)
                for state in blockstate_data['variants']:
                    state_data = blockstate_data['variants'][state]
                    for state_override in state_data:
                        model = state_override['model']
                        if "minecraft:block/" in model:
                            # probably vanilla
                            continue
                        base_block_name = "minecraft:" + str(pathlib.Path(blockstate_path).stem)
                        if not base_block_name in geyser_block_mapping['blocks']:
                            geyser_block_mapping['blocks'][base_block_name] = {
                                "name": base_block_name.replace("minecraft:", ""),
                                "geometry": "geometry.cube",
                                "included_in_creative_inventory": False,
                                "only_override_states": True,
                                "place_air": True,
                                "state_overrides": {
                                }
                            }
                        defined_block_name = "tumera_block_" + str(current_index)
                        state_override_mapping = {
                            "name": defined_block_name,
                            "display_name": defined_block_name,
                            "geometry": "geometry.cube",
                            "material_instances": {
                                "*": {
                                    "texture": defined_block_name,
                                    "render_method": "alpha_test",
                                    "face_dimming": True,
                                    "ambient_occlusion": True
                                }
                            }
                        }
                        geyser_block_mapping['blocks'][base_block_name]['state_overrides'][state] = state_override_mapping
                        current_index += 1
    open(os.path.join(bedrock_rp_dir, "geyser_item_mappings.json"), 'w').write(json.dumps(geyser_item_mapping))
    open(os.path.join(bedrock_rp_dir, "geyser_block_mappings.json"), 'w').write(json.dumps(geyser_block_mapping))
    open(os.path.join(bedrock_rp_dir, "textures", "item_texture.json"), 'w').write(json.dumps(item_textures))

def main(pack):
    print("tumera - 1.0\nbased on examples provided by ofunny & GeyserMC\n")
    print("pack: " + pack)
    print("output: " + output_file)
    packfile = load_pack(pack)
    print("\nstarting conversion...")
    if not os.path.isdir(bedrock_rp_dir):
        os.mkdir(bedrock_rp_dir)
    elif os.path.isdir(bedrock_rp_dir):
        shutil.rmtree(bedrock_rp_dir)
        os.mkdir(bedrock_rp_dir)
    if not os.path.isdir(working_dir):
        os.mkdir(working_dir)
    elif os.path.isdir(working_dir):
        shutil.rmtree(working_dir)
        os.mkdir(working_dir)
    print("-> unzipping java resource pack...")
    packfile.extractall(os.path.join(working_dir, "pack"))
    print("-> generating base bedrock resource pack...")
    generate_base_rp(bedrock_rp_dir)
    print("-> performing conversion...")
    convert()
    print("-> packing converted pack...")
    print("done!")

if __name__ == '__main__':
    try:
        resource_pack = sys.argv[1]
    except IndexError:
        print("error: a valid java edition resource pack must be specified.")
        exit(1)
    main(resource_pack)