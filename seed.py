import os
import random
import cloudinary
import cloudinary.uploader
from datetime import datetime
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

MONGO_URI = "mongodb+srv://sandrobencinic_db_user:EO9pLJU3lopUvE65@cluster0.lrjp8m6.mongodb.net/?appName=Cluster0"
MONGO_DBNAME = "woofdotcom"
CLOUDINARY_URL = "cloudinary://688417916775199:4tEXnuXR3LQazJIlHTcaitrI0f0@diycugkbp"

cloudinary.config(cloudinary_url=CLOUDINARY_URL)
client = MongoClient(MONGO_URI)
db = client[MONGO_DBNAME]

# Clear existing data
for col in ["users", "categories", "posts", "dogs", "messages"]:
    db[col].drop()

print("Cleared existing collections.")

# ── Categories ────────────────────────────────────────────────────────────────
categories = ["Training", "Health", "Nutrition", "Behaviour", "Lifestyle"]
db.categories.insert_many([{"category_name": c} for c in categories])
print("Categories inserted.")

# ── Users ─────────────────────────────────────────────────────────────────────
def make_user(username, email, fname, lname, phone, about, password="Password1!"):
    return {
        "username": username,
        "password": generate_password_hash(password),
        "email": email,
        "fname": fname,
        "lname": lname,
        "phone": phone,
        "about": about,
        "liked_posts": [],
        "adoption_requests": []
    }

users = [
    make_user("Admin", "admin@woofdotcom.com", "Admin", "User", "000-000-0000",
              "Site administrator and dog lover."),
    make_user("sarah_w", "sarah@example.com", "Sarah", "Wilson", "555-101-2020",
              "Proud owner of two golden retrievers. Dog trainer for 8 years."),
    make_user("mike_d", "mike@example.com", "Mike", "Davies", "555-303-4040",
              "Vet nurse and passionate advocate for dog adoption."),
    make_user("emma_r", "emma@example.com", "Emma", "Roberts", "555-505-6060",
              "Lifelong dog owner. Love hiking with my huskies!"),
]
db.users.insert_many(users)
print("Users inserted.")

admin = db.users.find_one({"username": "Admin"})
sarah = db.users.find_one({"username": "sarah_w"})
mike  = db.users.find_one({"username": "mike_d"})
emma  = db.users.find_one({"username": "emma_r"})

# ── Helper: upload image from URL to Cloudinary ───────────────────────────────
def upload_image(url, public_id):
    result = cloudinary.uploader.upload(url, public_id=public_id, resource_type="image")
    return result["secure_url"]

# ── Posts ─────────────────────────────────────────────────────────────────────
post_images = [
    ("https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg", "post_img_1001"),
    ("https://images.dog.ceo/breeds/labrador/n02099712_4323.jpg",         "post_img_1002"),
    ("https://images.dog.ceo/breeds/husky/n02110185_10047.jpg",           "post_img_1003"),
    ("https://images.dog.ceo/breeds/beagle/n02088364_10108.jpg",          "post_img_1004"),
    ("https://images.dog.ceo/breeds/poodle-standard/n02113799_2280.jpg",  "post_img_1005"),
    ("https://images.dog.ceo/breeds/bulldog-english/n02096585_1380.jpg",  "post_img_1006"),
]

