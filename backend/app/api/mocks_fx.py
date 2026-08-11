import xml.etree.ElementTree as ET

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(prefix="/mocks/fx", tags=["mocks-fx"])

FX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rates base="HKD">
  <rate pair="USDHKD" value="7.8500"/>
  <rate pair="EURHKD" value="8.4200"/>
  <rate pair="GBPHKD" value="9.9100"/>
</rates>
"""


def parse_fx_xml(xml_text: str) -> dict[str, float]:
    """Parse FX XML into {pair: value}. Used later by the aggregator."""
    root = ET.fromstring(xml_text)
    rates: dict[str, float] = {}
    for rate in root.findall("rate"):
        pair = rate.attrib["pair"]
        rates[pair] = float(rate.attrib["value"])
    return rates


@router.get("/rates")
def get_fx_rates():
    return Response(content=FX_XML.strip(), media_type="application/xml")