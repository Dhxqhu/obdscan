#!/usr/bin/env python3
"""
Additional / common-brand manufacturer packs.

Many brands share corporate electronics platforms; we still expose
first-class pack IDs (chevy, dodge, mazda, …) so selection is obvious.
"""

from __future__ import annotations

from .base import EcuModule, ManufacturerPack, STANDARD_DIDS


def _pack(
    id_: str,
    name: str,
    aliases: tuple[str, ...],
    modules: tuple[EcuModule, ...],
    gateways: tuple[int, ...] = (),
    description: str = "",
    sources: tuple[str, ...] = (),
    maturity: str = "scaffold",
) -> ManufacturerPack:
    return ManufacturerPack(
        id=id_,
        name=name,
        aliases=aliases,
        description=description
        or f"{name} DoIP/UDS address scaffold. Probe + discover; DID maps are sparse.",
        transports=("doip", "isotp"),
        gateway_addresses=gateways or tuple(m.address for m in modules[:2]),
        modules=modules,
        dids=STANDARD_DIDS,
        sources=sources or ("ISO 14229 / community address lists",),
        maturity=maturity,
    )


def _derive(
    base: ManufacturerPack,
    id_: str,
    name: str,
    aliases: tuple[str, ...] = (),
    description: str | None = None,
) -> ManufacturerPack:
    """Same modules/DIDs as base, new selectable brand id."""
    return ManufacturerPack(
        id=id_,
        name=name,
        aliases=aliases,
        description=description
        or f"{name} — uses {base.name} platform module map ({base.id}).",
        transports=base.transports,
        default_doip_port=base.default_doip_port,
        default_hsfz_port=base.default_hsfz_port,
        tester_address=base.tester_address,
        gateway_addresses=base.gateway_addresses,
        modules=base.modules,
        dids=base.dids,
        ip_hints=base.ip_hints,
        sources=base.sources + (f"derived from pack '{base.id}'",),
        maturity=base.maturity,
    )


# --- shared module catalogs -------------------------------------------------

_US_OBD = (
    EcuModule(0x07E0, "OBD_REQ", "Legislated OBD request (11-bit)"),
    EcuModule(0x07E8, "OBD_RSP_ECM", "OBD response ECM"),
    EcuModule(0x07E1, "OBD_REQ_TCM", "OBD request TCM"),
    EcuModule(0x07E9, "OBD_RSP_TCM", "OBD response TCM"),
)

_FORD_MODULES = (
    EcuModule(0x0700, "PCM", "Powertrain control module"),
    EcuModule(0x0701, "TCM", "Transmission control"),
    EcuModule(0x0702, "ABS", "ABS / ESC"),
    EcuModule(0x0703, "RCM", "Restraints control module"),
    EcuModule(0x0704, "BCM", "Body control module"),
    EcuModule(0x0705, "IPC", "Instrument panel cluster"),
    EcuModule(0x0706, "SCCM", "Steering column control"),
    EcuModule(0x0707, "APIM", "Sync / APIM infotainment"),
    EcuModule(0x0708, "GWM", "Gateway module"),
    EcuModule(0x0709, "BCMC", "Battery charge / BECM"),
    EcuModule(0x070A, "PSCM", "Power steering"),
    EcuModule(0x070B, "HVAC", "Climate control"),
    EcuModule(0x070C, "DDM", "Driver door module"),
    EcuModule(0x070D, "PDM", "Passenger door module"),
    EcuModule(0x070E, "TRM", "Trailer module"),
    EcuModule(0x070F, "SODL", "Side obstacle detection"),
    EcuModule(0x0710, "IPMA", "Image processing / camera"),
    EcuModule(0x0711, "ACM", "Audio control module"),
    EcuModule(0x0712, "TCU", "Telematics control"),
    EcuModule(0x0713, "SOBDMC", "Secondary OBD / motor control (hybrid)"),
    *_US_OBD,
)

