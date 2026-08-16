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
]