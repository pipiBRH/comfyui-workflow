"""20 new family portraits with a DIFFERENT POSE each (plus new outfits and settings).

Same identity sources as option A: photo 3 (whole family + dog) and photo 5 (faces up close); variant "b" also adds
photo 2 (standing, shows heights and builds). The pose, outfits and setting are new; faces and bodies must stay.
"""

REFS = {"a": ["fam_3.jpeg", "fam_5.jpeg"], "b": ["fam_3.jpeg", "fam_5.jpeg", "fam_2.jpeg"]}
VARIANT = "a"          # set by auto.py --variant

HEAD = {
    "a": ("Create a new photo of the family in <image1> with a new pose, new outfits and a new setting. <image1> is the main "
          "reference: take the father, the mother, the little boy and the dog from it, and keep every person's face, facial "
          "features, hairstyle, hair color, skin tone, body shape, build and height exactly as they are, and keep the dog's breed, "
          "size, fur colors and markings. <image2> is a close-up of the same father on the left, the boy in the middle and the "
          "mother on the right, and serves only as an extra reference for their faces. "),
    "b": ("Create a new photo of the family in <image1> with a new pose, new outfits and a new setting. <image1> is the main "
          "reference: take the father, the mother, the little boy and the dog from it, and keep every person's face, facial "
          "features, hairstyle, hair color, skin tone, body shape, build and height exactly as they are, and keep the dog's breed, "
          "size, fur colors and markings. <image2> is a close-up of the same father on the left, the boy in the middle and the "
          "mother on the right, and serves only as an extra reference for their faces. <image3> shows the same father and mother "
          "standing, with the boy on the father's shoulders and the dog in front, and serves only as a reference for their "
          "heights and builds. "),
}
ONCE = ("The result shows exactly three people, the father, the mother and the boy, plus the dog, each appearing only once, "
        "with every face clearly visible and turned toward the camera. ")

