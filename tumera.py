# tumera - work-in-progress resource pack converter for Geyser
# usage: python3 tumera.py <path to resource pack>

# self note: don't let this be another unmaintainable mess of broken code please.

import os
import zipfile
import json
import shutil
import pathlib
import uuid

from modules import items

# Script config
bedrock_rp_dir = "converted"
working_dir = "temp"
attachable_material = "entity_alphatest_one_sided"
block_material = "alpha_test"

# Converted pack info
output_file = "converted.mcpack"
pack_name = ""
pack_description = ""

def load_pack(pack):
    global pack_name
    global pack_description
    packfile = zipfile.ZipFile(pack, 'r')
    if "pack.mcmeta" not in packfile.namelist():
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
    os.mkdir(os.path.join(rpdir, "models", "blocks"))
    lang_dir = os.path.join(rpdir, "texts")
    en_lang_file = f"pack.name = {pack_name}\npack.description = {pack_description}"
    lang_file = ["en_US"]
    open(os.path.join(lang_dir, "en_US.lang"), 'w').write(en_lang_file)
    open(os.path.join(lang_dir, "languages.json"), 'w').write(json.dumps(lang_file))

def convert():
    geyser_block_mapping = {
        "format_version": 1,
        "blocks": {
        }
    }
    terrain_textures = {
	    "resource_pack_name": "tumera",
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
    print("generating base geyser animation...")
    base_disable_animation = {
        "format_version": "1.8.0",
        "animations": {
          "animation.geyser_custom.disable": {
            "loop": True,
            "override_previous_animation": True,
            "bones": {
              "geyser_custom": {
                "scale": 0
              }
            }
          }
        }
    }
    open(os.path.join(bedrock_rp_dir, "animations", "disable.animations.json"), 'w').write(json.dumps(base_disable_animation))
    if os.path.isdir(item_model_path):
        print("converting item predicates...")
        items.convert_predicates(bedrock_rp_dir, jrp, attachable_material)

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