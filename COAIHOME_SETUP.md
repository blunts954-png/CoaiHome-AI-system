# CoaiHome Store Setup Guide
## From Zero to Live Store

---

## STEP 1: Connect Your Shopify Store to the AI System

### 1.1 Get Your Shopify API Credentials

1. Go to: https://coaihome.myshopify.com/admin/settings/apps
2. Click "Develop apps" (at the bottom)
3. Click "Create an app"
4. Name it: "CoaiHome Automation"
5. Click "Configure Admin API scopes"
6. Enable these permissions:
   - `read_products`, `write_products`
   - `read_orders`, `write_orders`
   - `read_customers`, `write_customers`
   - `read_inventory`, `write_inventory`
   - `read_content`, `write_content`
7. Click "Save"
8. Click "Install app"
9. Copy the **Admin API access token** (starts with `shpat_`)

### 1.2 Add to Your Deployment

Add this to your Railway/Render environment variables:

```bash
SHOPIFY_SHOP_URL=coaihome.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxx (the one you just copied)
```

Restart your deployment.

---

## STEP 2: Create Store via Your AI Dashboard

### 2.1 Access Your Dashboard

Go to your deployed URL:
```
https://your-app.railway.app
```

### 2.2 Fill In Store Creation Form

Click "Create AI Store" and enter:

```
Niche: home organization
Brand Name: CoaiHome
Target Country: US
Brand Tone: modern
Primary Color: #4A6741 (sage green)
Secondary Color: #FFFFFF (white)
Price Range: {"min": 15, "max": 60}
Num Products: 10
```

Click "Create" and wait 5-10 minutes.

### 2.3 What Happens Next

The AI will:
1. ✅ Connect to AutoDS AI Store Builder
2. ✅ Generate store theme with your colors
3. ✅ Create homepage content
4. ✅ Research trending home organization products
5. ✅ Import 5-10 winning products
6. ✅ Set up pricing rules

**Check progress in your Shopify admin!**

---

## STEP 3: If AutoDS Store Builder Doesn't Work

### Manual Store Setup Guide

#### Step 3.1: Choose Shopify Theme

1. In Shopify admin: Online Store → Themes
2. Click "Explore free themes"
3. Recommended: **Dawn** or **Craft**
4. Click "Add to theme library"
5. Click "Publish"

#### Step 3.2: Customize Theme

Click "Customize" and set:

**Colors:**
- Background: #FFFFFF (white)
- Text: #1A1A1A (near black)
- Accent: #4A6741 (sage green)
- Secondary: #F5F5F5 (light gray)

**Typography:**
- Headings: Inter or Helvetica Neue
- Body: Inter or system font

**Logo:**
- Use Canva to create simple text logo: "CoaiHome"
- Font: Clean sans-serif, all lowercase or title case
- Upload to Header

#### Step 3.3: Create Pages

Go to Online Store → Pages → Add page:

**About Us Page:**
```
Title: About CoaiHome

Content:
At CoaiHome, we believe an organized home is a happy home.

We use AI to discover the best home organization products—
items that actually work, look great, and don't break the bank.

Every product in our store is:
✓ Tested for quality
✓ Priced fairly  
✓ Shipped fast

No more clutter. No more stress. Just a home that works for you.

Welcome to smarter home organization.
Welcome to CoaiHome.
```

**Contact Page:**
```
Title: Contact Us

Email: support@coaihome.com
Response time: Within 24 hours
```

**Shipping & Returns:**
```
Title: Shipping & Returns

SHIPPING
- Free shipping on orders over $35
- Standard shipping: 5-10 business days
- Express shipping: 3-5 business days

RETURNS
- 30-day hassle-free returns
- Items must be unused and in original packaging
- Contact us for return label
```

**FAQ Page:**
```
Title: FAQ

Q: How long does shipping take?
A: Most orders arrive within 5-10 business days.

Q: Do you offer free shipping?
A: Yes! Free shipping on all orders over $35.

Q: What if I don't like my purchase?
A: We offer 30-day hassle-free returns.

Q: Where do you ship from?
A: We work with suppliers worldwide to get you the best products fast.

Q: How do I track my order?
A: You'll receive a tracking number via email once your order ships.
```

#### Step 3.4: Set Up Navigation

Online Store → Navigation:

**Main Menu:**
- Home
- Shop All
- Kitchen Organization
- Closet & Storage
- Bathroom Organizers
- About
- Contact

**Footer Menu:**
- Shipping & Returns
- FAQ
- Privacy Policy
- Terms of Service

#### Step 3.5: Configure Settings

**Settings → General:**
- Store name: CoaiHome
- Email: support@coaihome.com