posts_data = [
    {
        "title": "5 Essential Commands Every Dog Should Know",
        "summary": "Teaching your dog basic commands is the foundation of a happy life together. Here are the five commands you should start with.",
        "content": """Starting with the basics is always the best approach when training your dog. These five commands will make your life much easier and keep your dog safe.\n\n**1. Sit** – The most fundamental command. Hold a treat close to your dog's nose, then move your hand up so their bottom lowers. Once they're in sitting position, say "Sit" and give the treat.\n\n**2. Stay** – Ask your dog to sit first. Open your palm in front of you and say "Stay". Take a few steps back and reward them if they stay put. Gradually increase the distance.\n\n**3. Come** – This recall command could one day save your dog's life. Put a leash on your dog, crouch down, and gently pull the leash while saying "Come". When they reach you, reward them generously.\n\n**4. Down** – Find a particularly good-smelling treat and hold it in your closed fist. Hold it up to your dog's snout, then move it to the floor and along the ground. Their body will follow.\n\n**5. Leave it** – Place a treat in both hands. Show your dog one enclosed fist with the treat inside. Say "Leave it". When they stop trying, give them the treat from the other hand.\n\nConsistency is key. Short, frequent training sessions work better than long infrequent ones. Always end on a positive note!""",
        "category": "Training",
        "author": "sarah_w",
        "likes": 24,
        "img_url": post_images[0],
    },
    {
        "title": "How to Spot Signs of a Healthy Dog",
        "summary": "Regular health checks at home can help you catch problems early. Learn what to look for to keep your dog in top shape.",
        "content": """As a dog owner, you're your pet's first line of defence. Knowing the signs of a healthy dog means you'll notice quickly when something is off.\n\n**Eyes** – Should be bright and clear with no discharge. A little sleep crust in the morning is normal, but persistent discharge warrants a vet visit.\n\n**Ears** – Clean and odour-free. Shaking of the head or scratching at ears can indicate infection or mites.\n\n**Coat** – A healthy coat is shiny and smooth. Excessive shedding, bald patches, or dull fur can signal nutritional deficiencies or skin conditions.\n\n**Weight** – You should be able to feel your dog's ribs without pressing hard, but not see them. Check with your vet if you're unsure about ideal weight.\n\n**Gums** – Should be pink and moist. Pale, white, blue or yellow gums are a veterinary emergency.\n\n**Energy levels** – Know your dog's normal energy baseline. Sudden lethargy or unusual hyperactivity can both be signs that something needs attention.\n\n**Bathroom habits** – Regular, firm stools are a good sign. Diarrhoea lasting more than 24 hours or blood in urine/faeces needs immediate attention.\n\nA monthly at-home check keeps you in tune with your dog's health and makes vet visits more productive.""",
        "category": "Health",
        "author": "mike_d",
        "likes": 31,
        "img_url": post_images[1],
    },
    {
        "title": "Raw vs Kibble: What's Best for Your Dog?",
        "summary": "The debate between raw feeding and kibble has been going on for years. We break down the pros and cons of each approach.",
        "content": """Choosing how to feed your dog is one of the most debated topics in the dog community. Here's a balanced look at both options.\n\n**Kibble (Dry Food)**\n\nPros: Convenient, long shelf life, nutritionally balanced if you choose a quality brand, generally more affordable, good for dental health.\n\nCons: Heavily processed, some brands use low-quality fillers, can contain preservatives and artificial additives.\n\n**Raw Food Diet (BARF – Biologically Appropriate Raw Food)**\n\nPros: Mimics what dogs eat in the wild, often improves coat condition and energy levels, no artificial additives, many owners report smaller stools and better digestion.\n\nCons: Requires careful meal planning to ensure nutritional balance, risk of bacterial contamination (for both dog and owner), more expensive, needs freezer space.\n\n**What do vets say?**\n\nMost vets recommend high-quality kibble as the baseline, as it's guaranteed to meet AAFCO nutritional standards. If you want to introduce raw, consult your vet first and consider a pre-made raw diet from a reputable supplier rather than DIY.\n\n**The middle ground**\n\nMany owners feed a combination – quality kibble as the base with occasional raw meaty bones or fresh food toppers. This gives the convenience of kibble with some of the benefits of fresh food.\n\nWhatever you choose, consistency matters. Sudden diet changes upset stomachs. Transition slowly over 7–10 days.""",
        "category": "Nutrition",
        "author": "Admin",
        "likes": 18,
        "img_url": post_images[2],
    },
    {
        "title": "Understanding Dog Body Language",
        "summary": "Dogs communicate constantly through their bodies. Learning to read the signals can transform your relationship with your dog.",
        "content": """Dogs can't speak our language, but they're incredibly expressive if you know what to look for. Misreading body language is one of the most common causes of dog bites and relationship breakdowns.\n\n**The Tail**\n\nA wagging tail doesn't always mean a happy dog. A high, fast wag often signals excitement or arousal (positive or negative). A low, slow wag can mean uncertainty or submission. A tail tucked between the legs signals fear.\n\n**The Eyes**\n\nSoft, relaxed eyes mean a relaxed dog. Hard, staring eyes can be a warning. "Whale eye" – when you can see the whites of the eyes – is a stress signal. Slow blinking is friendly; a dog looking away is trying to de-escalate.\n\n**The Ears**\n\nPinned back ears signal fear or submission. Erect, forward-pointing ears signal alertness or arousal. Relaxed ears in a neutral position mean the dog is comfortable.\n\n**The Body**\n\nA dog that rolls over is either being submissive or asking for a belly rub (context matters!). Piloerection – hackles raised along the back – signals arousal, fear or aggression. A play bow (front end down, back end up) is a universal invitation to play.\n\n**Calming Signals**\n\nYawning, lip licking, sniffing the ground, and turning away are all "calming signals" – your dog telling you (or another dog) that they need some space. Recognising these early prevents situations from escalating.""",
        "category": "Behaviour",
        "author": "emma_r",
        "likes": 42,
        "img_url": post_images[3],
    },
    {
        "title": "The Best Dog-Friendly Hiking Trails",
        "summary": "Exploring the great outdoors with your dog is one of life's great pleasures. Here are some tips and our favourite trails.",
        "content": """Hiking with your dog is one of the most rewarding experiences for both of you. Fresh air, new smells, and quality time together – what's not to love?\n\n**Before You Go**\n\nAlways check that the trail allows dogs and whether they need to be on a leash. Check your dog's fitness – older dogs or brachycephalic breeds (pugs, bulldogs) may struggle with steep terrain. Make sure vaccinations and flea/tick treatment are up to date.\n\n**What to Pack**\n\n- Collapsible water bowl and plenty of water\n- High-value snacks for energy and motivation\n- Dog first aid kit (especially tick remover)\n- Poop bags (always!)\n- Dog boots if terrain is rocky\n- Their ID tag and consider a GPS tracker\n\n**On the Trail**\n\nLet your dog sniff – this is mentally tiring in the best way and is what they're there for. Take regular breaks, especially on hot days. Watch for signs of fatigue: excessive panting, lagging behind, seeking shade.\n\n**After the Hike**\n\nCheck paws for cuts, thorns, or burns. Check the coat thoroughly for ticks – pay special attention to around the ears, between toes, and under the collar. A post-hike meal (not immediately after heavy exercise) and plenty of water will have your dog sleeping soundly.\n\nA tired dog is a happy dog – and a happy owner!""",
        "category": "Lifestyle",
        "author": "sarah_w",
        "likes": 29,
        "img_url": post_images[4],
    },
    {
        "title": "Separation Anxiety: Causes and Solutions",
        "summary": "Separation anxiety is one of the most common behavioural issues in dogs. Understanding it is the first step to helping your dog.",
        "content": """If your dog howls, destroys things, or has accidents when left alone, they may be suffering from separation anxiety. It's distressing for dogs and owners alike, but it's treatable.\n\n**What Causes It?**\n\nSeparation anxiety can develop after a change in routine (like an owner returning to work after time at home), after rehoming, or due to a traumatic experience. Some breeds are more prone to it than others – particularly those bred to work closely with humans.\n\n**Signs to Watch For**\n\n- Destructive behaviour specifically when alone\n- Excessive vocalisation (barking, howling, whining)\n- House soiling despite being toilet trained\n- Pacing, drooling, or excessive panting before you leave\n- Shadowing you around the house\n\n**What Helps**\n\n**Desensitisation** – Gradually get your dog used to being alone. Start with very short absences (even just stepping outside for 30 seconds) and build up very slowly.\n\n**Departure cues** – Make leaving and arriving low-key. Avoid big emotional goodbyes or excited greetings.\n\n**Enrichment** – Give a special long-lasting treat only when you leave (a stuffed Kong, for example). This creates a positive association.\n\n**Exercise** – A well-exercised dog settles more easily.\n\n**Professional help** – For severe cases, a qualified behaviourist and/or veterinary support can make a real difference. Don't suffer in silence – help is available.""",
        "category": "Behaviour",
        "author": "mike_d",
        "likes": 37,
        "img_url": post_images[5],
    },
]

