"""Pydantic models for NPS API responses."""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Generic type for NPSResponse
T = TypeVar("T")


class Activity(BaseModel):
    """Activity model."""

    id: str
    name: str


class Topic(BaseModel):
    """Topic model."""

    id: str
    name: str


class PhoneNumber(BaseModel):
    """Phone number model."""

    model_config = ConfigDict(populate_by_name=True)

    phone_number: str = Field(alias="phoneNumber")
    description: str
    extension: str
    type: str


class EmailAddress(BaseModel):
    """Email address model."""

    model_config = ConfigDict(populate_by_name=True)

    description: str
    email_address: str = Field(alias="emailAddress")


class Contacts(BaseModel):
    """Contacts model."""

    model_config = ConfigDict(populate_by_name=True)

    phone_numbers: List[PhoneNumber] = Field(default_factory=list, alias="phoneNumbers")
    email_addresses: List[EmailAddress] = Field(
        default_factory=list, alias="emailAddresses"
    )


class Fee(BaseModel):
    """Fee model."""

    cost: str
    description: str
    title: str


class StandardHours(BaseModel):
    """Standard operating hours model."""

    sunday: str
    monday: str
    tuesday: str
    wednesday: str
    thursday: str
    friday: str
    saturday: str


class OperatingHours(BaseModel):
    """Operating hours model."""

    model_config = ConfigDict(populate_by_name=True)

    exceptions: List[Any] = Field(default_factory=list)
    description: str
    standard_hours: StandardHours = Field(alias="standardHours")
    name: str


class Address(BaseModel):
    """Address model."""

    model_config = ConfigDict(populate_by_name=True)

    postal_code: str = Field(alias="postalCode")
    city: str
    state_code: str = Field(alias="stateCode")
    line1: str
    line2: str
    line3: str
    type: str


class Image(BaseModel):
    """Image model."""

    model_config = ConfigDict(populate_by_name=True)

    credit: str
    title: str
    alt_text: str = Field(alias="altText")
    caption: str
    url: str


class ParkData(BaseModel):
    """Park data model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    full_name: str = Field(alias="fullName")
    park_code: str = Field(alias="parkCode")
    description: str
    latitude: str
    longitude: str
    lat_long: str = Field(alias="latLong")
    activities: List[Activity] = Field(default_factory=list)
    topics: List[Topic] = Field(default_factory=list)
    states: str
    contacts: Contacts
    entrance_fees: List[Fee] = Field(default_factory=list, alias="entranceFees")
    entrance_passes: List[Fee] = Field(default_factory=list, alias="entrancePasses")
    fees: List[Any] = Field(default_factory=list)
    directions_info: str = Field(alias="directionsInfo")
    directions_url: str = Field(alias="directionsUrl")
    operating_hours: List[OperatingHours] = Field(
        default_factory=list, alias="operatingHours"
    )
    addresses: List[Address] = Field(default_factory=list)
    images: List[Image] = Field(default_factory=list)
    weather_info: str = Field(alias="weatherInfo")
    name: str
    designation: str


class AlertData(BaseModel):
    """Alert data model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    title: str
    park_code: str = Field(alias="parkCode")
    description: str
    category: str
    last_indexed_date: str = Field(alias="lastIndexedDate")