**Settings → Payments:**
- Connect Shopify Payments (or PayPal)

**Settings → Shipping:**
- Add "Standard Shipping" - $4.99
- Add "Free Shipping" - $0 (for orders over $35)

**Settings → Taxes:**
- Let Shopify handle it automatically

---

## STEP 4: Stock Your Store with Products

### Option A: AutoDS Integration (Recommended)

#### 4.1 Get AutoDS Account

1. Go to: https://autods.com
2. Sign up for 14-day free trial
3. Connect your Shopify store:
   - Go to Settings → Store Settings
   - Click "Connect Store"
   - Enter: coaihome.myshopify.com
   - Follow OAuth flow

#### 4.2 Get AutoDS API Key

1. In AutoDS: Settings → API
2. Click "Generate API Key"
3. Copy the key

#### 4.3 Add to Your Deployment

Add to environment variables:
```bash
AUTODS_API_KEY=your_autods_api_key
```

#### 4.4 Use AutoDS Product Research

In AutoDS dashboard:
1. Click "Products" → "Find Products"
2. Search: "home organization"
3. Filter by:
   - Shipping to US: < 10 days
   - Supplier rating: 4.5+
   - Price: $5-20 cost
4. Click on products to see details
5. Click "Add to Store" for good ones

**Add 10-15 products to start**

### Option B: Manual Product Research

If AutoDS isn't working, use these product ideas:

#### Hot Home Organization Products 2024:

| Product | Cost | Sell For | Margin |
|---------|------|----------|--------|
| Drawer organizer set | $8 | $25 | 68% |
| Under-sink organizer | $12 | $35 | 66% |
| Refrigerator bins (set of 6) | $10 | $28 | 64% |
| Closet hanging shelves | $9 | $27 | 67% |
| Spice drawer organizer | $7 | $22 | 68% |
| Cabinet door organizer | $6 | $20 | 70% |
| Vacuum storage bags | $8 | $25 | 68% |
| Pantry can organizer | $11 | $32 | 66% |
| Makeup organizer | $9 | $28 | 68% |
| Cord organizer box | $5 | $18 | 72% |
| Fridge lazy susan | $8 | $24 | 67% |
| Under-bed storage | $14 | $40 | 65% |

#### Where to Source:

1. **AliExpress** - Lowest cost, longer shipping
2. **CJ Dropshipping** - US warehouse options
3. **Spocket** - US/EU suppliers (faster shipping)
4. **Syncee** - Curated suppliers

#### How to Add Products Manually:

1. In Shopify: Products → Add product
2. Title: Benefit-focused (not just product name)
3. Description: Use AI service or write yourself
4. Images: Download from supplier, upload to Shopify
5. Price: Cost × 3 (for 66% margin)
6. Compare at price: 20% higher (shows "sale")
7. Inventory: Set to track quantity
8. Shipping: Set weight for shipping calculations

---

## STEP 5: AI-Generated TikTok Content

### 5.1 Content Strategy for CoaiHome

**Content Pillars:**
1. **Before/After** transformations (50%)
2. **Problem/Solution** demos (30%)
3. **Lifestyle/ASMR** organization (20%)

### 5.2 TikTok Video Scripts (AI-Generated)

Use this prompt with ChatGPT/Claude:

```
I run a home organization store called CoaiHome.

Create 10 TikTok video scripts for [PRODUCT NAME].

Each script should:
- Hook in first 3 seconds
- Show problem/solution
- Include trending audio suggestion
- Have clear CTA
- Be 15-30 seconds

Format:
Video 1:
Hook: [text]
Script: [what happens]
Audio: [trending sound]
CTA: [call to action]
Hashtags: [5-7 hashtags]
```

### 5.3 Ready-to-Use TikTok Scripts

#### Script 1: Drawer Organizer
```
HOOK: "Stop digging through messy drawers 🛑"

SCENE 1 (0-3s): Hand frantically searching messy junk drawer
TEXT: "This was me every morning"

SCENE 2 (3-8s): Show drawer organizer being placed in
TEXT: "Then I found this"

SCENE 3 (8-15s): Time-lapse organizing items into compartments
TEXT: "5 minutes later..."

SCENE 4 (15-20s): Beautiful organized drawer reveal
TEXT: "Finally 😍"

SCENE 5 (20-25s): Hand pulling out organized items easily
TEXT: "Link in bio - $25"

AUDIO: "Makeba" by Jain OR "original sound - satisfying videos"

CTA: "Organize your drawers - link in bio"

HASHTAGS:
#homeorganization #drawerorganizer #organizationhacks #cozyhome #tidytok #homehacks #organization #smallspaces
```

