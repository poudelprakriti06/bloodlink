from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_blood_request_email(donor, blood_request):

    if not donor.user.email:
        print(f"⚠️ NO EMAIL for donor: {donor.user.username}")
        return

    subject = f"[BloodLink] {blood_request.urgency} Blood Request — {blood_request.blood_group}"

    context = {
        "donor": donor,
        "blood_request": blood_request,
        "dashboard_url": "http://127.0.0.1:8000/dashboard/",
    }

    text_body = render_to_string("emails/blood_request_notification.txt", context)

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
      <div style="background:#c0392b;padding:20px 24px;">
        <h2 style="color:#fff;margin:0;">🩸 BloodLink — Blood Request Alert</h2>
      </div>
      <div style="padding:24px;">
        <p>Dear <strong>{donor.user.get_full_name() or donor.user.username}</strong>,</p>
        <p>A blood request matching your profile has been posted. Please respond as soon as possible.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
          <tr style="background:#fff5f5;">
            <td style="padding:8px 12px;font-weight:bold;border:1px solid #eee;">Blood Group</td>
            <td style="padding:8px 12px;border:1px solid #eee;"><strong style="color:#c0392b;">{blood_request.blood_group}</strong></td>
          </tr>
          <tr>
            <td style="padding:8px 12px;font-weight:bold;border:1px solid #eee;">Hospital</td>
            <td style="padding:8px 12px;border:1px solid #eee;">{blood_request.hospital.hospital_name}</td>
          </tr>
          <tr style="background:#fff5f5;">
            <td style="padding:8px 12px;font-weight:bold;border:1px solid #eee;">Urgency</td>
            <td style="padding:8px 12px;border:1px solid #eee;">{blood_request.urgency}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;font-weight:bold;border:1px solid #eee;">District</td>
            <td style="padding:8px 12px;border:1px solid #eee;">{blood_request.district}</td>
          </tr>
          <tr style="background:#fff5f5;">
            <td style="padding:8px 12px;font-weight:bold;border:1px solid #eee;">Units Required</td>
            <td style="padding:8px 12px;border:1px solid #eee;">{blood_request.units_required}</td>
          </tr>
          <tr>
            <td style="padding:8px 12px;font-weight:bold;border:1px solid #eee;">Required By</td>
            <td style="padding:8px 12px;border:1px solid #eee;">{blood_request.required_date}</td>
          </tr>
        </table>
        <div style="text-align:center;margin-top:24px;">
          <a href="http://127.0.0.1:8000/dashboard/" style="background:#c0392b;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px;">
            Open Dashboard &amp; Respond
          </a>
        </div>
        <p style="margin-top:24px;color:#777;font-size:13px;">
          You received this because your blood group matches and you are marked as available.
        </p>
      </div>
      <div style="background:#f5f5f5;padding:12px 24px;text-align:center;font-size:12px;color:#999;">
        BloodLink — Connecting Donors &amp; Hospitals in Nepal
      </div>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[donor.user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        print(f"✅ EMAIL SENT TO: {donor.user.email}")
    except Exception as e:
        print(f"❌ EMAIL FAILED FOR {donor.user.email}: {e}")
