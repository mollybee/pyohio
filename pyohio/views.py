from datetime import datetime
import json

from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.http import HttpResponse

from symposion.schedule.models import Slot
from symposion.sponsorship.models import Sponsor


def json_serializer(obj):
    if isinstance(obj, datetime.time):
        return obj.strftime("%H:%M")
    raise TypeError


def duration(start, end):
    start_dt = datetime.strptime(start.isoformat(), "%H:%M:%S")
    end_dt = datetime.strptime(end.isoformat(), "%H:%M:%S")
    delta = end_dt - start_dt
    return delta.seconds // 60


def schedule_json(request):
    slots = Slot.objects.all().order_by("start")
    protocol = request.META.get('HTTP_X_FORWARDED_PROTO', 'http')
    data = []
    for slot in slots:
        slot_data = {
            "room": ", ".join(room["name"] for room in slot.rooms.values()),
            "rooms": [room["name"] for room in slot.rooms.values()],
            "start": datetime.combine(slot.day.date, slot.start).isoformat(),
            "end": datetime.combine(slot.day.date, slot.end).isoformat(),
            "duration": duration(slot.start, slot.end),
            "kind": slot.kind.label,
            "conf_key": slot.pk,
            "license": "CC BY",  # TODO: this should be configurable or a part of the model
            "tags": "",
        }
        if hasattr(slot.content, "proposal"):
            slot_data.update({
                "name": slot.content.title,
                "authors": [s.name for s in slot.content.speakers()],
                "released": hasattr(slot.content.proposal, "recording_release") and slot.content.proposal.recording_release,
                "contact": [s.email for s in slot.content.speakers()] if request.user.is_staff else ["redacted"],
                "abstract": slot.content.abstract.raw,
                "description": slot.content.description.raw,
                "conf_url": "%s://%s%s" % (
                    protocol,
                    Site.objects.get_current().domain,
                    reverse("schedule_presentation_detail", args=[slot.content.pk])
                ),
            })
        else:
            slot_data.update({
                "name": slot.content_override.raw if slot.content_override else "Slot",
                "authors": None,
                "released": True,
                "contact": None,
                "abstract": "",
                "description": "",
                "conf_url": None,
            })
        data.append(slot_data)

    return HttpResponse(
        # TODO: json.dumps({'schedule': data}, default=json_serializer),
        # Carl requested the above change to be reverted. He doesn't have the bandwidth
        # to handle it the day before the conference; however, it still needs to be fixed.
        json.dumps(data, default=json_serializer),
        content_type="application/json"
    )


def sponsors_json(request):
    objects = Sponsor.objects.all().filter(active=True).order_by("level")
    sponsors = []
    for sponsor in objects:

        sponsor_benefit = sponsor.sponsor_logo
        if sponsor_benefit and sponsor_benefit.upload:
            logo_url = "{protocol}://{domain}{sponsor_url}".format(
                protocol=request.META.get('HTTP_X_FORWARDED_PROTO', 'http'),
                domain=Site.objects.get_current().domain,
                sponsor_url=sponsor_benefit.upload.url,
            )
        else:
            logo_url = ""

        sponsors.append({
            "name": sponsor.name,
            "external_url": sponsor.external_url,
            "level": sponsor.level.name,
            "conference": sponsor.level.conference.title,
            "order": sponsor.level.order,
            "logo_url": logo_url,
            "listing_text": sponsor.listing_text,
        })

    return HttpResponse(
        json.dumps({"sponsors": sponsors}, default=json_serializer),
        content_type="application/json"
    )