# key, file name, pose, father, mother, boy, dog, setting, light
THEMES = [
    ("P01", "手牽手站一排",
     "the family stands side by side in a row holding hands, the boy in the middle holding both parents' hands, the dog sitting in front of the boy",
     "a charcoal suit with a white shirt", "an emerald green satin midi dress", "a white shirt with charcoal shorts, suspenders and a bow tie",
     "an emerald bow tie", "a classic portrait studio with a dark charcoal hand-painted canvas backdrop and a wooden floor", "soft studio key light"),
    ("P02", "騎在爸爸肩上",
     "the father stands and carries the boy on his shoulders, holding the boy's hands, the mother stands close beside the father with her arm around his waist, and the dog sits at their feet",
     "a light blue denim shirt and khaki chinos", "a white eyelet summer dress", "a yellow T-shirt and denim shorts",
     "a yellow bandana", "a sunny park with a wide green lawn and big leafy trees behind them", "soft golden afternoon light"),
    ("P03", "牽手走向鏡頭",
     "the family walks toward the camera holding hands, the boy between his parents mid-step, and the dog trots beside the mother on a leash",
     "a navy knit sweater and gray trousers", "a camel coat over a cream dress", "a small red wool coat and dark trousers",
     "a red bandana", "a tree-lined park path in autumn covered with golden fallen leaves", "soft autumn afternoon light"),
    ("P04", "趴著撐下巴",
     "the family lies on their stomachs side by side on a large blanket, propped on their elbows with their chins resting in their hands, the boy in the middle, and the dog lies next to the boy",
     "a white linen shirt and light jeans", "a white linen blouse and light jeans", "a small white linen shirt and light jeans",
     "a collar of white daisies", "a meadow full of small wildflowers, with the blanket spread on the grass", "soft morning light"),
    ("P05", "爸爸把小孩舉高高",
     "the father lifts the boy high in the air with both hands, the boy laughing with his arms spread like an airplane, the mother stands beside them clapping and laughing, and the dog jumps up happily next to them",
     "a white linen shirt with rolled sleeves and beige shorts", "a light blue maxi dress", "a white T-shirt and blue shorts",
     "a blue bandana", "a sunny beach with gentle waves", "soft bright morning light"),
    ("P06", "沙發上窩在一起",
     "the father sits on a sofa with the boy on his lap, the mother sits on the sofa armrest beside the father with her arm around his shoulders, and the dog sits on the sofa next to the father",
     "an olive green knit sweater and dark jeans", "a cream turtleneck and a plaid skirt", "a mustard sweater and jeans",
     "a green collar", "a modern living room with a gray sofa, plants and a large window", "soft window light"),
    ("P07", "媽媽背小孩",
     "the mother kneels on the grass with the boy riding piggyback on her back, his arms around her neck and his cheek next to hers, the father kneels beside them with one arm around the mother, and the dog lies in front of them",
     "a light gray shirt and white trousers", "a lilac cotton dress", "a white shirt and mint green shorts",
     "a mint green bandana", "a spring garden full of blooming tulips", "soft spring daylight"),
    ("P08", "爸爸從後面抱住",
     "the father stands and hugs the mother from behind, the mother holds the boy on her hip and the boy hugs her neck, all three smiling at the camera, and the dog sits at the mother's feet",
     "a white shirt and black trousers", "a black off-shoulder dress", "a white shirt and black shorts",
     "a black bow tie", "a rooftop terrace with a city skyline softly blurred behind them", "warm golden-hour light"),
    ("P09", "公園長椅",
     "the father and the mother sit on a wooden park bench, the boy stands on the bench between them with his arms around both parents' shoulders, and the dog sits on the ground in front of the bench",
     "a navy polo shirt and white chinos", "a red gingham dress", "a navy polo shirt and white shorts",
     "a red gingham bandana", "a green park with a wooden bench under tall trees", "soft daylight"),
    ("P10", "坐在石階上",
     "the family sits on wide stone steps at different heights: the father on the top step, the mother one step below him leaning back against his knees, the boy on the lowest step in front of the mother, and the dog lies on the step beside the boy",
     "a beige linen suit", "a white blouse and a long terracotta skirt", "a white shirt and beige shorts",
     "a terracotta bandana", "an old European town street with stone buildings and flower boxes", "soft daylight"),
    ("P11", "一起抱狗狗",
     "all three crouch down around the dog and hug it together, the boy hugging the dog's neck in the middle, the parents on either side with their hands on the dog, all faces close together",
     "a gray T-shirt and jeans", "a gray T-shirt and jeans", "a small gray T-shirt and jeans",
     "a red collar", "a backyard lawn with a white picket fence and flower beds", "soft afternoon light"),
    ("P12", "一起跳起來",
     "the whole family jumps in the air at the same moment with big smiles, the father and the mother holding the boy's hands as he jumps between them, and the dog leaps beside them",
     "a yellow sweater and jeans", "a red sweater and jeans", "a small blue sweater and jeans",
     "a green bandana", "a bright white seamless photo studio", "bright even studio light"),
    ("P13", "聖誕市集抱小孩",
     "the father holds the boy on his hip with one arm, the mother stands close and leans her head on the father's shoulder, and the dog sits in front of them",
     "a charcoal wool coat with a red scarf", "a cream wool coat with a gray scarf", "a navy puffer coat and red mittens",
     "a red knit sweater", "a Christmas market at dusk with warm string lights and wooden stalls softly blurred behind them", "warm soft string-light glow"),
    ("P14", "一二三盪起來",
     "the father and the mother walk side by side and each hold one of the boy's hands, swinging him up between them so his feet are off the ground, the boy laughing, and the dog runs beside them",
     "a white henley shirt and khaki trousers", "a flowing cream dress", "a white T-shirt and beige overalls",
     "a brown leather collar", "a meadow with tall golden grass", "soft golden-hour light"),
    ("P15", "盪鞦韆",
     "the boy sits on a wooden tree swing, the father stands behind the swing with his hands on the ropes, the mother stands beside the boy holding his hand, and the dog sits in front of the swing",
     "a light green linen shirt and white trousers", "a white lace blouse and jeans", "a small light green shirt and white shorts",
     "a light green bandana", "a garden with a large old oak tree and a green lawn", "soft dappled daylight"),
    ("P16", "經典扶手椅全家福",
     "a classic formal family portrait: the mother sits in an elegant velvet armchair, the boy stands beside her leaning on the armrest, the father stands behind the armchair with one hand on the mother's shoulder, and the dog lies on the rug in front of the armchair",
     "a black three-piece suit", "a burgundy velvet dress", "a small black vest suit with a burgundy bow tie",
     "a burgundy bow tie", "a traditional portrait studio with a dark green painted backdrop and a Persian rug", "soft Rembrandt-style studio light"),
    ("P17", "湖邊木棧道",
     "the family sits on a wooden dock facing the camera, the father's arm around the mother, the boy sitting on the father's knee, and the dog lying beside the mother",
     "a navy fleece vest over a plaid shirt and jeans", "a cream cable-knit cardigan and jeans", "a red flannel shirt and jeans",
     "a red bandana", "a calm mountain lake with pine trees and mountains behind them", "soft morning light"),
    ("P18", "窗邊一起看書",
     "the family sits together on a cushioned window seat: the mother holds an open picture book, the boy sits on her lap pointing at the book, the father sits beside them with his arm around the mother, all looking up at the camera, and the dog rests its head on the father's knee",
     "a light blue oxford shirt and a navy cardigan", "an oatmeal knit sweater", "a navy striped long-sleeve T-shirt",
     "a navy collar", "a cozy reading nook by a large window with bookshelves", "soft window daylight"),
    ("P19", "廚房一起做餅乾",
     "the family bakes together at a kitchen island: the boy sits on the countertop with flour on his hands, the father and the mother stand on either side of him, with a bowl of dough and cookie cutters on the counter, and the dog sits on the floor looking up at them",
     "a white T-shirt and a denim apron", "a striped shirt and a denim apron", "a small white T-shirt and a tiny apron",
     "a red bandana", "a bright farmhouse kitchen with white cabinets and wooden shelves", "soft daylight"),
    ("P20", "雪地坐雪橇",
     "the boy sits on a wooden sled in the snow, the mother kneels behind him hugging him, the father kneels beside the sled holding its rope, and the dog sits next to the father",
     "a navy ski jacket and gray snow pants", "a white puffer jacket and black snow pants", "a red snow jacket and snow pants",
     "a red knit sweater", "a snowy hill with snow-covered pine trees", "soft bright overcast light"),
]


def refs(t):
    return REFS[VARIANT]


def prompt(t):
    _, _, pose, dad, mom, boy, dog, place, light = t
    return (HEAD[VARIANT] + ONCE + f"New pose: {pose}. Outfits: the father wears {dad}, the mother wears {mom}, the boy wears {boy}, "
            f"and the dog wears {dog}. Setting: {place}, with {light}. A natural, professional family photograph.")
