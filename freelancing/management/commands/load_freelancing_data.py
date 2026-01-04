import random
import uuid
import os
import shutil
from pathlib import Path
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from shop.models import MnoryUser as User
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from freelancing.models import (
    Project,
    Proposal,
    Contract,
    Payment,
    Message,
    Review,
    FreelancerProfile,
    CompanyProfile,
    Skill,
    Category,
)

fake = Faker()


class Command(BaseCommand):
    help = "Load dummy data for testing (projects, freelancers, companies, etc.) with images from static/images"

    def add_arguments(self, parser):
        parser.add_argument(
            "--projects", type=int, default=20, help="Number of projects to create"
        )
        parser.add_argument(
            "--freelancers",
            type=int,
            default=15,
            help="Number of freelancers to create",
        )
        parser.add_argument(
            "--companies", type=int, default=10, help="Number of companies to create"
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing freelancing data before seeding",
        )

    def handle(self, *args, **options):
        num_projects = options["projects"]
        num_freelancers = options["freelancers"]
        num_companies = options["companies"]
        clear_data = options["clear"]

        if clear_data:
            self.stdout.write(
                self.style.WARNING("Clearing existing freelancing data...")
            )
            Message.objects.all().delete()
            Review.objects.all().delete()
            Payment.objects.all().delete()
            Contract.objects.all().delete()
            Proposal.objects.all().delete()
            Project.objects.all().delete()
            FreelancerProfile.objects.all().delete()
            CompanyProfile.objects.all().delete()
            # Delete users created for freelancing
            User.objects.filter(user_type__in=["freelancer", "company"]).delete()
            # Delete skills and categories to avoid UNIQUE constraint errors
            Skill.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✅ Cleared existing data!"))

        self.stdout.write(self.style.SUCCESS("Loading dummy data with images..."))

        # Get available images from static/images
        static_images_path = os.path.join(settings.BASE_DIR, "static", "images")
        available_images = []
        if os.path.exists(static_images_path):
            available_images = [
                f
                for f in os.listdir(static_images_path)
                if f.lower().endswith((".jpg", ".png", ".jpeg"))
            ]
            self.stdout.write(f"Found {len(available_images)} images in static/images/")

        # --- Create Categories ---
        category_data = [
            {
                "name": "Web Development",
                "description": "Full-stack, backend, and frontend development",
            },
            {
                "name": "Mobile Development",
                "description": "iOS, Android, and cross-platform apps",
            },
            {
                "name": "Design & Creative",
                "description": "UI/UX, graphic design, and branding",
            },
            {
                "name": "AI & Machine Learning",
                "description": "ML models, data science, and AI solutions",
            },
            {
                "name": "Digital Marketing",
                "description": "SEO, social media, and content marketing",
            },
            {
                "name": "Writing & Translation",
                "description": "Content writing, copywriting, and translation",
            },
            {
                "name": "Video & Animation",
                "description": "Video editing, motion graphics, and 3D animation",
            },
            {
                "name": "Data Science",
                "description": "Data analysis, visualization, and business intelligence",
            },
        ]

        categories = []
        for cat_data in category_data:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "slug": slugify(cat_data["name"]),
                    "description": cat_data["description"],
                },
            )
            categories.append(category)
            if created:
                self.stdout.write(f"  Created category: {category.name}")

        # --- Create Skills ---
        skill_map = {
            "Web Development": [
                "Python",
                "Django",
                "React",
                "Vue.js",
                "Node.js",
                "PHP",
                "Laravel",
                "Angular",
                "TypeScript",
                "JavaScript",
            ],
            "Mobile Development": [
                "Flutter",
                "React Native",
                "Swift",
                "Kotlin",
                "iOS",
                "Android",
                "Xamarin",
            ],
            "Design & Creative": [
                "UI/UX Design",
                "Figma",
                "Adobe XD",
                "Photoshop",
                "Illustrator",
                "Sketch",
                "InVision",
                "Branding",
            ],
            "AI & Machine Learning": [
                "Machine Learning",
                "Deep Learning",
                "TensorFlow",
                "PyTorch",
                "NLP",
                "Computer Vision",
                "Data Mining",
            ],
            "Digital Marketing": [
                "SEO",
                "SEM",
                "Social Media Marketing",
                "Content Marketing",
                "Email Marketing",
                "Google Ads",
                "Facebook Ads",
            ],
            "Writing & Translation": [
                "Content Writing",
                "Copywriting",
                "Technical Writing",
                "Translation",
                "Proofreading",
                "Blogging",
            ],
            "Video & Animation": [
                "Video Editing",
                "After Effects",
                "Premiere Pro",
                "Motion Graphics",
                "3D Animation",
                "Blender",
            ],
            "Data Science": [
                "Python",
                "R",
                "SQL",
                "Tableau",
                "Power BI",
                "Data Analysis",
                "Statistics",
                "Excel",
            ],
        }

        skills = []
        for cat in categories:
            if cat.name in skill_map:
                for skill_name in skill_map[cat.name]:
                    skill, created = Skill.objects.get_or_create(
                        name=skill_name, defaults={"category": cat}
                    )
                    skills.append(skill)

        self.stdout.write(
            f"  Created {len(skills)} skills across {len(categories)} categories"
        )

        # --- Create Companies ---
        company_names = [
            "TechVision Solutions",
            "Digital Dynamics Inc",
            "Creative Minds Studio",
            "InnovateLab",
            "CodeCraft Technologies",
            "DesignHub Agency",
            "DataDriven Analytics",
            "CloudNine Systems",
            "SmartBiz Solutions",
            "FutureTech Innovations",
            "WebWorks Pro",
            "AppGenius",
            "BrandBuilders Co",
            "MarketMasters",
            "ContentCreators LLC",
        ]

        industries = [
            "Technology",
            "E-commerce",
            "Healthcare",
            "Finance",
            "Education",
            "Marketing",
            "Media",
            "Consulting",
            "Retail",
            "Manufacturing",
        ]

        locations = [
            "New York, NY",
            "San Francisco, CA",
            "London, UK",
            "Berlin, Germany",
            "Toronto, Canada",
            "Sydney, Australia",
            "Dubai, UAE",
            "Singapore",
            "Paris, France",
            "Amsterdam, Netherlands",
            "Cairo, Egypt",
        ]

        companies = []
        for i in range(num_companies):
            company_name = company_names[i % len(company_names)]
            email = f"company{i+1}@{slugify(company_name).replace('-', '')}.com"

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"  User {email} already exists, skipping...")
                )
                continue

            username = f"company{i+1}"
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                user_type="company",
                first_name=company_name.split()[0],
                last_name="Inc" if i % 2 == 0 else "LLC",
            )

            company = CompanyProfile.objects.create(
                user=user,
                company_name=company_name,
                description=fake.text(max_nb_chars=300),
                industry=random.choice(industries),
                location=random.choice(locations),
                company_size=random.choice(
                    ["1-10", "11-50", "51-200", "201-500", "500+"]
                ),
                founded_year=random.randint(2010, 2024),
                rating=round(random.uniform(3.5, 5.0), 1),
                is_verified=random.choice([True, True, False]),  # 66% verified
            )

            # Add company logo from static images
            if available_images:
                logo_image = random.choice(
                    [img for img in available_images if "logo" in img.lower()]
                    or available_images
                )
                source_path = os.path.join(static_images_path, logo_image)

                # Copy image to media directory
                media_path = os.path.join(settings.MEDIA_ROOT, "company_logos")
                os.makedirs(media_path, exist_ok=True)
                dest_filename = f"company_{i+1}_{logo_image}"
                dest_path = os.path.join(media_path, dest_filename)

                shutil.copy2(source_path, dest_path)
                company.logo = f"company_logos/{dest_filename}"
                company.save()

            companies.append(company)

        self.stdout.write(self.style.SUCCESS(f"  Created {len(companies)} companies"))

        # --- Create Freelancers ---
        freelancer_titles = [
            "Full Stack Developer",
            "Frontend Developer",
            "Backend Developer",
            "UI/UX Designer",
            "Graphic Designer",
            "Web Designer",
            "Mobile App Developer",
            "Data Scientist",
            "Machine Learning Engineer",
            "SEO Specialist",
            "Content Writer",
            "Digital Marketing Expert",
            "Video Editor",
            "3D Artist",
            "Motion Graphics Designer",
            "Python Developer",
            "React Developer",
            "WordPress Developer",
        ]

        freelancers = []
        for i in range(num_freelancers):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{i+1}@freelancer.com"

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"  User {email} already exists, skipping...")
                )
                continue

            username = f"{first_name.lower()}{last_name.lower()}{i+1}"
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                user_type="freelancer",
                first_name=first_name,
                last_name=last_name,
            )

            title = random.choice(freelancer_titles)
            experience_level = random.choice(["entry", "intermediate", "expert"])

            freelancer = FreelancerProfile.objects.create(
                user=user,
                title=title,
                bio=fake.text(max_nb_chars=250),
                hourly_rate=random.randint(15, 150),
                experience_level=experience_level,
                languages="English, Arabic" if i % 3 == 0 else "English",
                location=random.choice(locations),
                availability=random.choice(["full_time", "part_time", "contract"]),
                rating=round(random.uniform(3.8, 5.0), 1),
                total_jobs_completed=random.randint(5, 100),
                total_earnings=random.randint(1000, 50000),
                is_verified=random.choice([True, True, False]),  # 66% verified
                portfolio_url=(
                    f"https://portfolio.{first_name.lower()}{last_name.lower()}.com"
                    if i % 3 == 0
                    else ""
                ),
                linkedin_url=(
                    f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}"
                    if i % 2 == 0
                    else ""
                ),
                github_url=(
                    f"https://github.com/{first_name.lower()}{last_name.lower()}"
                    if "Developer" in title
                    else ""
                ),
            )

            # Add profile picture from static images
            if available_images:
                # Try to get gender-appropriate image
                profile_images = [
                    img
                    for img in available_images
                    if any(
                        keyword in img.lower()
                        for keyword in ["man", "woman", "person", "kid"]
                    )
                ]
                if profile_images:
                    profile_image = random.choice(profile_images)
                else:
                    profile_image = random.choice(available_images)

                source_path = os.path.join(static_images_path, profile_image)

                # Copy image to media directory
                media_path = os.path.join(settings.MEDIA_ROOT, "freelancer_profiles")
                os.makedirs(media_path, exist_ok=True)
                dest_filename = f"freelancer_{i+1}_{profile_image}"
                dest_path = os.path.join(media_path, dest_filename)

                shutil.copy2(source_path, dest_path)
                freelancer.profile_picture = f"freelancer_profiles/{dest_filename}"
                freelancer.save()

            # Add skills (3-5 relevant skills)
            relevant_skills = [
                s for s in skills if any(keyword in title for keyword in s.name.split())
            ]
            if not relevant_skills:
                relevant_skills = skills

            selected_skills = random.sample(
                relevant_skills, k=min(random.randint(3, 5), len(relevant_skills))
            )
            freelancer.skills.add(*selected_skills)

            freelancers.append(freelancer)

        self.stdout.write(
            self.style.SUCCESS(f"  Created {len(freelancers)} freelancers")
        )

        # --- Create Projects ---
        project_titles = [
            "E-commerce Website Development",
            "Mobile App for Food Delivery",
            "Corporate Website Redesign",
            "CRM System Integration",
            "AI Chatbot Development",
            "Social Media Marketing Campaign",
            "Logo and Brand Identity Design",
            "Data Analytics Dashboard",
            "SEO Optimization for Website",
            "Video Production and Editing",
            "Mobile Game Development",
            "API Development and Integration",
            "Content Writing for Blog",
            "Email Marketing Automation",
            "3D Product Visualization",
            "Machine Learning Model Development",
            "WordPress Plugin Development",
            "UI/UX Design for SaaS Platform",
            "Database Optimization",
            "Cloud Migration Project",
        ]

        project_descriptions = [
            "We need a professional to help us build a modern, scalable solution that meets our business needs.",
            "Looking for an experienced developer to create a custom application with clean code and best practices.",
            "Seeking a talented designer to create stunning visuals that align with our brand identity.",
            "Need an expert to implement advanced features and integrate with third-party services.",
            "We're looking for someone who can deliver high-quality work within the specified timeline.",
            "This project requires strong attention to detail and excellent communication skills.",
            "Looking for a creative professional who can bring fresh ideas to the table.",
            "We need someone with proven experience in similar projects and a strong portfolio.",
            "Seeking a reliable freelancer who can work independently and meet deadlines.",
            "Looking for an expert who can provide ongoing support and maintenance after delivery.",
        ]

        projects = []
        for i in range(num_projects):
            if not companies:
                self.stdout.write(
                    self.style.WARNING("No companies available to create projects")
                )
                break

            client = random.choice(companies).user
            category = random.choice(categories)
            project_type = random.choice(["fixed", "hourly"])

            title = project_titles[i % len(project_titles)]
            description = f"{fake.text(max_nb_chars=200)}\n\n{random.choice(project_descriptions)}\n\n{fake.text(max_nb_chars=150)}"

            project_data = {
                "client": client,
                "title": title,
                "description": description,
                "category": category,
                "project_type": project_type,
                "estimated_duration": random.choice(
                    [
                        "Less than 1 week",
                        "1-2 weeks",
                        "1 month",
                        "2-3 months",
                        "3-6 months",
                    ]
                ),
                "experience_level": random.choice(["entry", "intermediate", "expert"]),
                "deadline": timezone.now() + timedelta(days=random.randint(14, 90)),
                "status": random.choice(
                    ["open", "open", "open", "in_progress"]
                ),  # More open projects
                "is_featured": random.choice(
                    [True, False, False, False]
                ),  # 25% featured
                "views_count": random.randint(10, 500),
                "proposals_count": random.randint(0, 15),
            }

            if project_type == "fixed":
                project_data["budget_min"] = random.randint(500, 2000)
                project_data["budget_max"] = project_data[
                    "budget_min"
                ] + random.randint(500, 3000)
            else:
                project_data["hourly_rate_min"] = random.randint(15, 50)
                project_data["hourly_rate_max"] = project_data[
                    "hourly_rate_min"
                ] + random.randint(20, 100)

            project = Project.objects.create(**project_data)

            # Add required skills (2-4 skills from category)
            category_skills = [s for s in skills if s.category == category]
            if category_skills:
                selected_skills = random.sample(
                    category_skills, k=min(random.randint(2, 4), len(category_skills))
                )
                project.skills_required.add(*selected_skills)

            projects.append(project)

        self.stdout.write(self.style.SUCCESS(f"  Created {len(projects)} projects"))

        # --- Create Proposals ---
        proposals_created = 0
        if freelancers and projects:
            for project in projects:
                num_proposals = random.randint(2, 8)
                selected_freelancers = random.sample(
                    freelancers, k=min(num_proposals, len(freelancers))
                )

                for freelancer in selected_freelancers:
                    proposal, created = Proposal.objects.get_or_create(
                        project=project,
                        freelancer=freelancer.user,
                        defaults={
                            "cover_letter": f"{fake.text(max_nb_chars=200)}\n\nI believe I'm a perfect fit for this project because of my experience in {random.choice([s.name for s in freelancer.skills.all()] or ['my field'])}. I can deliver high-quality work within your timeline.\n\n{fake.text(max_nb_chars=150)}",
                            "proposed_amount": (
                                random.randint(
                                    int(project.budget_min or 500),
                                    int(project.budget_max or 2000),
                                )
                                if project.project_type == "fixed"
                                else random.randint(300, 1500)
                            ),
                            "estimated_duration": f"{random.randint(7, 30)} days",
                            "status": random.choice(
                                ["pending", "pending", "pending", "accepted"]
                            ),
                        },
                    )
                    if created:
                        proposals_created += 1
                        project.proposals_count = project.proposals.count()
                        project.save()

        self.stdout.write(
            self.style.SUCCESS(f"  Created {proposals_created} proposals")
        )

        # --- Create Contracts + Payments + Reviews ---
        contracts_created = 0
        payments_created = 0
        reviews_created = 0

        if projects and freelancers:
            for project in random.sample(projects, k=min(10, len(projects))):
                accepted_proposals = project.proposals.filter(status="accepted")
                if accepted_proposals.exists():
                    proposal = accepted_proposals.first()
                    contract_status = random.choice(
                        ["active", "completed", "completed"]
                    )

                    contract = Contract.objects.create(
                        project=project,
                        client=project.client,
                        freelancer=proposal.freelancer,
                        proposal=proposal,
                        title=project.title,
                        description=project.description,
                        amount=proposal.proposed_amount,
                        start_date=timezone.now()
                        - timedelta(days=random.randint(1, 60)),
                        end_date=(
                            timezone.now() + timedelta(days=random.randint(7, 60))
                            if contract_status == "active"
                            else timezone.now() - timedelta(days=random.randint(1, 10))
                        ),
                        status=contract_status,
                    )
                    contracts_created += 1

                    # Payments
                    num_payments = random.randint(1, 3)
                    for i in range(num_payments):
                        payment_status = (
                            "completed"
                            if contract_status == "completed"
                            else random.choice(["pending", "completed", "completed"])
                        )
                        Payment.objects.create(
                            contract=contract,
                            amount=contract.amount / num_payments,
                            description=f"Payment {i + 1} of {num_payments} for {contract.title}",
                            payment_type=random.choice(
                                ["milestone", "hourly", "bonus"]
                            ),
                            status=payment_status,
                            paid_date=(
                                timezone.now() - timedelta(days=random.randint(1, 30))
                                if payment_status == "completed"
                                else None
                            ),
                            transaction_id=f"TXN{random.randint(100000, 999999)}",
                        )
                        payments_created += 1

                    # Reviews
                    if contract_status == "completed":
                        Review.objects.create(
                            contract=contract,
                            reviewer=contract.client,
                            reviewee=contract.freelancer,
                            rating=random.randint(4, 5),
                            comment=f"{fake.text(max_nb_chars=150)}\n\nHighly professional and delivered excellent work!",
                            is_public=True,
                        )
                        reviews_created += 1

                        if random.choice([True, False]):
                            Review.objects.create(
                                contract=contract,
                                reviewer=contract.freelancer,
                                reviewee=contract.client,
                                rating=random.randint(4, 5),
                                comment=f"Great client to work with. {fake.sentence()}",
                                is_public=True,
                            )
                            reviews_created += 1

        self.stdout.write(
            self.style.SUCCESS(f"  Created {contracts_created} contracts")
        )
        self.stdout.write(self.style.SUCCESS(f"  Created {payments_created} payments"))
        self.stdout.write(self.style.SUCCESS(f"  Created {reviews_created} reviews"))

        # --- Create Messages ---
        messages_created = 0
        if freelancers and companies:
            all_users = [f.user for f in freelancers] + [c.user for c in companies]

            for _ in range(min(30, len(all_users) * 2)):
                sender = random.choice(all_users)
                possible_recipients = [u for u in all_users if u != sender]
                if possible_recipients:
                    recipient = random.choice(possible_recipients)

                    subject_templates = [
                        "Question about your project",
                        "Interested in working together",
                        "Project proposal discussion",
                        "Follow-up on our conversation",
                        "Clarification needed",
                    ]

                    Message.objects.create(
                        sender=sender,
                        recipient=recipient,
                        subject=random.choice(subject_templates),
                        message=f"{fake.text(max_nb_chars=300)}\n\nBest regards,\n{sender.get_full_name() or sender.email}",
                        is_read=random.choice([True, False, False]),
                    )
                    messages_created += 1

        self.stdout.write(self.style.SUCCESS(f"  Created {messages_created} messages"))

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("✅ Freelancing Data Seeding Complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  📁 Categories: {len(categories)}")
        self.stdout.write(f"  🎯 Skills: {len(skills)}")
        self.stdout.write(f"  🏢 Companies: {len(companies)}")
        self.stdout.write(f"  👤 Freelancers: {len(freelancers)}")
        self.stdout.write(f"  💼 Projects: {len(projects)}")
        self.stdout.write(f"  📝 Proposals: {proposals_created}")
        self.stdout.write(f"  📋 Contracts: {contracts_created}")
        self.stdout.write(f"  💰 Payments: {payments_created}")
        self.stdout.write(f"  ⭐ Reviews: {reviews_created}")
        self.stdout.write(f"  💬 Messages: {messages_created}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("Test credentials: All users have password: password123")
        if companies:
            self.stdout.write(f"  Sample company: {companies[0].user.email}")
        if freelancers:
            self.stdout.write(f"  Sample freelancer: {freelancers[0].user.email}")
