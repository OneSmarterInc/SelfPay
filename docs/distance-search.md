# Distance search

City/ZIP searches resolve against bundled Census data. Ambiguous or misspelled names require selection. Unknown places prompt for a five-digit ZIP. State-only and National browsing remain available without distance claims.

The server computes Haversine straight-line miles to imported facility coordinates and uses the closest eligible location per offer. Radius defaults to 50 miles; choices are 25, 50, 100 and 250. Results within the radius sort by distance, including across state borders. With no in-radius offer, the nearest three eligible offers anywhere appear under the requested fallback heading. Procedure, protocol and price-type filters remain in force.

Cards label approximate miles and city-center/ZIP-reference precision. These are not driving distances. State-covering programs appear separately without distances. Directory leads with the selected modality, no mapped numeric price and no numeric price wording appear below results as quote leads within the radius; members must confirm exact exam availability.

For multi-location entries, a price's existing region must explicitly name a location's city, or the reviewed offer must supply an explicit locations list. Coordinates alone do not extend branch pricing. Offers without valid price-location coordinates are omitted with a visible notice, and remain available through National browsing. The nearest-three fallback cannot recover missing coordinates.

The classic interface and Ask MySelfPay call the same server search. No search-time geocoding or external location service is used. Tests: `python -m unittest test_proximity test_geo test_facility_locations -v`.

Deployment prerequisite: existing database entries need the separately reviewed coordinate-enriched import. This code does not backfill the live database. Complete that staged import and price-mapping review under the live-change policy before claiming complete live distance coverage.