inserted_posts = []
for i, p in enumerate(posts_data):
    url, public_id = p["img_url"]
    print(f"Uploading post image {i+1}/6: {public_id}...")
    img_path = upload_image(url, public_id)
    img_id = int(public_id.split("_")[-1])
    now = datetime.now()
    doc = {
        "title": p["title"],
        "summary": p["summary"],
        "content": p["content"],
        "category": p["category"],
        "author": p["author"],
        "created": now.timetuple(),
        "create_date": now.strftime("%d/%m/%Y"),
        "create_time": now.strftime("%H:%M"),
        "update_date": "",
        "likes": p["likes"],
        "img_id": img_id,
        "img_filename": f"{public_id}.webp",
        "img_path": img_path,
    }
    result = db.posts.insert_one(doc)
    inserted_posts.append(result.inserted_id)

print("Posts inserted.")

# ── Dogs ──────────────────────────────────────────────────────────────────────
dog_images = [
    ("https://images.dog.ceo/breeds/retriever-golden/n02099601_7771.jpg", "dog_img_2001"),
    ("https://images.dog.ceo/breeds/husky/n02110185_11364.jpg",           "dog_img_2002"),
    ("https://images.dog.ceo/breeds/beagle/n02088364_13776.jpg",          "dog_img_2003"),
    ("https://images.dog.ceo/breeds/labrador/n02099712_7003.jpg",         "dog_img_2004"),
    ("https://images.dog.ceo/breeds/spaniel-cocker/n02102318_5978.jpg",   "dog_img_2005"),
    ("https://images.dog.ceo/breeds/poodle-standard/n02113799_4063.jpg",  "dog_img_2006"),
]

