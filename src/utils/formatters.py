"""Data formatting utilities for NPS API responses."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from src.models.responses import (
        AlertData,
        CampgroundData,
        EventData,
        ParkData,
        VisitorCenterData,
    )
else:
    from src.models.responses import AlertData, ParkData


def format_park_data(park_data: List[ParkData]) -> List[Dict[str, Any]]:
    """
    Format park data into a more readable format for LLMs.

    Args:
        park_data: List of ParkData models

    Returns:
        List of formatted park dictionaries
    """
    return [
        {
            "name": park.full_name,
            "code": park.park_code,
            "description": park.description,
            "states": [s.strip() for s in park.states.split(",")],
            "url": park.url,
            "designation": park.designation,
            "activities": [activity.name for activity in park.activities],
            "weatherInfo": park.weather_info,
            "location": {"latitude": park.latitude, "longitude": park.longitude},
            "entranceFees": [
                {"cost": fee.cost, "description": fee.description, "title": fee.title}
                for fee in park.entrance_fees
            ],
            "operatingHours": [
                {
                    "name": hours.name,
                    "description": hours.description,
                    "standardHours": {
                        "sunday": hours.standard_hours.sunday,
                        "monday": hours.standard_hours.monday,
                        "tuesday": hours.standard_hours.tuesday,
                        "wednesday": hours.standard_hours.wednesday,
                        "thursday": hours.standard_hours.thursday,
                        "friday": hours.standard_hours.friday,
                        "saturday": hours.standard_hours.saturday,
                    },
                }
                for hours in park.operating_hours
            ],
            "contacts": {
                "phoneNumbers": [
                    {
                        "type": phone.type,
                        "number": phone.phone_number,
                        "description": phone.description,
                    }
                    for phone in park.contacts.phone_numbers
                ],
                "emailAddresses": [
                    {"address": email.email_address, "description": email.description}
                    for email in park.contacts.email_addresses
                ],
            },
            "images": [
                {
                    "url": image.url,
                    "title": image.title,
                    "altText": image.alt_text,
                    "caption": image.caption,
                    "credit": image.credit,
                }
                for image in park.images
            ],
        }
        for park in park_data
    ]


def format_park_details(park: ParkData) -> Dict[str, Any]:
    """
    Format detailed park information for a single park.

    Args:
        park: ParkData model

    Returns:
        Formatted park details dictionary
    """
    # Determine the best address to use as the primary address
    physical_address = None
    for addr in park.addresses:
        if addr.type == "Physical":
            physical_address = addr
            break
    if not physical_address and park.addresses:
        physical_address = park.addresses[0]

    # Format operating hours in a more readable way
    formatted_hours = []
    for hours in park.operating_hours:
        standard_hours = hours.standard_hours
        formatted_standard_hours = [
            f"{day.capitalize()}: {getattr(standard_hours, day.lower()) or 'Closed'}"
            for day in [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ]
        ]

        formatted_hours.append(
            {
                "name": hours.name,
                "description": hours.description,
                "standardHours": formatted_standard_hours,
            }
        )

    # Build location with address
    location: Dict[str, Any] = {
        "latitude": park.latitude,
        "longitude": park.longitude,
    }

    if physical_address:
        location["address"] = {
            "line1": physical_address.line1,
            "line2": physical_address.line2,
            "city": physical_address.city,
            "stateCode": physical_address.state_code,
            "postalCode": physical_address.postal_code,
        }

    return {
        "name": park.full_name,
        "code": park.park_code,
        "url": park.url,
        "description": park.description,
        "designation": park.designation,
        "states": [s.strip() for s in park.states.split(",")],
        "weatherInfo": park.weather_info,
        "directionsInfo": park.directions_info,
        "directionsUrl": park.directions_url,
        "location": location,
        "contacts": {
            "phoneNumbers": [
                {
                    "type": phone.type,
                    "number": phone.phone_number,
                    "extension": phone.extension,
                    "description": phone.description,
                }
                for phone in park.contacts.phone_numbers
            ],
            "emailAddresses": [
                {"address": email.email_address, "description": email.description}
                for email in park.contacts.email_addresses
            ],
        },
        "entranceFees": [
            {"title": fee.title, "cost": fee.cost, "description": fee.description}
            for fee in park.entrance_fees
        ],
        "entrancePasses": [
            {"title": pass_.title, "cost": pass_.cost, "description": pass_.description}
            for pass_ in park.entrance_passes
        ],
        "operatingHours": formatted_hours,
        "topics": [topic.name for topic in park.topics],
        "activities": [activity.name for activity in park.activities],
        "images": [
            {
                "url": image.url,
                "title": image.title,
                "altText": image.alt_text,
                "caption": image.caption,
                "credit": image.credit,
            }
            for image in park.images
        ],
    }


def format_alert_data(alert_data: List[AlertData]) -> List[Dict[str, Any]]:
    """
    Format alert data into a more readable format for LLMs.

    Args:
        alert_data: List of AlertData models

    Returns:
        List of formatted alert dictionaries
    """
    formatted_alerts = []

    for alert in alert_data:
        # Get the date part from the lastIndexedDate (which is in ISO format)
        last_updated = "Unknown"
        if alert.last_indexed_date:
            try:
                last_updated = datetime.fromisoformat(
                    alert.last_indexed_date.replace("Z", "+00:00")
                ).strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                last_updated = "Unknown"

        # Categorize the alert type
        alert_type = alert.category
        if alert_type == "Information":
            alert_type = "Information (non-emergency)"
        elif alert_type == "Caution":
            alert_type = "Caution (potential hazard)"
        elif alert_type == "Danger":
            alert_type = "Danger (significant hazard)"
        elif alert_type == "Park Closure":
            alert_type = "Park Closure (area inaccessible)"

        formatted_alerts.append(
            {
                "title": alert.title,
                "description": alert.description,
                "parkCode": alert.park_code,
                "type": alert_type,
                "url": alert.url,
                "lastUpdated": last_updated,
            }
        )

    return formatted_alerts


def format_visitor_center_data(
    visitor_center_data: List["VisitorCenterData"],
) -> List[Dict[str, Any]]:
    """
    Format visitor center data into a more readable format for LLMs.

    Args:
        visitor_center_data: List of VisitorCenterData models

    Returns:
        List of formatted visitor center dictionaries
    """
    formatted_centers = []

    for center in visitor_center_data:
        # Find physical address if available
        physical_address = None
        for addr in center.addresses:
            if addr.type == "Physical":
                physical_address = addr
                break
        if not physical_address and center.addresses:
            physical_address = center.addresses[0]

        # Format operating hours in a more readable way
        formatted_hours = []
        for hours in center.operating_hours:
            standard_hours = hours.standard_hours
            formatted_standard_hours = [
                f"{day.capitalize()}: {getattr(standard_hours, day.lower()) or 'Closed'}"
                for day in [
                    "Sunday",
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ]
            ]

            formatted_hours.append(
                {
                    "name": hours.name,
                    "description": hours.description,
                    "standardHours": formatted_standard_hours,
                }
            )

        # Build location with address
        location: Dict[str, Any] = {
            "latitude": center.latitude,
            "longitude": center.longitude,
        }

        if physical_address:
            location["address"] = {
                "line1": physical_address.line1,
                "line2": physical_address.line2,
                "city": physical_address.city,
                "stateCode": physical_address.state_code,
                "postalCode": physical_address.postal_code,
            }

        formatted_centers.append(
            {
                "name": center.name,
                "parkCode": center.park_code,
                "description": center.description,
                "url": center.url,
                "directionsInfo": center.directions_info,
                "directionsUrl": center.directions_url,
                "location": location,
                "operatingHours": formatted_hours,
                "contacts": {
                    "phoneNumbers": [
                        {
                            "type": phone.type,
                            "number": phone.phone_number,
                            "extension": phone.extension,
                            "description": phone.description,
                        }
                        for phone in center.contacts.phone_numbers
                    ],
                    "emailAddresses": [
                        {
                            "address": email.email_address,
                            "description": email.description,
                        }
                        for email in center.contacts.email_addresses
                    ],
                },
            }
        )

    return formatted_centers


def format_campground_data(
    campground_data: List["CampgroundData"],
) -> List[Dict[str, Any]]:
    """
    Format campground data into a more readable format for LLMs.

    Args:
        campground_data: List of CampgroundData models

    Returns:
        List of formatted campground dictionaries
    """
    formatted_campgrounds = []

    for campground in campground_data:
        # Find physical address if available
        physical_address = None
        for addr in campground.addresses:
            if addr.type == "Physical":
                physical_address = addr
                break
        if not physical_address and campground.addresses:
            physical_address = campground.addresses[0]

        # Format operating hours in a more readable way
        formatted_hours = []
        for hours in campground.operating_hours:
            standard_hours = hours.standard_hours
            formatted_standard_hours = [
                f"{day.capitalize()}: {getattr(standard_hours, day.lower()) or 'Closed'}"
                for day in [
                    "Sunday",
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ]
            ]

            formatted_hours.append(
                {
                    "name": hours.name,
                    "description": hours.description,
                    "standardHours": formatted_standard_hours,
                }
            )

        # Format amenities for better readability
        amenities = []
        if campground.amenities:
            if campground.amenities.trash_recycling_collection:
                amenities.append("Trash/Recycling Collection")
            if campground.amenities.toilets:
                amenities.append(f"Toilets ({', '.join(campground.amenities.toilets)})")
            if campground.amenities.internet_connectivity:
                amenities.append("Internet Connectivity")
            if campground.amenities.showers:
                amenities.append(f"Showers ({', '.join(campground.amenities.showers)})")
            if campground.amenities.cell_phone_reception:
                amenities.append("Cell Phone Reception")
            if campground.amenities.laundry:
                amenities.append("Laundry")
            if campground.amenities.amphitheater:
                amenities.append("Amphitheater")
            if campground.amenities.dump_station:
                amenities.append("Dump Station")
            if campground.amenities.camp_store:
                amenities.append("Camp Store")
            if campground.amenities.staff_or_volunteer_host_onsite:
                amenities.append("Staff/Volunteer Host Onsite")
            if campground.amenities.potable_water:
                amenities.append(
                    f"Potable Water ({', '.join(campground.amenities.potable_water)})"
                )
            if campground.amenities.ice_available_for_sale:
                amenities.append("Ice Available For Sale")
            if campground.amenities.firewood_for_sale:
                amenities.append("Firewood For Sale")
            if campground.amenities.food_storage_lockers:
                amenities.append("Food Storage Lockers")

        # Build location with address
        location: Dict[str, Any] = {
            "latitude": campground.latitude,
            "longitude": campground.longitude,
        }

        if physical_address:
            location["address"] = {
                "line1": physical_address.line1,
                "line2": physical_address.line2,
                "city": physical_address.city,
                "stateCode": physical_address.state_code,
                "postalCode": physical_address.postal_code,
            }

        formatted_campgrounds.append(
            {
                "name": campground.name,
                "parkCode": campground.park_code,
                "description": campground.description,
                "url": campground.url,
                "reservationInfo": campground.reservation_info,
                "reservationUrl": campground.reservation_url,
                "regulations": campground.regulations_overview,
                "regulationsUrl": campground.regulations_url,
                "weatherOverview": campground.weather_overview,
                "location": location,
                "operatingHours": formatted_hours,
                "fees": [
                    {
                        "title": fee.title,
                        "cost": fee.cost,
                        "description": fee.description,
                    }
                    for fee in campground.fees
                ],
                "totalSites": campground.campsites.total_sites,
                "sitesReservable": campground.number_of_sites_reservable,
                "sitesFirstComeFirstServe": campground.number_of_sites_first_come_first_serve,
                "campsiteTypes": {
                    "group": campground.campsites.group,
                    "horse": campground.campsites.horse,
                    "tentOnly": campground.campsites.tent_only,
                    "electricalHookups": campground.campsites.electrical_hookups,
                    "rvOnly": campground.campsites.rv_only,
                    "walkBoatTo": campground.campsites.walk_boat_to,
                    "other": campground.campsites.other,
                },
                "amenities": amenities,
                "accessibility": {
                    "wheelchairAccess": campground.accessibility.wheelchair_access,
                    "rvAllowed": campground.accessibility.rv_allowed,
                    "rvMaxLength": campground.accessibility.rv_max_length,
                    "trailerAllowed": campground.accessibility.trailer_allowed,
                    "trailerMaxLength": campground.accessibility.trailer_max_length,
                    "accessRoads": campground.accessibility.access_roads,
                    "adaInfo": campground.accessibility.ada_info,
                },
                "contacts": {
                    "phoneNumbers": [
                        {
                            "type": phone.type,
                            "number": phone.phone_number,
                            "extension": phone.extension,
                            "description": phone.description,
                        }
                        for phone in campground.contacts.phone_numbers
                    ],
                    "emailAddresses": [
                        {
                            "address": email.email_address,
                            "description": email.description,
                        }
                        for email in campground.contacts.email_addresses
                    ],
                },
            }
        )

    return formatted_campgrounds


def format_event_data(event_data: List["EventData"]) -> List[Dict[str, Any]]:
    """
    Format event data into a more readable format for LLMs.

    Args:
        event_data: List of EventData models

    Returns:
        List of formatted event dictionaries
    """
    formatted_events = []

    for event in event_data:
        # Format dates and times
        formatted_dates = ", ".join(event.dates) if event.dates else ""

        # Format times
        formatted_times = []
        for time in event.times:
            time_string = ""
            if time.time_start:
                time_string += "Sunrise" if time.sunrise_time_start else time.time_start
            if time.time_end:
                time_string += " to "
                time_string += "Sunset" if time.sunset_time_end else time.time_end
            formatted_times.append(time_string if time_string else "All day")

        formatted_times_str = (
            ", ".join(formatted_times) if formatted_times else "All day"
        )

        formatted_events.append(
            {
                "title": event.title,
                "parkCode": event.park_code,
                "parkName": event.park_full_name,
                "description": event.description,
                "category": event.category,
                "subcategory": event.subcategory,
                "tags": event.tags,
                "location": event.location,
                "coordinates": {
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                },
                "dateTime": {
                    "dates": formatted_dates,
                    "times": formatted_times_str,
                    "dateStart": event.date_start,
                    "dateEnd": event.date_end,
                    "isAllDay": event.is_all_day,
                    "isRecurring": event.is_recurring,
                    "recurrenceDateStart": event.recurrence_date_start,
                    "recurrenceDateEnd": event.recurrence_date_end,
                },
                "feeInfo": event.fee_info,
                "contactInfo": {
                    "email": event.contact_email_address,
                    "phone": event.contact_telephone_number,
                },
                "infoUrl": event.info_url or event.url,
                "lastUpdated": event.last_updated,
            }
        )

    return formatted_events
