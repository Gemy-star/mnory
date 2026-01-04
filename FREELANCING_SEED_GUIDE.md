# Freelancing Data Seeding Command

This custom Django management command seeds the database with realistic freelancing platform data including companies, freelancers, projects, proposals, contracts, and more.

## Features

✅ **Automatic image assignment** - Uses images from `static/images/` directory
✅ **Comprehensive data** - Creates complete freelancing ecosystem
✅ **Realistic content** - Uses Faker library for natural-looking data
✅ **Configurable** - Control how much data to generate
✅ **Clear option** - Optionally wipe existing data before seeding

## Usage

### Basic Usage

```bash
python manage.py load_freelancing_data
```

This creates:
- 10 companies
- 15 freelancers
- 20 projects
- Multiple proposals, contracts, payments, reviews, and messages

### Custom Amounts

```bash
python manage.py load_freelancing_data --companies 20 --freelancers 30 --projects 50
```

### Clear Existing Data First

```bash
python manage.py load_freelancing_data --clear
```

⚠️ **Warning:** The `--clear` flag will delete all existing freelancing data including users!

### All Options

```bash
python manage.py load_freelancing_data \
    --companies 15 \
    --freelancers 25 \
    --projects 40 \
    --clear
```

## What Gets Created

### 📁 Categories (8)
- Web Development
- Mobile Development
- Design & Creative
- AI & Machine Learning
- Digital Marketing
- Writing & Translation
- Video & Animation
- Data Science

### 🎯 Skills (60+)
Each category has 6-10 relevant skills

### 🏢 Companies
- Company profiles with logos (from static/images/)
- Various industries and company sizes
- Realistic ratings and verification status
- Locations from major cities worldwide

### 👤 Freelancers
- Complete freelancer profiles with photos (from static/images/)
- Professional titles and bios
- Hourly rates ranging from $15-$150
- Skills, experience levels, and portfolios
- Work history and ratings

### 💼 Projects
- Diverse project types (fixed price and hourly)
- Categories and required skills
- Realistic budgets and timelines
- Open and in-progress statuses
- Featured projects

### 📝 Proposals
- 2-8 proposals per project
- Cover letters and proposed amounts
- Mix of pending and accepted statuses

### 📋 Contracts
- Active and completed contracts
- Start and end dates
- Linked to accepted proposals

### 💰 Payments
- Multiple payments per contract
- Various payment methods (Stripe, PayPal, Bank Transfer)
- Paid and pending statuses

### ⭐ Reviews
- Client reviews for freelancers
- Freelancer reviews for clients
- Ratings from 4-5 stars
- Detailed comments

### 💬 Messages
- Direct messages between users
- Realistic subjects and content
- Read/unread status

## Images

The command automatically uses images from `static/images/` directory:

- **Company logos:** Any image with "logo" in filename
- **Freelancer profiles:** Images with "man", "woman", "person", or "kid" in filename
- **Fallback:** Random images if specific ones aren't available

### Current Available Images
```
- kid.jpg
- logo-black.png
- logo-solgan.png
- logo.png
- man.jpg
- men.jpg
- slide1.jpg
- slide2.jpg
- slide3.jpg
- woman.jpg
```

## Test Credentials

All seeded users have the same password for easy testing:

**Password:** `password123`

Sample accounts will be displayed after seeding:
- Company example: `company1@techvisionsolutions.com`
- Freelancer example: `john.doe1@freelancer.com`

## Requirements

```bash
pip install faker
```

## Output Example

```
Loading dummy data with images...
Found 10 images in static/images/
  Created category: Web Development
  Created category: Mobile Development
  ...
  Created 10 companies
  Created 15 freelancers
  Created 20 projects
  Created 85 proposals
  Created 10 contracts
  Created 22 payments
  Created 14 reviews
  Created 30 messages

============================================================
✅ Freelancing Data Seeding Complete!
============================================================
  📁 Categories: 8
  🎯 Skills: 67
  🏢 Companies: 10
  👤 Freelancers: 15
  💼 Projects: 20
  📝 Proposals: 85
  📋 Contracts: 10
  💰 Payments: 22
  ⭐ Reviews: 14
  💬 Messages: 30
============================================================

Test credentials: All users have password: password123
  Sample company: company1@techvisionsolutions.com
  Sample freelancer: john.doe1@freelancer.com
```

## Tips

1. **Run migrations first:**
   ```bash
   python manage.py migrate
   ```

2. **Start fresh:** Use `--clear` to remove old test data
   ```bash
   python manage.py load_freelancing_data --clear
   ```

3. **Add more images:** Place additional images in `static/images/` before running

4. **Customize amounts:** Adjust numbers based on your testing needs

5. **Performance:** Larger datasets take longer to generate (expect 30-60 seconds for default amounts)

## Troubleshooting

### "No module named faker"
```bash
pip install faker
```

### Media files not showing
Make sure `MEDIA_ROOT` and `MEDIA_URL` are configured in your Django settings:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Images not copying
Ensure `static/images/` directory exists and contains image files

## Related Commands

- View data in Django admin: `/admin/`
- Browse companies: `/companies/`
- Browse freelancers: `/freelancers/`
- Browse projects: `/projects/`

## Notes

- The command is idempotent when not using `--clear` - it will create new data without duplicating
- Emails are generated uniquely to avoid conflicts
- All timestamps are randomized for realistic-looking data
- Skills are automatically associated with appropriate categories
- Proposals are linked to relevant freelancers based on their skills
