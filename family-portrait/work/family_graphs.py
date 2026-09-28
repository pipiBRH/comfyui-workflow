"""ComfyUI API graphs for the family portrait (Qwen-Image 2.1, official bf16 files)."""

UNET, CLIP, VAE = "qwen_image_2.1_bf16.safetensors", "qwen3vl_8b_bf16.safetensors", "qwen_image_2.1_vae_bf16.safetensors"

# reference photos, uploaded as fam_<n>.jpeg (n = 1..6, see work/photos/README.md)
REFS_NEW = ["fam_5.jpeg", "fam_4.jpeg", "fam_3.jpeg", "fam_2.jpeg", "fam_6.jpeg"]

IDS = ("<image1> is a close-up of the family: the father on the left, the little boy in the middle and the mother on the right; "
       "it is the main reference for their three faces. <image2> shows the mother on the left, the little boy in the middle and the "
       "father on the right sitting on the floor under a sheer curtain, as a second view of their faces. <image3> shows the father, "
       "the mother, the little boy and their dog sitting on the floor, and is the reference for the dog and for everyone's body "
       "proportions. <image4> shows the father and the mother standing, with the boy on the father's shoulders and the dog sitting "
       "in front, and is the reference for their heights and builds. <image5> shows the mother, the dog and the father, as a second "
       "view of the dog. Keep every person's facial identity, facial features, hairstyle, hair color, skin tone, body shape, build "
       "and height exactly as in the reference photos, and keep the dog's breed, size, fur colors and markings.")

SCENES = {
    "studio": ("Create a new formal full-length family portrait photograph of this family. " + IDS +
               " New outfits and pose: the father stands on the right in a tailored navy suit with a crisp white shirt, the mother "
               "stands on the left in an elegant floor-length champagne satin gown, and the little boy stands between them in a small "
               "navy suit with a white shirt and a red bow tie, holding both parents' hands; the dog sits at the boy's feet wearing a "
               "small red bow tie. Everyone smiles warmly and looks at the camera. The setting is a classic portrait studio with a "
               "hand-painted warm gray-brown canvas backdrop and a light oak wooden floor, lit by a large soft key light from the front "
               "left with gentle fill light, natural skin tones, crisp focus on every face, professional family portrait photography.",
               (1664, 2496)),
    "picnic": ("Create a new outdoor family portrait photograph of this family. " + IDS +
               " New outfits and pose: the family sits together on a cream picnic blanket on a green lawn; the father sits on the right "
               "in a light beige linen shirt and white trousers with one arm around the mother, the mother sits on the left in a flowing "
               "white cotton summer dress, the little boy sits on the mother's lap in a white shirt and beige shorts, and the dog lies on "
               "the blanket in front of them. Everyone smiles and looks at the camera. The setting is a sunny park in soft golden "
               "late-afternoon light, with leafy trees and softly blurred greenery behind them, warm natural light on their faces, crisp "
               "focus on every face, professional lifestyle family photography.",
               (2496, 1664)),
    "sofa": ("Create a new cozy family portrait photograph of this family at home. " + IDS +
             " New outfits and pose: the family sits close together on a cream linen sofa; the father sits on the right and the mother "
             "on the left, both in matching cream cable-knit sweaters and blue jeans, the little boy sits between them in a small cream "
             "cable-knit sweater and blue jeans, leaning on his mother, and the dog lies on the sofa beside the father with its head on "
             "his knee. Everyone smiles and looks at the camera. The setting is a bright Scandinavian living room with a large window "
             "with soft daylight, a wooden floor, a green potted plant and a warm floor lamp, crisp focus on every face, professional "
             "family portrait photography.",
             (2496, 1664)),
}

EDIT_STUDIO = ("Change the outfits and the background in <image1> and keep everything else. <image1> is the canvas: keep the father, "
               "the mother, the little boy and the dog in exactly the same positions, poses, expressions and framing, and keep every "
               "person's face, hairstyle, body shape and build exactly as they are. <image2> is a close-up of the same father on the "
               "left, the boy in the middle and the mother on the right, and serves only as an extra reference for their faces. Dress "
               "the father in a tailored navy suit with a white shirt, the mother in an elegant champagne satin dress, and the boy in a "
               "small navy suit with a white shirt and a red bow tie, and give the dog a small red bow tie in place of its lace collar. "
               "Replace the white studio room with a classic portrait studio: a hand-painted warm gray-brown canvas backdrop and a "
               "light oak wooden floor, with soft studio light that matches the original lighting.")