class VisitorCenterData(BaseModel):
    """Visitor center data model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    name: str
    park_code: str = Field(alias="parkCode")
    description: str
    latitude: str
    longitude: str
    lat_long: str = Field(alias="latLong")
    directions_info: str = Field(alias="directionsInfo")
    directions_url: str = Field(alias="directionsUrl")
    addresses: List[Address] = Field(default_factory=list)
    operating_hours: List[OperatingHours] = Field(
        default_factory=list, alias="operatingHours"
    )
    contacts: Contacts


class CampgroundAmenities(BaseModel):
    """Campground amenities model."""

    model_config = ConfigDict(populate_by_name=True)

    trash_recycling_collection: bool = Field(alias="trashRecyclingCollection")
    toilets: List[str] = Field(default_factory=list)
    internet_connectivity: bool = Field(alias="internetConnectivity")
    showers: List[str] = Field(default_factory=list)
    cell_phone_reception: bool = Field(alias="cellPhoneReception")
    laundry: bool
    amphitheater: bool
    dump_station: bool = Field(alias="dumpStation")
    camp_store: bool = Field(alias="campStore")
    staff_or_volunteer_host_onsite: bool = Field(alias="staffOrVolunteerHostOnsite")
    potable_water: List[str] = Field(default_factory=list, alias="potableWater")
    ice_available_for_sale: bool = Field(alias="iceAvailableForSale")
    firewood_for_sale: bool = Field(alias="firewoodForSale")
    food_storage_lockers: bool = Field(alias="foodStorageLockers")


class Campsites(BaseModel):
    """Campsites model."""

    model_config = ConfigDict(populate_by_name=True)

    total_sites: str = Field(alias="totalSites")
    group: str
    horse: str
    tent_only: str = Field(alias="tentOnly")
    electrical_hookups: str = Field(alias="electricalHookups")
    rv_only: str = Field(alias="rvOnly")
    walk_boat_to: str = Field(alias="walkBoatTo")
    other: str


class CampgroundAccessibility(BaseModel):
    """Campground accessibility model."""

    model_config = ConfigDict(populate_by_name=True)

    wheelchair_access: str = Field(alias="wheelchairAccess")
    internet_info: str = Field(alias="internetInfo")
    cell_phone_info: str = Field(alias="cellPhoneInfo")
    fire_stove_policy: str = Field(alias="fireStovePolicy")
    rv_allowed: bool = Field(alias="rvAllowed")
    rv_info: str = Field(alias="rvInfo")
    rv_max_length: str = Field(alias="rvMaxLength")
    additional_info: str = Field(alias="additionalInfo")
    trailer_max_length: str = Field(alias="trailerMaxLength")
    ada_info: str = Field(alias="adaInfo")
    trailer_allowed: bool = Field(alias="trailerAllowed")
    access_roads: List[str] = Field(default_factory=list, alias="accessRoads")
    classifications: List[str] = Field(default_factory=list)


class CampgroundData(BaseModel):
    """Campground data model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    name: str
    park_code: str = Field(alias="parkCode")
    description: str
    latitude: str
    longitude: str
    lat_long: str = Field(alias="latLong")
    audio_description: str = Field(alias="audioDescription")
    is_passport_stamp_location: bool = Field(alias="isPassportStampLocation")
    passport_stamp_location_description: str = Field(
        alias="passportStampLocationDescription"
    )
    passport_stamp_images: List[Any] = Field(
        default_factory=list, alias="passportStampImages"
    )
    geometry_poi_id: str = Field(alias="geometryPoiId")
    reservation_info: str = Field(alias="reservationInfo")
    reservation_url: str = Field(alias="reservationUrl")
    regulations_url: str = Field(alias="regulationsurl")
    regulations_overview: str = Field(alias="regulationsOverview")
    amenities: CampgroundAmenities
    contacts: Contacts
    fees: List[Fee] = Field(default_factory=list)
    directions_overview: str = Field(alias="directionsOverview")
    directions_url: str = Field(alias="directionsUrl")
    operating_hours: List[OperatingHours] = Field(
        default_factory=list, alias="operatingHours"
    )
    addresses: List[Address] = Field(default_factory=list)
    weather_overview: str = Field(alias="weatherOverview")
    number_of_sites_reservable: str = Field(alias="numberOfSitesReservable")
    number_of_sites_first_come_first_serve: str = Field(
        alias="numberOfSitesFirstComeFirstServe"
    )
    campsites: Campsites
    accessibility: CampgroundAccessibility


class EventTime(BaseModel):
    """Event time model."""

    model_config = ConfigDict(populate_by_name=True)

    time_start: str = Field(alias="timeStart")
    time_end: str = Field(alias="timeEnd")
    sunrise_time_start: bool = Field(alias="sunriseTimeStart")
    sunset_time_end: bool = Field(alias="sunsetTimeEnd")


class EventData(BaseModel):
    """Event data model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    title: str
    park_full_name: str = Field(default="", alias="parkFullName")
    description: str
    latitude: str
    longitude: str
    category: str
    subcategory: str = Field(default="")
    location: str
    tags: List[str] = Field(default_factory=list)
    recurrence_date_start: str = Field(default="", alias="recurrenceDateStart")
    recurrence_date_end: str = Field(default="", alias="recurrenceDateEnd")
    times: List[EventTime] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    date_start: str = Field(alias="dateStart")
    date_end: str = Field(alias="dateEnd")
    regres_url: str = Field(default="", alias="regresurl")
    contact_email_address: str = Field(default="", alias="contactEmailAddress")
    contact_telephone_number: str = Field(default="", alias="contactTelephoneNumber")
    fee_info: str = Field(default="", alias="feeInfo")
    is_recurring: bool = Field(alias="isRecurring")
    is_all_day: bool = Field(alias="isAllDay")
    site_code: str = Field(default="", alias="siteCode")
    park_code: str = Field(alias="parkCode")
    organization_name: str = Field(default="", alias="organizationName")
    types: List[str] = Field(default_factory=list)
    create_date: str = Field(default="", alias="createDate")
    last_updated: str = Field(default="", alias="lastUpdated")
    info_url: str = Field(default="", alias="infoURL")
    portal_name: str = Field(default="", alias="portalName")


class NPSResponse(BaseModel, Generic[T]):
    """Generic NPS API response model."""

    total: str
    limit: str
    start: str
    data: List[T]