#### Script 2: Under-Sink Organizer
```
HOOK: "The space under your sink is lying to you 😤"

SCENE 1 (0-3s): Messy under-sink cabinet, stuff falling out
TEXT: "Wasted space"

SCENE 2 (3-8s): Show 2-tier organizer being installed
TEXT: "This changes everything"

SCENE 3 (8-18s): Products being organized on shelves
TEXT: "Double the space"

SCENE 4 (18-25s): Satisfying reveal of organized under-sink
TEXT: "Game changer ✨"

AUDIO: Upbeat trending audio

CTA: "Double your space - link in bio"

HASHTAGS:
#bathroomorganization #under sink #organization #homehacks #smallbathroom #storagehacks #homeorganization
```

#### Script 3: Fridge Organization
```
HOOK: "POV: You open your fridge after organizing it 🧊"

SCENE 1 (0-3s): Dark, messy fridge
TEXT: "Before was chaos"

SCENE 2 (3-8s): Fridge bins being arranged
TEXT: "Added these bins"

SCENE 3 (8-20s): Aesthetic shot of organized fridge with matching containers
TEXT: "Satisfying ASMR"

SCENE 4 (20-25s): Person grabbing items smoothly
TEXT: "$28 for the set"

AUDIO: ASMR/satisfying sounds

CTA: "Get organized - link in bio"

HASHTAGS:
#fridgeorganization #kitchenorganization #fridgetok #organization #satisfying #asmr #cleanfridge
```

### 5.4 Using AI to Generate Content

**Option 1: ChatGPT/Claude**
```
Create 10 TikTok scripts for a [PRODUCT NAME] targeting 
millennials who want an organized home. Each should be 
15-30 seconds with a strong hook and call to action.
```

**Option 2: Your AI System**
Use the dashboard at `/dashboard` → AI Content Generator

**Option 3: Canva Magic Write**
1. Go to canva.com
2. Create TikTok video
3. Use "Magic Write" for captions

### 5.5 TikTok Posting Schedule

**Week 1 (Establish presence):**
- Day 1: Intro video (who you are)
- Day 2: Product demo #1
- Day 3: Before/after #1
- Day 4: Tips video
- Day 5: Product demo #2
- Day 6: Behind the scenes
- Day 7: Before/after #2

**Week 2+ (Scale):**
- 2-3 posts per day
- Mix of: demos, before/after, tips, trending sounds
- Post at 8-9 AM and 7-9 PM EST

### 5.6 Content Batch Creation

**Sunday Batch Session (2 hours):**
1. Write 7 scripts (30 min)
2. Film 7 videos (60 min)
3. Edit in CapCut (30 min)
4. Schedule via Later or TikTok drafts

**Tools:**
- **CapCut**: Free video editing
- **Canva**: Thumbnails and graphics
- **TrendTok**: Find trending sounds
- **Later**: Schedule posts

---

## STEP 6: Launch Checklist

Before going live:

- [ ] Store theme customized
- [ ] Logo uploaded
- [ ] About/Contact/FAQ pages created
- [ ] 10+ products added
- [ ] Pricing has 50%+ margins
- [ ] Shipping rates set
- [ ] Payment connected
- [ ] Domain connected (or .myshopify.com working)
- [ ] TikTok account created (@coaihome)
- [ ] Instagram created (@coaihome)
- [ ] First 3 TikToks filmed
- [ ] Email capture popup installed (Privy)

---

## STEP 7: First Week Action Plan

| Day | Actions |
|-----|---------|
| **Today** | Set up Shopify, connect AI system, create TikTok |
| **Day 2** | Add 5 more products, film 2 TikToks |
| **Day 3** | Customize theme, write About page |
| **Day 4** | Post first TikTok, add 5 more products |
| **Day 5** | Post 2nd TikTok, set up email capture |
| **Day 6** | Post 3rd TikTok, engage with comments |
| **Day 7** | Review analytics, plan Week 2 content |

---

## Quick Reference

**Your Store:**
- URL: coaihome.myshopify.com
- Niche: Home Organization
- Name: CoaiHome
- TikTok: @coaihome
- Target: US millennials/homeowners

**Content Hooks That Work:**
- "Stop doing [problem]..."
- "POV: You finally organized..."
- "This changed everything..."
- "I wish I knew about this sooner..."
- "The space under your [X] is lying to you..."

**Products to Start With:**
1. Drawer organizer
2. Under-sink organizer
3. Fridge bins
4. Closet shelves
5. Pantry organizers

---

Let's GO! 🚀

First task: Get your Shopify API token and add it to your deployment!