_GM_MODULES = (
    EcuModule(0x0700, "ECM", "Engine control module"),
    EcuModule(0x0701, "TCM", "Transmission"),
    EcuModule(0x0702, "EBCM", "Electronic brake / ABS"),
    EcuModule(0x0703, "SDM", "Sensing diagnostic / airbags"),
    EcuModule(0x0704, "BCM", "Body control"),
    EcuModule(0x0705, "IPC", "Instrument cluster"),
    EcuModule(0x0706, "Radio", "Infotainment / radio"),
    EcuModule(0x0707, "CGM", "Central gateway / CGM"),
    EcuModule(0x0708, "HVAC", "HVAC"),
    EcuModule(0x0709, "EPS", "Electric power steering"),
    EcuModule(0x070A, "EBCM2", "Brake booster / ESC variant"),
    EcuModule(0x070B, "PDM", "Passenger door"),
    EcuModule(0x070C, "DDM", "Driver door"),
    EcuModule(0x070D, "AOS", "Airbag occupant sensor"),
    EcuModule(0x070E, "FSCM", "Fuel system control"),
    EcuModule(0x070F, "HPCM", "Hybrid powertrain"),
    EcuModule(0x0710, "BECM", "Battery energy control"),
    EcuModule(0x0711, "TCU", "Telematics / OnStar"),
    EcuModule(0x0712, "PAC", "Park assist"),
    EcuModule(0x0713, "FCM", "Front camera"),
    *_US_OBD,
)

_FCA_MODULES = (
    EcuModule(0x0700, "ECM", "Engine / PCM"),
    EcuModule(0x0701, "TCM", "Transmission"),
    EcuModule(0x0702, "ABS", "ABS / ESP"),
    EcuModule(0x0703, "ORC", "Occupant restraint"),
    EcuModule(0x0704, "BCM", "Body control"),
    EcuModule(0x0705, "IPC", "Cluster"),
    EcuModule(0x0706, "RADIO", "Radio / Uconnect"),
    EcuModule(0x0707, "GW", "Gateway"),
    EcuModule(0x0708, "HVAC", "HVAC"),
    EcuModule(0x0709, "TPMS", "Tire pressure"),
    EcuModule(0x070A, "DTCM", "Drivetrain control"),
    EcuModule(0x070B, "EPS", "Electric steering"),
    EcuModule(0x070C, "RFH", "RF hub / keyless"),
    EcuModule(0x070D, "SCM", "Steering column"),
    EcuModule(0x070E, "ITBM", "Integrated trailer brake"),
    EcuModule(0x070F, "HSM", "Heated seat"),
    EcuModule(0x0710, "PTCM", "Power top / cabin"),
    EcuModule(0x0711, "BPCM", "Battery pack (hybrid/PHEV)"),
    EcuModule(0x0712, "ACC", "Adaptive cruise"),
    *_US_OBD,
)

_HONDA_MODULES = (
    EcuModule(0x0700, "PCM", "Powertrain"),
    EcuModule(0x0701, "TCM", "Transmission"),
    EcuModule(0x0702, "ABS", "ABS / VSA"),
    EcuModule(0x0703, "SRS", "SRS airbag"),
    EcuModule(0x0704, "BODY", "Body electrical"),
    EcuModule(0x0705, "GATEWAY", "Gateway"),
    EcuModule(0x0706, "GAUGE", "Gauge control"),
    EcuModule(0x0707, "HVAC", "Climate"),
    EcuModule(0x0708, "EPS", "EPS"),
    EcuModule(0x0709, "BMS", "Battery / IMA / hybrid"),
    EcuModule(0x070A, "MICU", "Multiplex integrated control"),
    EcuModule(0x070B, "KEYLESS", "Keyless access"),
    EcuModule(0x070C, "TPMS", "TPMS"),
    EcuModule(0x070D, "AUDIO", "Audio unit"),
    EcuModule(0x070E, "PARKING", "Parking sensors"),
    EcuModule(0x070F, "FWD_CAM", "Forward camera"),
    *_US_OBD,
)

_NISSAN_MODULES = (
    EcuModule(0x0700, "ECM", "Engine"),
    EcuModule(0x0701, "TCM", "CVT / transmission"),
    EcuModule(0x0702, "ABS", "ABS / VDC"),
    EcuModule(0x0703, "AIRBAG", "Airbag"),
    EcuModule(0x0704, "BCM", "Body control"),
    EcuModule(0x0705, "IPDM", "Intelligent power distribution"),
    EcuModule(0x0706, "METER", "Combination meter"),
    EcuModule(0x0707, "AV", "AV / head unit"),
    EcuModule(0x0708, "GATEWAY", "Gateway"),
    EcuModule(0x0709, "HV_BAT", "EV/hybrid battery"),
    EcuModule(0x070A, "EPS", "EPS"),
    EcuModule(0x070B, "HCM", "Hybrid control"),
    EcuModule(0x070C, "SONAR", "Sonar / parking"),
    EcuModule(0x070D, "LANE", "Lane camera"),
    EcuModule(0x070E, "ADAS", "ADAS controller"),
    EcuModule(0x070F, "TCU", "Telematics"),
    *_US_OBD,
)

