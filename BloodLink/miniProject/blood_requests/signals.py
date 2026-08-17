from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BloodRequest
from donors.models import DonorProfile
from notifications.services import create_notification
from notifications.email_utils import send_blood_request_email
from donors.utils import calculate_distance


@receiver(post_save, sender=BloodRequest)
def notify_donors_on_blood_request(sender, instance, created, **kwargs):

    if not created:
        return

    print("🔥 BLOOD REQUEST SIGNAL IS RUNNING!")

    has_coordinates = bool(instance.latitude and instance.longitude)

    # Base filter: matching blood group, available, eligible
    base_qs = DonorProfile.objects.filter(
        blood_group=instance.blood_group,
        is_available=True,
    ).select_related('user')

    if has_coordinates:
        # Prefer donors with coordinates for distance sorting
        donors_with_coords = base_qs.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        donors_without_coords = base_qs.filter(
            latitude__isnull=True,
            district=instance.district
        )
    else:
        # No coordinates on request — fall back to same district
        donors_with_coords = DonorProfile.objects.none()
        donors_without_coords = base_qs.filter(district=instance.district)

    print(f"🔥 DONORS WITH COORDS: {donors_with_coords.count()}, WITHOUT: {donors_without_coords.count()}")

    nearby_donors = []

    for donor in donors_with_coords:
        if not donor.is_eligible():
            continue
        distance = calculate_distance(
            instance.latitude, instance.longitude,
            donor.latitude, donor.longitude
        )
        nearby_donors.append((distance, donor))

    nearby_donors.sort(key=lambda x: x[0])

    # Fill remaining slots from same-district donors without coords
    slots_remaining = 10 - len(nearby_donors[:10])
    fallback_donors = [
        (None, d) for d in donors_without_coords
        if d.is_eligible()
    ][:slots_remaining]

    final_donors = nearby_donors[:10] + fallback_donors

    print(f"🔥 TOTAL DONORS TO NOTIFY: {len(final_donors)}")

    for entry in final_donors:
        distance, donor = entry

        if distance is not None:
            message = (
                f"Emergency blood request for {instance.blood_group} blood "
                f"at {instance.hospital.hospital_name}. "
                f"You are approximately {distance:.2f} km away."
            )
        else:
            message = (
                f"Emergency blood request for {instance.blood_group} blood "
                f"at {instance.hospital.hospital_name} in {instance.district}."
            )

        print(f"📧 NOTIFYING: {donor.user.username}")

        create_notification(
            donor=donor,
            blood_request=instance,
            message=message
        )

        send_blood_request_email(donor, instance)

        print(f"✅ DONE: {donor.user.username}")