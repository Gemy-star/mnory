import sys
import traceback

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings


class Command(BaseCommand):
    help = "Check Redis/cache and Django Channels realtime chat health."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running realtime health checks..."))

        cache_ok = self.check_cache()
        channels_ok = self.check_channels_layer()

        self.stdout.write("")
        if cache_ok and channels_ok:
            self.stdout.write(self.style.SUCCESS("All realtime checks passed."))
            sys.exit(0)
        else:
            self.stdout.write(self.style.ERROR("One or more realtime checks FAILED."))
            if not cache_ok:
                self.stdout.write(self.style.ERROR(" - Cache / Redis check failed"))
            if not channels_ok:
                self.stdout.write(self.style.ERROR(" - Channels layer check failed"))
            sys.exit(1)

    def check_cache(self) -> bool:
        self.stdout.write("[1/2] Checking cache / Redis connectivity...")
        try:
            test_key = "mnory_realtime_health_check"
            cache.set(test_key, "ok", timeout=5)
            value = cache.get(test_key)
            if value == "ok":
                backend = getattr(settings, "CACHES", {}).get("default", {}).get(
                    "BACKEND", "(unknown)"
                )
                self.stdout.write(
                    self.style.SUCCESS(f"  ✔ Cache operational (backend: {backend})")
                )
                return True
            else:
                self.stdout.write(
                    self.style.ERROR("  ✖ Cache did not return expected value.")
                )
                return False
        except Exception:
            self.stdout.write(self.style.ERROR("  ✖ Error while talking to cache:"))
            self.stdout.write(traceback.format_exc())
            return False

    def check_channels_layer(self) -> bool:
        self.stdout.write("[2/2] Checking Channels layer (Redis / in-memory)...")

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer is None:
                self.stdout.write(
                    self.style.ERROR("  ✖ No channel layer configured (CHANNEL_LAYERS is None).")
                )
                return False

            test_group = "mnory_realtime_health_group"
            test_message = {"type": "health.check", "message": "ping"}

            # We can't easily wait for a consumer here without running ASGI,
            # but we can at least ensure the send() call succeeds.
            async_to_sync(channel_layer.group_send)(test_group, test_message)

            backend = channel_layer.__class__.__module__ + "." + channel_layer.__class__.__name__
            self.stdout.write(
                self.style.SUCCESS(f"  ✔ Channels layer send succeeded (backend: {backend})")
            )
            self.stdout.write(
                "    Note: this command only verifies that sending to the layer works;\n"
                "    you should still test a real WebSocket chat from the browser."
            )

            return True
        except Exception:
            self.stdout.write(self.style.ERROR("  ✖ Error while using channel layer:"))
            self.stdout.write(traceback.format_exc())
            return False