_MAZDA_MODULES = (
    EcuModule(0x0700, "PCM", "Powertrain"),
    EcuModule(0x0701, "TCM", "Transmission"),
    EcuModule(0x0702, "ABS", "ABS / DSC"),
    EcuModule(0x0703, "RCM", "Restraints"),
    EcuModule(0x0704, "BCM", "Body control"),
    EcuModule(0x0705, "IC", "Instrument cluster"),
    EcuModule(0x0706, "START", "Smart start / keyless"),
    EcuModule(0x0707, "GATEWAY", "Gateway"),
    EcuModule(0x0708, "CMU", "Connectivity / CMU"),
    EcuModule(0x0709, "EPS", "EPS"),
    EcuModule(0x070A, "HVAC", "Climate"),
    EcuModule(0x070B, "LAS", "Lane-keep / camera"),
    EcuModule(0x070C, "MRCC", "Radar cruise"),
    EcuModule(0x070D, "BSW", "Blind spot"),
    *_US_OBD,
)

_TOYOTA_MODULES = (
    EcuModule(0x0700, "ENGINE", "Engine / hybrid control"),
    EcuModule(0x0701, "TRANS", "Transmission"),
    EcuModule(0x0702, "ABS", "ABS / VSC"),
    EcuModule(0x0703, "SRS", "Airbag"),
    EcuModule(0x0704, "BODY", "Body ECU"),
    EcuModule(0x0705, "GATEWAY", "Gateway"),
    EcuModule(0x0706, "HV_BATTERY", "HV battery"),
    EcuModule(0x0707, "CLUSTER", "Combination meter"),
    EcuModule(0x0708, "AC", "Air conditioning"),
    EcuModule(0x0709, "EPS", "EPS"),
    EcuModule(0x070A, "PM", "Power management"),
    EcuModule(0x070B, "SMART", "Smart key"),
    EcuModule(0x070C, "TPMS", "TPMS"),
    EcuModule(0x070D, "RADAR", "Millimeter-wave radar"),
    EcuModule(0x070E, "CAMERA", "Forward recognition camera"),
    EcuModule(0x070F, "BLIND", "Blind spot monitor"),
    *_US_OBD,
)

_HYUNDAI_MODULES = (
    EcuModule(0x0700, "ENGINE", "Engine"),
    EcuModule(0x0701, "TCU", "Transmission"),
    EcuModule(0x0702, "ABS", "ABS / ESC"),
    EcuModule(0x0703, "AIRBAG", "Airbag"),
    EcuModule(0x0704, "BCM", "BCM"),
    EcuModule(0x0705, "CLUSTER", "Cluster"),
    EcuModule(0x0706, "SMART_KEY", "Smart key"),
    EcuModule(0x0707, "GATEWAY", "Gateway"),
    EcuModule(0x0708, "AVN", "AVN / head unit"),
    EcuModule(0x0709, "BMS", "Battery management"),
    EcuModule(0x070A, "EPS", "MDPS / EPS"),
    EcuModule(0x070B, "ACU", "Aircon"),
    EcuModule(0x070C, "LDWS", "Lane departure"),
    EcuModule(0x070D, "FCA", "Forward collision"),
    EcuModule(0x070E, "BCW", "Blind-spot collision"),
    *_US_OBD,
)

_SUBARU_MODULES = (
    EcuModule(0x0700, "ECM", "Engine"),
    EcuModule(0x0701, "TCM", "Transmission"),
    EcuModule(0x0702, "VDC", "VDC / ABS"),
    EcuModule(0x0703, "AIRBAG", "Airbag"),
    EcuModule(0x0704, "BIU", "Body integrated unit"),
    EcuModule(0x0705, "COMBI", "Combination meter"),
    EcuModule(0x0706, "GATEWAY", "Gateway"),
    EcuModule(0x0707, "EYESIGHT", "EyeSight stereo camera"),
    EcuModule(0x0708, "EPS", "EPS"),
    EcuModule(0x0709, "HVAC", "HVAC"),
    EcuModule(0x070A, "TPMS", "TPMS"),
    EcuModule(0x070B, "KEYLESS", "Keyless access"),
    *_US_OBD,
)

