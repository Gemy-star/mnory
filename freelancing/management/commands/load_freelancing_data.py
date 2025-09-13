import random
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from shop.models import MnoryUser as User
from django.utils import timezone
from faker import Faker

from freelancing.models import (
    Project, Proposal, Contract, Payment, Message, Review,
    FreelancerProfile, CompanyProfile, Skill, Category
)

fake = Faker()


class Command(BaseCommand):
    help = "Load dummy data for testing (projects, freelancers, companies, etc.)"

    def add_arguments(self, parser):
        parser.add_argument('--projects', type=int, default=10, help="Number of projects to create")
        parser.add_argument('--freelancers', type=int, default=5, help="Number of freelancers to create")
        parser.add_argument('--companies', type=int, default=3, help="Number of companies to create")

    def handle(self, *args, **options):
        num_projects = options['projects']
        num_freelancers = options['freelancers']
        num_companies = options['companies']

        self.stdout.write(self.style.SUCCESS("Loading dummy data..."))

        # --- Create Categories ---
        category_names = ["Web Development", "Design", "AI/ML", "Mobile Apps"]
        categories = []
        for c in category_names:
            category, _ = Category.objects.get_or_create(
                name=c,
                defaults={"slug": c.lower().replace(" ", "-")}
            )
            categories.append(category)

        # --- Create Skills ---
        skill_map = {
            "Web Development": ["Python", "Django", "React", "DevOps"],
            "Design": ["UI/UX", "Figma", "Illustrator"],
            "AI/ML": ["Machine Learning", "Deep Learning", "NLP"],
            "Mobile Apps": ["Flutter", "React Native", "Swift"]
        }
        skills = []
        for cat in categories:
            for s in skill_map[cat.name]:
                skill, _ = Skill.objects.get_or_create(name=s, category=cat)
                skills.append(skill)

        # --- Create Companies ---
        companies = []
        for _ in range(num_companies):
            user = User.objects.create_user(
                username=fake.user_name() + str(uuid.uuid4())[:6],
                email=fake.email(),
                password="password123",
                user_type="company",
            )
            company = CompanyProfile.objects.create(
                user=user,
                company_name=fake.company(),
                description=fake.text(max_nb_chars=200),
                industry=random.choice(["Tech", "Design", "Marketing"]),
                location=fake.city(),
                company_size=random.choice(["1-10", "11-50", "51-200"]),
            )
            companies.append(company)

        # --- Create Freelancers ---
        freelancers = []
        for _ in range(num_freelancers):
            user = User.objects.create_user(
                username=fake.user_name() + str(uuid.uuid4())[:6],
                email=fake.email(),
                password="password123",
                user_type="freelancer",
            )
            freelancer = FreelancerProfile.objects.create(
                user=user,
                title=fake.job(),
                bio=fake.text(max_nb_chars=150),
                hourly_rate=random.randint(10, 100),
                experience_level=random.choice(["junior", "mid", "senior"]),
            )
            freelancer.skills.add(*random.sample(skills, k=random.randint(1, 3)))
            freelancers.append(freelancer)

        # --- Create Projects ---
        projects = []
        for _ in range(num_projects):
            client = random.choice(companies).user
            category = random.choice(categories)
            project = Project.objects.create(
                client=client,
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=400),
                category=category,
                project_type=random.choice(["fixed", "hourly"]),
                budget_min=random.randint(100, 500),
                budget_max=random.randint(600, 2000),
                estimated_duration=random.choice(["1 week", "1 month", "3 months"]),
                experience_level=random.choice(["junior", "mid", "senior"]),
                deadline=timezone.now() + timedelta(days=random.randint(7, 60)),
                status="open",
            )
            project.skills_required.add(*random.sample(
                [s for s in skills if s.category == category],
                k=random.randint(1, 3)
            ))
            projects.append(project)

        # --- Create Proposals ---
        for project in projects:
            used_freelancers = set()
            for _ in range(random.randint(1, 4)):
                freelancer = random.choice(freelancers).user
                if freelancer.id in used_freelancers:
                    continue

                Proposal.objects.get_or_create(
                    project=project,
                    freelancer=freelancer,
                    defaults={
                        "cover_letter": fake.text(max_nb_chars=300),
                        "proposed_amount": random.randint(200, 1000),
                        "status": "pending",
                    }
                )
                used_freelancers.add(freelancer.id)

        # --- Create Contracts + Payments + Reviews ---
        for project in random.sample(projects, k=min(5, len(projects))):
            proposal = project.proposals.first()
            if proposal:
                contract = Contract.objects.create(
                    project=project,
                    client=project.client,
                    freelancer=proposal.freelancer,
                    proposal=proposal,
                    title=project.title,
                    description=project.description,
                    amount=proposal.proposed_amount,
                    start_date=timezone.now(),
                    status=random.choice(["active", "completed"]),
                )

                # Payments
                for _ in range(random.randint(1, 3)):
                    Payment.objects.create(
                        contract=contract,
                        amount=random.randint(50, 500),
                        description=fake.sentence(),
                        status=random.choice(["pending", "paid"]),
                    )

                # Reviews
                if contract.status == "completed":
                    Review.objects.create(
                        contract=contract,
                        reviewer=contract.client,
                        reviewee=contract.freelancer,
                        rating=random.randint(3, 5),
                        comment=fake.text(max_nb_chars=150),
                        is_public=True,
                    )

        # --- Create Messages ---
        for _ in range(20):
            sender_profile = random.choice(freelancers + companies)
            recipient_profile = random.choice(
                [p for p in (freelancers + companies) if p.user != sender_profile.user]
            )
            Message.objects.create(
                sender=sender_profile.user,
                recipient=recipient_profile.user,
                subject=fake.sentence(),
                message=fake.text(max_nb_chars=200),
            )

        self.stdout.write(self.style.SUCCESS("✅ Dummy data created successfully!"))
