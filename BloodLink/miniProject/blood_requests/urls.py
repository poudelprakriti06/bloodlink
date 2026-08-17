from django.urls import path
from . import views


urlpatterns = [

    # Blood request API
    path(
        '',
        views.BloodRequestListCreateView.as_view(),
        name='blood-request-list-create'
    ),

    path(
        '<int:pk>/',
        views.BloodRequestDetailView.as_view(),
        name='blood-request-detail'
    ),

    # Donor accepts request
    path(
        '<int:id>/accept/',
        views.AcceptBloodRequestView.as_view(),
        name='accept_blood_request'
    ),

    # Donor declines request
    path(
        '<int:id>/decline/',
        views.DeclineBloodRequestView.as_view(),
        name='decline_blood_request'
    ),

    # Donor completes donation
    path(
        '<int:id>/complete-donation/',
        views.CompleteDonationView.as_view(),
        name='complete_donation'
    ),

    # Hospital confirms blood received
    path(
        '<int:id>/confirm-received/',
        views.ConfirmBloodReceivedView.as_view(),
        name='confirm_blood_received'
    ),

    # Hospital cancels blood request
    path(
        '<int:id>/cancel/',
        views.CancelBloodRequestView.as_view(),
        name='cancel_blood_request'
    ),

    # Hospital deletes blood request
    path(
        '<int:id>/delete/',
        views.DeleteBloodRequestView.as_view(),
        name='delete_blood_request'
    ),

    # Hospital removes a specific accepted donor
    path(
        'remove-donor/<int:id>/',
        views.RemoveDonorView.as_view(),
        name='remove_donor'
    ),
]