_MITSU_MODULES = (
    EcuModule(0x0700, "ENGINE", "Engine"),
    EcuModule(0x0701, "AT", "Automatic transmission"),
    EcuModule(0x0702, "ABS", "ABS / ASC"),
    EcuModule(0x0703, "SRS", "SRS"),
    EcuModule(0x0704, "ETACS", "ETACS body"),
    EcuModule(0x0705, "METER", "Combination meter"),
    EcuModule(0x0706, "GATEWAY", "Gateway"),
    EcuModule(0x0707, "AC", "A/C"),
    EcuModule(0x0708, "EPS", "EPS"),
    EcuModule(0x0709, "AWC", "All-wheel control"),
    *_US_OBD,
)

_RENAULT_MODULES = (
    EcuModule(0x0700, "ENGINE", "Engine / Injection"),
    EcuModule(0x0701, "GEARBOX", "Gearbox"),
    EcuModule(0x0702, "ABS", "ABS / ESP"),
    EcuModule(0x0703, "AIRBAG", "Airbag"),
    EcuModule(0x0704, "UCH", "UCH body computer"),
    EcuModule(0x0705, "CLUSTER", "Instrument panel"),
    EcuModule(0x0706, "GATEWAY", "Gateway"),
    EcuModule(0x0707, "RADIO", "Radio / MediaNav"),
    EcuModule(0x0708, "HVAC", "Climate"),
    EcuModule(0x0709, "EPS", "Electric steering"),
    EcuModule(0x070A, "BMS", "EV battery"),
    *_US_OBD,
)


# --- primary packs ----------------------------------------------------------

TOYOTA = _pack(
    "toyota",
    "Toyota / Lexus",
    ("lexus", "scion"),
    _TOYOTA_MODULES,
    gateways=(0x0705,),
    description="Toyota/Lexus — CAN/ISO-TP common; DoIP on newer global platforms.",
)

FORD = _pack(
    "ford",
    "Ford",
    ("ford_motor", "f150", "mustang"),
    _FORD_MODULES,
    gateways=(0x0708,),
    description="Ford UDS/DoIP scaffold (PCM, GWM, Sync/APIM, ABS, RCM, …).",
)

LINCOLN = _derive(FORD, "lincoln", "Lincoln", ("lincoln_motor",))

GM = _pack(
    "gm",
    "General Motors",
    ("general_motors", "gm_global"),
    _GM_MODULES,
    gateways=(0x0707,),
    description="GM Global A/B architecture scaffold (Chevy/GMC/Cadillac/Buick share this map).",
)

CHEVY = _derive(
    GM,
    "chevy",
    "Chevrolet",
    ("chevrolet", "chevy_truck", "silverado", "camaro", "corvette"),
)
GMC = _derive(GM, "gmc", "GMC", ("sierra", "yukon"))
CADILLAC = _derive(GM, "cadillac", "Cadillac", ("cts", "escalade"))
BUICK = _derive(GM, "buick", "Buick", ())
HOLDEN = _derive(GM, "holden", "Holden", ())

STELLANTIS = _pack(
    "stellantis",
    "Stellantis (group)",
    ("fca", "psa"),
    _FCA_MODULES,
    gateways=(0x0707,),
    description="Stellantis/FCA/PSA shared scaffold — prefer brand ids: dodge, jeep, ram, …",
)

DODGE = _derive(
    STELLANTIS,
    "dodge",
    "Dodge",
    ("challenger", "charger", "durango", "ram_dodge"),
)
JEEP = _derive(STELLANTIS, "jeep", "Jeep", ("wrangler", "grand_cherokee", "gladiator"))
RAM = _derive(STELLANTIS, "ram", "Ram", ("ramtrucks", "ram_truck"))
CHRYSLER = _derive(STELLANTIS, "chrysler", "Chrysler", ("pacifica", "300c"))
FIAT = _derive(STELLANTIS, "fiat", "Fiat", ("abarth",))
ALFA = _derive(STELLANTIS, "alfa", "Alfa Romeo", ("alfa_romeo", "giulia", "stelvio"))
PEUGEOT = _derive(STELLANTIS, "peugeot", "Peugeot", ("psa_peugeot",))
CITROEN = _derive(STELLANTIS, "citroen", "Citroën", ("citroën", "ds_automobiles"))

