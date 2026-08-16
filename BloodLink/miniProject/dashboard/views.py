from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from notifications.models import Notification
from donors.models import Donation


@login_required
def dashboard(request):
    if hasattr(request.user, 'hospital_profile'):
        return redirect('hospital_dashboard')

    donor = request.user.donor_profile

    notifications = Notification.objects.filter(
        donor=donor
    ).select_related(
        'blood_request',
        'blood_request__hospital'
    ).order_by('-sent_at')

    completed_donations = set(
        Donation.objects.filter(
            donor=donor
        ).values_list(
            'blood_request_id',
            flat=True
        )
    )

    return render(
        request,
        'dashboard.html',
        {
            'notifications': notifications,
            'completed_donations': completed_donations,
        }
    )


@login_required
def toggle_availability(request):
    if not hasattr(request.user, 'donor_profile'):
        return redirect('dashboard')

    if request.method == 'POST':

        donor = request.user.donor_profile

        donor.is_available = not donor.is_available

        donor.save()
    return redirect('dashboard')