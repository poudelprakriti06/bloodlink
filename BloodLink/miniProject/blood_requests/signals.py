from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BloodRequest
from donors.models import DonorProfile
from notifications.services import create_notification
from notifications.email_utils import send_blood_request_email
from donors.utils import calculate_distance


@receiver(post_save, sender=BloodRequest)
def notify_donors_on_blood_request(sender, instance, created, **kwargs):

    # Only run when a new blood request is created
    if not created:
        return

    print("🔥 BLOOD REQUEST SIGNAL IS RUNNING!")

    # Safety check: request must have coordinates
    if not instance.latitude or not instance.longitude:
        print("❌ Blood request has no coordinates!")
        return

    # Find donors with matching blood group and location data
    matching_donors = DonorProfile.objects.filter(
        blood_group=instance.blood_group,
        is_available=True,
        latitude__isnull=False,
        longitude__isnull=False
    )

    print("🔥 MATCHING DONORS:", matching_donors.count())

    nearby_donors = []

    # Calculate distance for each eligible donor
    for donor in matching_donors:

        print("🔥 CHECKING DONOR:", donor.user.username)

        if donor.is_eligible():

            print("✅ DONOR IS ELIGIBLE:", donor.user.username)

            distance = calculate_distance(
                instance.latitude,
                instance.longitude,
                donor.latitude,
                donor.longitude
            )

            print(
                f"📍 DISTANCE FROM REQUEST TO {donor.user.username}: "
                f"{distance:.2f} km"
            )

            nearby_donors.append(
                (distance, donor)
            )

        else:
            print("❌ DONOR IS NOT ELIGIBLE:", donor.user.username)

    # Sort donors from nearest to farthest
    nearby_donors.sort(key=lambda x: x[0])

    print("🔥 NEARBY ELIGIBLE DONORS:", len(nearby_donors))

    # Notify only top 10 nearest donors
    for distance, donor in nearby_donors[:10]:

        print("📧 CREATING NOTIFICATION FOR:", donor.user.username)

        message = (
            f"Emergency blood request for {instance.blood_group} blood "
            f"at {instance.hospital.hospital_name}. "
            f"You are approximately {distance:.2f} km away."
        )

        create_notification(
            donor=donor,
            blood_request=instance,
            message=message
        )

        print("✅ NOTIFICATION CREATED!")

        send_blood_request_email(
            donor,
            instance
        )

        print("📧 EMAIL SENT!")