HONDA = _pack(
    "honda",
    "Honda",
    ("honda_motor", "civic", "accord", "crv"),
    _HONDA_MODULES,
    gateways=(0x0705,),
)
ACURA = _derive(HONDA, "acura", "Acura", ("tsx", "mdx", "rdx"))

NISSAN = _pack(
    "nissan",
    "Nissan",
    ("nissan_motor", "altima", "rogue", "gtr"),
    _NISSAN_MODULES,
    gateways=(0x0708,),
)
INFINITI = _derive(NISSAN, "infiniti", "Infiniti", ("infinity",))  # common misspelling

MAZDA = _pack(
    "mazda",
    "Mazda",
    ("mazda3", "mazda6", "cx5", "mx5", "miata"),
    _MAZDA_MODULES,
    gateways=(0x0707,),
    description="Mazda (Skyactiv) UDS scaffold — distinct from Ford despite past platform sharing.",
)

HYUNDAI = _pack(
    "hyundai",
    "Hyundai",
    ("hyundai_motor", "tucson", "elantra", "ioniq"),
    _HYUNDAI_MODULES,
    gateways=(0x0707,),
)
KIA = _derive(HYUNDAI, "kia", "Kia", ("sportage", "telluride", "ev6"))
GENESIS = _derive(HYUNDAI, "genesis", "Genesis", ("gv70", "g80"))

SUBARU = _pack(
    "subaru",
    "Subaru",
    ("wrx", "outback", "forester", "ascent"),
    _SUBARU_MODULES,
    gateways=(0x0706,),
    description="Subaru — EyeSight camera module included in probe list.",
)

MITSUBISHI = _pack(
    "mitsubishi",
    "Mitsubishi",
    ("mitsu", "outlander", "lancer", "evo"),
    _MITSU_MODULES,
    gateways=(0x0706,),
)

RENAULT = _pack(
    "renault",
    "Renault",
    ("dacia", "alpine"),
    _RENAULT_MODULES,
    gateways=(0x0706,),
)

SUZUKI = _pack(
    "suzuki",
    "Suzuki",
    ("vitara", "jimny"),
    (
        EcuModule(0x0700, "ECM", "Engine"),
        EcuModule(0x0701, "TCM", "Transmission"),
        EcuModule(0x0702, "ABS", "ABS"),
        EcuModule(0x0703, "SRS", "Airbag"),
        EcuModule(0x0704, "BCM", "Body"),
        EcuModule(0x0705, "METER", "Meter"),
        EcuModule(0x0706, "GATEWAY", "Gateway"),
        EcuModule(0x0707, "HVAC", "HVAC"),
        EcuModule(0x0708, "EPS", "EPS"),
        *_US_OBD,
    ),
    gateways=(0x0706,),
)

VOLVO = _pack(
    "volvo",
    "Volvo",
    ("volvo_cars",),
    (
        EcuModule(0x0101, "CEM", "Central electronic module"),
        EcuModule(0x010A, "ECM", "Engine"),
        EcuModule(0x010B, "TCM", "Transmission"),
        EcuModule(0x0110, "BCM", "Body"),
        EcuModule(0x0120, "DIM", "Driver info module"),
        EcuModule(0x0130, "SUM", "Suspension"),
        EcuModule(0x0140, "SRS", "SRS"),
        EcuModule(0x0150, "PSCM", "Power steering"),
        EcuModule(0x01A0, "AUD", "Audio"),
        EcuModule(0x4010, "DOIP_GW", "DoIP gateway style"),
    ),
    gateways=(0x0101, 0x4010),
    description="Volvo SPA/CMA platforms are DoIP-capable; CEM is a common entry point.",
)
POLESTAR = _derive(VOLVO, "polestar", "Polestar", ("polestar2", "polestar3"))

PORSCHE = _pack(
    "porsche",
    "Porsche",
    ("911", "cayenne", "macan", "taycan"),
    (
        EcuModule(0x4010, "GATEWAY", "DoIP gateway (VAG-family platforms)"),
        EcuModule(0x0010, "DME", "Engine"),
        EcuModule(0x0002, "PDK", "PDK transmission"),
        EcuModule(0x0003, "PSM", "PSM / ABS"),
        EcuModule(0x0009, "FRONT_END", "Front end electronics"),
        EcuModule(0x0017, "CLUSTER", "Cluster"),
        EcuModule(0x005F, "PCM", "PCM infotainment"),
        EcuModule(0x0019, "CAN_GW", "CAN gateway"),
        EcuModule(0x0015, "AIRBAG", "Airbag"),
        EcuModule(0x0042, "DOOR_DR", "Driver door"),
    ),
    gateways=(0x4010, 0x0019),
    description="Newer Porsche share VAG-ish DoIP patterns; classic cars differ.",
)

