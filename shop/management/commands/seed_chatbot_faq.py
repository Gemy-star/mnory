from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import override

from constance import config

from shop.models import ChatbotQuestion


class Command(BaseCommand):
    help = "Seed common chatbot FAQ questions and answers using About, Terms, and Policy content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            dest="overwrite",
            help="Overwrite existing answers for the same question/language.",
        )

    def handle(self, *args, **options):
        overwrite = options.get("overwrite", False)

        company_name = (config.COMPANY_NAME or "Mnory").strip()
        company_desc = (config.COMPANY_DESCRIPTION or "").strip()

        def safe_render_text(template_name: str, lang: str) -> str:
            """Render a template for a given language and strip HTML to plain text.

            Falls back to an empty string on error.
            """

            try:
                with override(lang):
                    html = render_to_string(template_name, {"config": config})
                text = strip_tags(html or "").strip()
                # Keep it reasonably short for chatbot-style answers
                return text[:1200]
            except Exception:
                return ""

        # Extract text for terms & policy in both languages (best-effort)
        terms_en = safe_render_text("shop/terms.html", "en")
        terms_ar = safe_render_text("shop/terms.html", "ar")
        policy_en = safe_render_text("shop/policy.html", "en")
        policy_ar = safe_render_text("shop/policy.html", "ar")

        if not company_desc:
            company_desc = (
                f"{company_name} is a fashion and lifestyle platform focused on quality "
                f"products and reliable delivery."
            )

        faq_items = [
            # About Mnory (English)
            {
                "question": "What is Mnory?",
                "language_code": "en",
                "answer": company_desc,
                "source_path": "/",
            },
            # About Mnory (Arabic)
            {
                "question": "ما هو منوري؟",
                "language_code": "ar",
                "answer": company_desc,
                "source_path": "/",
            },
            # Privacy / data protection (English)
            {
                "question": "How do you protect my data?",
                "language_code": "en",
                "answer": (
                    (policy_en or "")
                    or (
                        "We collect only the information needed to process your orders, "
                        "secure your account, and improve your shopping experience. "
                        "Your data is protected with encryption and strict access controls. "
                        "You can review the full details in our Privacy Policy page."
                    )
                ),
                "source_path": "/policy/",
            },
            # Privacy / data protection (Arabic)
            {
                "question": "كيف تحمون بياناتي؟",
                "language_code": "ar",
                "answer": policy_ar or policy_en or "",
                "source_path": "/policy/",
            },
            # Terms & conditions (English)
            {
                "question": "What are your terms and conditions?",
                "language_code": "en",
                "answer": (
                    (terms_en or "")
                    or (
                        "By using Mnory you agree to our Terms of Service. "
                        "They explain how you can use the platform, payment and delivery "
                        "rules, and limitations of our responsibility. "
                        "For the full legal text, please read the Terms of Service page."
                    )
                ),
                "source_path": "/terms/",
            },
            # Terms & conditions (Arabic)
            {
                "question": "ما هي الشروط والأحكام؟",
                "language_code": "ar",
                "answer": terms_ar or terms_en or "",
                "source_path": "/terms/",
            },
        ]

        created = 0
        updated = 0

        for item in faq_items:
            question = (item["question"] or "").strip()
            if not question:
                continue
            lang_code = item["language_code"]
            defaults = {
                "answer": item.get("answer", "").strip(),
                "language_code": lang_code,
                "source_path": item.get("source_path", "") or "",
            }

            obj, was_created = ChatbotQuestion.objects.get_or_create(
                question=question,
                language_code=lang_code,
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                if overwrite:
                    changed = False
                    if obj.answer != defaults["answer"]:
                        obj.answer = defaults["answer"]
                        changed = True
                    if obj.source_path != defaults["source_path"]:
                        obj.source_path = defaults["source_path"]
                        changed = True
                    if changed:
                        obj.save(update_fields=["answer", "source_path"])
                        updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} chatbot FAQ entries; updated {updated} existing entries."
            )
        )
