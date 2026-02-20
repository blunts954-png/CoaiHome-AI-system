"""
Generate TikTok content calendar - NO SERVER NEEDED
Run this to create 30 days of content instantly!
"""
import csv
from datetime import datetime, timedelta
import random

# Hook templates
HOOKS = [
    "POV: You finally found the perfect drawer organizer",
    "Stop scrolling if you hate messy drawers!",
    "This organizer saved my morning routine",
    "I was today years old when I learned about this",
    "If you have a small apartment, you NEED this",
    "This is your sign to get organized",
    "The way this changed everything...",
    "TikTok made me buy it and I'm not mad",
    "Things that just make sense: drawer organizers",
    "Nobody told me about this until now",
    "This is what your kitchen needs",
    "If you're still using regular drawers, stop",
    "This went viral for a reason",
    "I tested this so you don't have to",
    "This is the organizer that broke the internet"
]

CONTENT_TYPES = {
    "product_demo": {"duration": "15-30s", "best_time": ["12:00", "19:00"]},
    "before_after": {"duration": "10-20s", "best_time": ["8:00", "20:00"]},
    "problem_solution": {"duration": "20-30s", "best_time": ["13:00", "21:00"]},
    "tips_educational": {"duration": "30-60s", "best_time": ["9:00", "15:00"]},
    "asmr_satisfying": {"duration": "15-30s", "best_time": ["20:00", "22:00"]},
    "storytime": {"duration": "45-90s", "best_time": ["19:00", "21:00"]}
}

SAMPLE_PRODUCTS = [
    {"title": "Premium Drawer Organizer", "price": "24.99"},
    {"title": "Magnetic Spice Rack", "price": "34.99"},
    {"title": "Under Sink Organizer", "price": "29.99"},
    {"title": "Fridge Storage Bins", "price": "19.99"},
    {"title": "Closet Organizer Set", "price": "39.99"}
]

def generate_script(product, content_type):
    hook = random.choice(HOOKS).replace("drawer organizer", product["title"].lower())
    
    if content_type == "product_demo":
        return f"""[0-3s] {hook}
[3-8s] Show the {product['title']} in use
[8-15s] Show the result/benefit
[15-20s] Show different use cases
[20-25s] Price reveal - only ${product['price']}
[25-30s] Link in bio!"""
    
    elif content_type == "before_after":
        return f"""[0-3s] {hook}
[3-5s] Show messy/problem state
[5-8s] Add {product['title']}
[8-12s] Quick transformation
[12-15s] Reveal organized result
[15-20s] CTA - Link in bio!"""
    
    else:  # problem_solution and others
        return f"""[0-3s] Stop doing this! Show frustrating old way
[3-8s] Problem demonstration
[8-12s] "Instead, try this:" + reveal {product['title']}
[12-18s] Show it solving the problem
[18-25s] Multiple use cases
[25-30s] Link in bio - only ${product['price']}"""

def generate_caption(product):
    templates = [
        f"POV: You found the perfect {product['title']} 🥹\n\nLink in bio!",
        f"This {product['title']} went viral for a reason 🔥\n\nGet yours - link in bio!",
        f"Why didn't anyone tell me about {product['title']} sooner?! 🤯\n\nLink in bio!",
        f"The way this changed everything... ✨\n\n{product['title']} - link in bio!",
        f"Add to cart energy 🛒✨\n\n{product['title']}\nLink in bio!"
    ]
    return random.choice(templates)

def generate_hashtags():
    return "#homeorganization #organization #tiktokmademebuyit #amazonfinds #satisfying #musthave #coaihome"

def create_calendar():
    calendar = []
    start_date = datetime.now()
    content_types = list(CONTENT_TYPES.keys())
    
    for day in range(30):
        date = start_date + timedelta(days=day)
        posts_per_day = 2 if day % 3 != 0 else 3
        
        for post_num in range(posts_per_day):
            product = SAMPLE_PRODUCTS[day % len(SAMPLE_PRODUCTS)]
            content_type = content_types[day % len(content_types)]
            best_times = CONTENT_TYPES[content_type]["best_time"]
            post_time = best_times[post_num % len(best_times)]
            
            calendar.append({
                "day": day + 1,
                "date": date.strftime("%Y-%m-%d"),
                "post_time": post_time,
                "content_type": content_type,
                "product": product["title"],
                "hook": random.choice(HOOKS).replace("drawer organizer", product["title"].lower()),
                "script": generate_script(product, content_type),
                "cta": f"Link in bio - only ${product['price']}",
                "hashtags": generate_hashtags(),
                "caption": generate_caption(product),
                "status": "scheduled"
            })
    
    return calendar

def save_to_csv(calendar):
    with open("content_calendar.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "day", "date", "post_time", "content_type", "product",
            "hook", "script", "cta", "hashtags", "caption", "status"
        ])
        writer.writeheader()
        for item in calendar:
            writer.writerow(item)
    print(f"✅ Saved {len(calendar)} content pieces to content_calendar.csv")

def main():
    print("🎬 Generating 30-day TikTok content calendar...")
    print("=" * 60)
    
    calendar = create_calendar()
    save_to_csv(calendar)
    
    print("=" * 60)
    print(f"📅 Created {len(calendar)} videos worth of content!")
    print("🎬 Now film these and post 2-3x daily!")
    print()
    print("📁 Open 'content_calendar.csv' to see your content plan")
    print()
    print("🚀 SAMPLE - Day 1:")
    print(f"   Hook: {calendar[0]['hook']}")
    print(f"   Time: {calendar[0]['post_time']}")
    print(f"   Type: {calendar[0]['content_type']}")

if __name__ == "__main__":
    main()