JAGUAR_LR = _pack(
    "jaguar_lr",
    "Jaguar / Land Rover",
    ("jlr",),
    (
        EcuModule(0x0700, "PCM", "Powertrain"),
        EcuModule(0x0701, "TCM", "Transmission"),
        EcuModule(0x0702, "ABS", "ABS"),
        EcuModule(0x0703, "RCM", "Restraints"),
        EcuModule(0x0704, "BCM", "Body"),
        EcuModule(0x0705, "GATEWAY", "Gateway"),
        EcuModule(0x0706, "IPK", "Instrument pack"),
        EcuModule(0x0707, "ATCM", "Terrain / ATCM"),
        EcuModule(0x0708, "HVAC", "HVAC"),
        EcuModule(0x0709, "PACM", "Parking aid"),
        EcuModule(0x14DA, "DOIP", "DoIP entity scaffold"),
    ),
    gateways=(0x0705, 0x14DA),
)
JAGUAR = _derive(JAGUAR_LR, "jaguar", "Jaguar", ("f_pace", "xe", "xf"))
LAND_ROVER = _derive(
    JAGUAR_LR,
    "landrover",
    "Land Rover",
    ("land_rover", "lr", "range_rover", "defender", "discovery"),
)

TESLA = _pack(
    "tesla",
    "Tesla",
    ("model_3", "model_y", "model_s", "model_x"),
    (
        EcuModule(0x0001, "VCLEFT", "Vehicle controller left"),
        EcuModule(0x0002, "VCRIGHT", "Vehicle controller right"),
        EcuModule(0x0003, "VCFRONT", "Vehicle controller front"),
        EcuModule(0x0010, "BMS", "Battery management"),
        EcuModule(0x0020, "DI", "Drive inverter"),
        EcuModule(0x0030, "GTW", "Gateway"),
        EcuModule(0x0040, "MCU", "Media control"),
        EcuModule(0x0050, "AUTOPILOT", "Autopilot / HW"),
    ),
    gateways=(0x0030,),
    description="Tesla access is limited/model-specific — scaffold only.",
)

RIVIAN = _pack(
    "rivian",
    "Rivian",
    ("r1t", "r1s"),
    (
        EcuModule(0x0700, "VDM", "Vehicle dynamics"),
        EcuModule(0x0701, "BMS", "Battery"),
        EcuModule(0x0702, "GATEWAY", "Gateway"),
        EcuModule(0x0703, "TZM", "Thermal"),
        EcuModule(0x0704, "XMM", "Infotainment"),
        EcuModule(0x0705, "EZC", "Zone controller"),
        *_US_OBD,
    ),
    gateways=(0x0702,),
)

LUCID = _pack(
    "lucid",
    "Lucid",
    ("air", "gravity"),
    (
        EcuModule(0x0700, "VCU", "Vehicle control"),
        EcuModule(0x0701, "BMS", "Battery"),
        EcuModule(0x0702, "GATEWAY", "Gateway"),
        EcuModule(0x0703, "INV", "Inverter"),
        EcuModule(0x0704, "CGM", "Cabin"),
        *_US_OBD,
    ),
    gateways=(0x0702,),
)


EXTRA_PACKS = (
    # High-demand US / JP brands first
    FORD,
    LINCOLN,
    CHEVY,
    GM,
    GMC,
    CADILLAC,
    BUICK,
    HOLDEN,
    DODGE,
    JEEP,
    RAM,
    CHRYSLER,
    STELLANTIS,
    FIAT,
    ALFA,
    PEUGEOT,
    CITROEN,
    HONDA,
    ACURA,
    NISSAN,
    INFINITI,
    MAZDA,
    TOYOTA,
    HYUNDAI,
    KIA,
    GENESIS,
    SUBARU,
    MITSUBISHI,
    SUZUKI,
    RENAULT,
    VOLVO,
    POLESTAR,
    PORSCHE,
    JAGUAR,
    LAND_ROVER,
    JAGUAR_LR,
    TESLA,
    RIVIAN,
    LUCID,
)