def graph(name, prompt, refs, seed, size=None, resolution=1024, steps=25):
    """size=None: edit mode, the canvas is refs[0]; size=(w, h): new picture on an empty canvas."""
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "QwenImage21Cache", "inputs": {"model": ["1", 0], "device": "auto", "dtype": "default"}},
        "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "qwen_image", "device": "default"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "20": {"class_type": "TextEncodeQwenImage21",
               "inputs": {"clip": ["3", 0], "prompt": prompt, "negative_prompt": "", "vae": ["4", 0], "resolution": resolution}},
        "40": {"class_type": "KSampler", "inputs": {"model": ["2", 0], "positive": ["20", 0], "negative": ["20", 1], "seed": seed,
                                                    "steps": steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "50": {"class_type": "VAEDecode", "inputs": {"samples": ["40", 0], "vae": ["4", 0]}},
        "60": {"class_type": "SaveImage", "inputs": {"images": ["50", 0], "filename_prefix": f"family/{name}"}},
    }
    for i, r in enumerate(refs, 1):
        g[str(10 + i)] = {"class_type": "LoadImage", "inputs": {"image": r}}
        g["20"]["inputs"][f"images.image_{i}"] = [str(10 + i), 0]
    if size:
        g["30"] = {"class_type": "EmptyLatentImage", "inputs": {"width": size[0], "height": size[1], "batch_size": 1}}
        g["40"]["inputs"]["latent_image"] = ["30", 0]
    else:
        g["40"]["inputs"]["latent_image"] = ["20", 2]
    return g

EDIT_STUDIO_1 = ("Change the outfits and the background in the image and keep everything else. Keep the father, the mother, the little "
                 "boy and the dog in exactly the same positions, poses, expressions and framing, and keep every person's face, hairstyle, "
                 "body shape and build exactly as they are. Dress the father in a tailored navy suit with a white shirt, the mother in an "
                 "elegant champagne satin dress, and the boy in a small navy suit with a white shirt and a red bow tie, and give the dog a "
                 "small red bow tie in place of its lace collar. Replace the white studio room with a classic portrait studio: a "
                 "hand-painted warm gray-brown canvas backdrop and a light oak wooden floor, with soft studio light that matches the "
                 "original lighting.")

EDIT_STUDIO_1 = ("Change the outfits and the background in the image and keep everything else. Keep the father, the mother, the little "
                 "boy and the dog in exactly the same positions, poses, expressions and framing, and keep every person's face, hairstyle, "
                 "body shape and build exactly as they are. Dress the father in a tailored navy suit with a white shirt, the mother in an "
                 "elegant champagne satin dress, and the boy in a small navy suit with a white shirt and a red bow tie, and give the dog a "
                 "small red bow tie in place of its lace collar. Replace the white studio room with a classic portrait studio: a "
                 "hand-painted warm gray-brown canvas backdrop and a light oak wooden floor, with soft studio light that matches the "
                 "original lighting.")

# one reference sheet per person (face close-up + full body of the same person side by side)
REFS_SOLO = ["ref_father.png", "ref_mother.png", "ref_boy.png", "ref_dog.png"]
IDS_SOLO = ("<image1> shows the father: his face up close on the left and his whole body on the right. <image2> shows the mother: "
            "her face up close on the left and her whole body on the right. <image3> shows their little boy: his face up close on the "
            "left and his whole body on the right. <image4> shows their dog from two angles. The photo contains exactly these three "
            "people and this one dog, each appearing once. Keep each person's face, facial features, hairstyle, hair color, skin tone, "
            "body shape, build and height exactly as in their reference image, and keep the dog's breed, size, fur colors and markings.")
for _k in list(SCENES):
    _p, _size = SCENES[_k]
    SCENES[_k + "_solo"] = (_p.replace(IDS, IDS_SOLO), _size)