dogs_data = [
    {
        "name": "buddy",
        "gender": "Male",
        "age": "3",
        "size": "Large",
        "good_with": ["Kids", "Dogs", "Cats"],
        "description": "Buddy is a gorgeous 3-year-old Golden Retriever with a heart of gold. He loves everyone he meets and has never met a stranger. Buddy is fully house trained, great on the lead, and knows his basic commands. He was surrendered when his owner moved abroad and is looking for a loving forever home where he can get the cuddles and exercise he deserves.",
        "greeting": "Hi, I'm Buddy! I love fetch, belly rubs, and stealing socks (don't tell anyone). I promise to be your best friend forever!",
        "owner": admin,
        "img_url": dog_images[0],
    },
    {
        "name": "luna",
        "gender": "Female",
        "age": "2",
        "size": "Large",
        "good_with": ["Dogs"],
        "description": "Luna is an energetic and intelligent 2-year-old Husky who needs an experienced owner who understands the breed. She is stunning to look at and an absolute joy to be around once she has had her exercise. Luna needs at least 2 hours of activity a day and a secure garden. She is not suitable for homes with cats or small animals due to a high prey drive.",
        "greeting": "Howwooo! I'm Luna and I have enough energy for the both of us. Take me hiking and I'll love you forever.",
        "owner": emma,
        "img_url": dog_images[1],
    },
    {
        "name": "charlie",
        "gender": "Male",
        "age": "5",
        "size": "Small",
        "good_with": ["Kids", "Dogs", "Cats"],
        "description": "Charlie is a sweet, gentle 5-year-old Beagle who adores company. He is great with children and other pets, making him the perfect family dog. Charlie loves sniffing on long walks and is an expert at finding the best spots in the garden to sunbathe. He is fully vaccinated, neutered, and microchipped. A real gem looking for his forever sofa.",
        "greeting": "Hi there! I'm Charlie. I might follow my nose into trouble sometimes, but I always come back for cuddles. Adopt me?",
        "owner": mike,
        "img_url": dog_images[2],
    },
    {
        "name": "max",
        "gender": "Male",
        "age": "1",
        "size": "Large",
        "good_with": ["Dogs"],
        "description": "Max is a bouncy 1-year-old Labrador who is full of life and mischief! He is still very much a puppy at heart and needs a home that can continue his training. Max knows sit, down and is working on recall. He would thrive with an active family or individual who can give him the stimulation he needs. Not suitable for homes with very young children due to his size and exuberance.",
        "greeting": "HELLO! Is it walkies time? What about now? Now? I'm Max and every moment is the BEST MOMENT EVER!",
        "owner": admin,
        "img_url": dog_images[3],
    },
    {
        "name": "rosie",
        "gender": "Female",
        "age": "4",
        "size": "Medium",
        "good_with": ["Kids", "Dogs", "Cats"],
        "description": "Rosie is a calm and affectionate 4-year-old Cocker Spaniel who loves nothing more than being close to her people. She is well-mannered, great in the car, and fantastic with children and other animals. Rosie was previously a therapy dog and has impeccable manners. She is looking for a quieter home where she can be a loyal companion.",
        "greeting": "Hello, lovely. I'm Rosie. I'll sit nicely, I won't bark, and I'll look at you with these eyes until you give me a biscuit.",
        "owner": sarah,
        "img_url": dog_images[4],
    },
    {
        "name": "pepper",
        "gender": "Female",
        "age": "6",
        "size": "Medium",
        "good_with": ["Kids", "Cats"],
        "description": "Pepper is a sophisticated and playful 6-year-old Standard Poodle. Don't let the elegant appearance fool you – she is hilarious and loves to clown around. Pepper is incredibly smart, quick to learn, and has been trained in agility. She is hypoallergenic, making her a wonderful option for families with allergies. She has recently been rehomed due to her owner's health problems.",
        "greeting": "Bonjour! I'm Pepper. I'm smart, I'm stylish, and I'm probably already training you without you knowing.",
        "owner": mike,
        "img_url": dog_images[5],
    },
]

for i, d in enumerate(dogs_data):
    url, public_id = d["img_url"]
    print(f"Uploading dog image {i+1}/6: {public_id}...")
    img_path = upload_image(url, public_id)
    img_id = int(public_id.split("_")[-1])
    now = datetime.now()
    doc = {
        "name": d["name"],
        "gender": d["gender"],
        "age": d["age"],
        "size": d["size"],
        "good_with": d["good_with"],
        "description": d["description"],
        "greeting": d["greeting"],
        "created": now.timetuple(),
        "owner_id": d["owner"]["_id"],
        "img_id": img_id,
        "img_filename": f"{public_id}.webp",
        "img_path": img_path,
    }
    db.dogs.insert_one(doc)

print("Dogs inserted.")
print("\nAll done! Seed data loaded successfully.")
print("\nAdmin login: username=Admin  password=Password1!")
print("Other users: sarah_w / mike_d / emma_r  password=Password1!")
