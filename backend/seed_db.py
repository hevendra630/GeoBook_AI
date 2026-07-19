import asyncio
import os
import random
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.models import Business, BusinessCategory
import google.generativeai as genai
from sqlalchemy import text

load_dotenv()

CITIES = [
    {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
    {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480},
    {"name": "Guntur", "lat": 16.3067, "lon": 80.4365},
    {"name": "Nellore", "lat": 14.4426, "lon": 79.9865},
    {"name": "Kurnool", "lat": 15.8281, "lon": 78.0373},
    {"name": "Kakinada", "lat": 16.9891, "lon": 82.2475},
    {"name": "Rajahmundry", "lat": 17.0005, "lon": 81.8040},
    {"name": "Tirupati", "lat": 13.6288, "lon": 79.4192},
    {"name": "Kadapa", "lat": 14.4673, "lon": 78.8242},
    {"name": "Anantapur", "lat": 14.6819, "lon": 77.6006},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Kadiri", "lat": 14.1130, "lon": 78.1601},
    {"name": "Mysore", "lat": 12.2958, "lon": 76.6394},
    {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
    {"name": "Madurai", "lat": 9.9252, "lon": 78.1198},
    {"name": "Warangal", "lat": 17.9689, "lon": 79.5941},
]

NAMES = {
    BusinessCategory.restaurant: ["Spice Route", "Biryani House", "Andhra Meals", "Foodie's Point", "City Cafe", "Taste Hub", "Grand Restaurant", "Family Diner", "The Dosa Place", "Kebab Corner"],
    BusinessCategory.school: ["Public School", "High School", "Academy", "International School", "Convent", "Vidya Mandir", "Grammar School", "Modern School", "Heritage School", "Global Academy"],
    BusinessCategory.hospital: ["City Hospital", "General Hospital", "Care Clinic", "Life Hospital", "Medicare", "Health City", "Trust Hospital", "Multi-Specialty Hospital", "Apex Hospital", "Sanjeevani"],
    BusinessCategory.police: ["Police Station", "Town PS", "Traffic Police", "Women PS", "Rural PS", "Central PS", "Cyber Crime Station", "Outpost", "Highway Patrol", "Headquarters"],
    BusinessCategory.bus_stop: ["RTC Bus Stand", "City Bus Stop", "Express Stop", "Highway Bus Stop", "Junction Bus Stop", "Central Station", "Local Stop", "Transit Hub", "Depot", "Main Bus Stand"],
    BusinessCategory.salon: ["Style Salon", "Beauty Hub", "Glamour Salon", "Cuts & Curls", "Mens Parlour", "Unisex Salon", "Elegance", "Makeover Studio", "Trends", "Radiance"],
    BusinessCategory.dental: ["Smile Dental", "Care Dental Clinic", "Advanced Dental", "Family Dental", "Tooth Fairy", "Perfect Smile", "Root Canal Center", "Orthodontics", "Dental Spa", "Oral Care"],
    BusinessCategory.clinic: ["Health Clinic", "Primary Care", "Fever Clinic", "Pediatric Clinic", "Skin Clinic", "Eye Clinic", "Physiotherapy", "Wellness Center", "Women's Clinic", "Homeopathy Clinic"]
}

DESCRIPTIONS = {
    BusinessCategory.restaurant: "A great place to eat authentic local food with amazing ambiance.",
    BusinessCategory.school: "Providing quality education with experienced teachers and modern facilities.",
    BusinessCategory.hospital: "24/7 care with top doctors and emergency facilities.",
    BusinessCategory.police: "Maintaining law and order, ensuring citizen safety.",
    BusinessCategory.bus_stop: "Connecting major routes and providing comfortable transit.",
    BusinessCategory.salon: "Premium beauty and grooming services.",
    BusinessCategory.dental: "Specialized dental care and oral hygiene.",
    BusinessCategory.clinic: "Consultations and treatments by expert doctors."
}

async def seed():
    print("Connecting to Supabase...")
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    elif db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://")
        
    engine = create_async_engine(db_url, connect_args={"statement_cache_size": 0})
    Session = async_sessionmaker(engine)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        genai.configure(api_key=gemini_key)
    
    businesses = []
    
    print("Generating business data...")
    for city in CITIES:
        for cat in BusinessCategory:
            if cat == BusinessCategory.other:
                continue
            for i in range(10):
                lat = city["lat"] + random.uniform(-0.05, 0.05)
                lon = city["lon"] + random.uniform(-0.05, 0.05)
                name = f"{random.choice(NAMES[cat])} {city['name']}"
                desc = DESCRIPTIONS[cat]
                
                b = Business(
                    name=name,
                    category=cat,
                    address=f"Some Street, {city['name']}, AP",
                    latitude=lat,
                    longitude=lon,
                    description=desc
                )
                businesses.append(b)

    print(f"Generated {len(businesses)} businesses. Generating embeddings in batches...")
    
    if gemini_key:
        # Batch requests to Gemini (max 100 per batch usually)
        batch_size = 100
        for i in range(0, len(businesses), batch_size):
            batch = businesses[i:i+batch_size]
            texts = [f"{b.name} - {b.category.value} - {b.description}" for b in batch]
            try:
                # Wrap in asyncio.to_thread if it's blocking, but it's okay here
                result = genai.embed_content(
                    model="models/gemini-embedding-2",
                    content=texts,
                    task_type="retrieval_document"
                )
                embeddings = result['embedding']
                for b, emb in zip(batch, embeddings):
                    b.embedding = emb
                print(f"Embedded batch {i//batch_size + 1}/{(len(businesses)+batch_size-1)//batch_size}")
                # sleep to avoid rate limits on free tier (15 RPM -> 1 request every 4 seconds)
                await asyncio.sleep(4)
            except Exception as e:
                print(f"Error generating embeddings for batch {i}: {e}")
                
    async with Session() as db:
        print("Clearing old test data...")
        await db.execute(text("TRUNCATE TABLE businesses CASCADE"))
        print("Inserting new data...")
        db.add_all(businesses)
        await db.commit()
        print(f"Successfully inserted {len(businesses)} businesses!")

if __name__ == "__main__":
    asyncio.run(seed())
