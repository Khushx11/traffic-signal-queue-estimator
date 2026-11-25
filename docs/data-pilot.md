# FHWA data pilot

The [ITS DataHub metadata](https://data.transportation.gov/api/views/8ect-6jqj)
identifies the trajectory and supporting-data collection as CC BY-SA 3.0.
Check terms on each video collection and asset before redistributing footage or
derived material. The repository stores download instructions and the inventory.

The Peachtree support archive contains a vehicle trajectory CSV and a nested
signal-timing archive. The latter contains movement-specific transition tables,
including northbound left-turn and through records for Peachtree and 10th Street
during the 12:45–1:00 recording period. These are candidates for phase evidence.
Confirm their units and synchronisation against the video before interpreting them
as verified signals. The support CSV has 873,887 trajectory rows. An inspection
found 10-digit Global_Time values that advance by 100 in successive sampled frames.
Resolve the actual time origin before mapping those values to the video clock.

Record an alignment audit for each included approach. In a development recording,
choose distinctive events such as stop-line crossings and match them against
trajectory positions to quantify residual offsets. For final tests, establish
reference alignment independently of estimator setup and tuning. List uncovered
queue tails, missing phases and independently unresolvable counts.

## Australian external test

Adelaide hourly intersection volumes can guide site selection. Main Roads WA
publishes site diagrams, phase sequences and timing reports where available.
Transport for NSW lists camera snapshots and Brisbane City Council offers a
footage request pathway. None of these alone establishes a verified cycle-level
queue reference. Add Australian results when permission-cleared continuous
footage and audited per-lane counts are available.

- [City of Adelaide intersection volumes](https://researchdata.edu.au/traffic-intersection-volumes/2210790)
- [Main Roads WA signal information](https://reportingcentreresources.mainroads.wa.gov.au/pdf/TrafficMap_Information_Sheet_Traffic_Lights.pdf)
- [Transport for NSW camera catalogue](https://opendata.transport.nsw.gov.au/data/dataset/?license_id=cc-by&tags=camera+locations&tags=traffic+images)
- [Brisbane CCTV footage requests](https://www.brisbane.qld.gov.au/transport-and-parking/traffic-management-and-safety/traffic-safety-and-cctv)
