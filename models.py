from pydantic import BaseModel
from typing import Optional, Dict, List

class Property(BaseModel):
    title: str
    location: str
    price: str
    bhk: Optional[str] = None
    property_type: str
    transactionType: Optional[str] = None
    anyConstructionDone: Optional[str] = None
    plotFacing: Optional[str] = None
    cabins: Optional[str] = None
    workstations: Optional[str] = None
    pantry: Optional[str] = None
    washroom: Optional[str] = None
    highSpeedInternet: Optional[str] = None
    publicTransport: Optional[str] = None
    amenities: Optional[Dict] = None
    propertyFeatures: Optional[Dict] = None
    images: Optional[Dict[str, List[str]]] = None
    negotiable: Optional[str] = None