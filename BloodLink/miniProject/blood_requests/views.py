from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, redirect

from .models import BloodRequest
from .serializers import BloodRequestSerializer
from notifications.models import Notification
from donors.models import Donation, DonorProfile
from hospitals.models import HospitalProfile
from django.utils import timezone


# ============================================================
# BLOOD REQUEST LIST + CREATE
# ============================================================

class BloodRequestListCreateView(generics.ListCreateAPIView):

    queryset = BloodRequest.objects.all().order_by("-created_at")
    serializer_class = BloodRequestSerializer
    permission_classes = [IsAuthenticated]


# ============================================================
# BLOOD REQUEST DETAIL
# ============================================================

class BloodRequestDetailView(generics.RetrieveUpdateAPIView):

    queryset = BloodRequest.objects.all()
    serializer_class = BloodRequestSerializer
    permission_classes = [IsAuthenticated]


# ============================================================
# DONOR ACCEPTS BLOOD REQUEST
# ============================================================

class AcceptBloodRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, id):
        blood_request = get_object_or_404(
            BloodRequest,
            id=id
        )

        donor = get_object_or_404(
            DonorProfile,
            user=request.user
        )

        # Count donors who have already accepted this request
        accepted_count = Notification.objects.filter(
            blood_request=blood_request,
            response="Accepted"
        ).count()

        # Do not allow more donors than the required units
        if accepted_count >= blood_request.units_required:

            return Response(
                {
                    "message": "All required donor units have already been accepted."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        
        
        
        # Find this donor's notification for this request
        notification = get_object_or_404(
            Notification,
            blood_request=blood_request,
            donor=donor
        )

        # Check if donor already responded
        if notification.response != "Pending":

            return Response(
                {
                    "message": "You have already responded to this request."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark notification as accepted
        notification.response = "Accepted"
        notification.is_read = True
        notification.save()

        # Donor becomes unavailable
        donor.is_available = False
        donor.save()

        # IMPORTANT:
        # We do NOT increase units_fulfilled here.
        #
        # units_fulfilled increases only after
        # the hospital confirms that blood was received.

        return redirect("dashboard")


# ============================================================
# DONOR DECLINES BLOOD REQUEST
# ============================================================

class DeclineBloodRequestView(APIView):

    def post(self, request, id):

        notification = get_object_or_404(
            Notification,
            blood_request_id=id,
            donor__user=request.user
        )

        # Check if donor already responded
        if notification.response != "Pending":

            return Response(
                {
                    "message": "You have already responded to this request."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark notification as declined
        notification.response = "Declined"
        notification.is_read = True
        notification.save()

        return redirect("dashboard")


# ============================================================
# DONOR COMPLETES DONATION
# ============================================================

class CompleteDonationView(APIView):

    def post(self, request, id):

        blood_request = get_object_or_404(
            BloodRequest,
            id=id
        )

        donor = get_object_or_404(
            DonorProfile,
            user=request.user
        )

        # Find donor's notification
        notification = get_object_or_404(
            Notification,
            blood_request=blood_request,
            donor=donor
        )

        # Donor must have accepted
        if notification.response != "Accepted":

            return Response(
                {
                    "message": "You must accept the blood request before completing the donation."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark donor's donation as completed
        notification.response = "Completed"
        notification.is_read = True
        notification.save()

        return redirect("dashboard")

# ============================================================
# HOSPITAL CONFIRMS BLOOD RECEIVED
# ============================================================

class ConfirmBloodReceivedView(APIView):

    def post(self, request, id):

        # Get blood request
        blood_request = get_object_or_404(
            BloodRequest,
            id=id
        )

        # Get logged-in hospital
        hospital = get_object_or_404(
            HospitalProfile,
            user=request.user
        )

        # Make sure this request belongs to this hospital
        if blood_request.hospital != hospital:

            return Response(
                {
                    "message": "You are not authorized to confirm this request."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the specific donor notification
        notification = get_object_or_404(
            Notification,
            id=request.POST.get("notification_id"),
            blood_request=blood_request
        )

        # Donor must have completed the donation
        if notification.response != "Completed":

            return Response(
                {
                    "message": "The donor has not completed the donation yet."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get donor
        donor = notification.donor

        # Prevent duplicate donation records
        donation_exists = Donation.objects.filter(
            donor=donor,
            blood_request=blood_request
        ).exists()

        if donation_exists:

            return Response(
                {
                    "message": "Blood from this donor has already been received."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Make sure units are still remaining
        if blood_request.units_fulfilled >= blood_request.units_required:

            return Response(
                {
                    "message": "All required blood units have already been received."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ====================================================
        # CREATE DONATION RECORD
        # ====================================================

        Donation.objects.create(
            donor=donor,
            blood_request=blood_request,
            hospital_name=str(blood_request.hospital),
            donation_date=timezone.now().date(),
            remarks="Blood received and confirmed by hospital."
        )

        # ====================================================
        # UPDATE DONOR
        # ====================================================

        donor.last_donation_date = timezone.now().date()
        donor.is_available = False
        donor.save()

        # ====================================================
        # UPDATE NOTIFICATION
        # ====================================================

        notification.response = "Received"
        notification.is_read = True
        notification.save()

        # ====================================================
        # UPDATE BLOOD REQUEST
        # ====================================================

        blood_request.units_fulfilled += 1

        if blood_request.units_fulfilled >= blood_request.units_required:

            blood_request.status = "Fulfilled"

        else:

            blood_request.status = "Pending"

        blood_request.save()

        # Return to hospital dashboard
        return redirect("hospital_dashboard")