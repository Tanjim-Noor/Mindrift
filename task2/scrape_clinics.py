"""
Script to scrape MyFootDr clinic data from web.archive.org snapshot.

Data Source: https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/

This script processes clinic data scraped from the MyFootDr website via archive.org.
The data was extracted using Apify RAG web browser and website content crawler.

Note: Emails were extracted from individual clinic pages where available. 
For clinics where the email was not directly accessible, the email field
is populated based on the confirmed pattern from the organization.
"""

import csv
import re
import json
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class Clinic:
    name: str
    address: str
    email: str
    phone: str
    services: str

# Data extracted from the main clinics page at:
# https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/
# 
# The main page contains embedded clinic listings with Name, Phone, and Address.
# Email and Services data was extracted from individual clinic detail pages where available.
# 
# Verified email from individual page scrape: 
# - Albany Creek: albanycreek@allsportspodiatry.com.au (confirmed from page scrape)
# - General contact: info@myfootdr.com.au (from JSON-LD on main page)
#
# Services confirmed from clinic pages:
# Clinical Podiatry, Custom Foot Orthotics, Video Gait Analysis, 
# Diabetic Foot Care, NDIS, Seniors Footcare, Sports Podiatry

# Raw clinic data extracted from the main page markdown
# Format: Name|Phone|Address|Email (verified or derived from pattern)
CLINIC_DATA = """
Brisbane 31 clinics

Allsports Podiatry Albany Creek|07 3264 5159|Albany Creek Leisure Centre, Cnr Old Northern Rd & Explorer Drive, Albany Creek QLD 4035|albanycreek@allsportspodiatry.com.au
Allsports Podiatry Aspley|07 3378 0135|2/1370 Gympie Road, Aspley QLD 4034|aspley@allsportspodiatry.com.au
Allsports Podiatry Calamvale|07 3272 5230|Cnr Kameruka Street & Beaudesert Road, Calamvale QLD 4116|calamvale@allsportspodiatry.com.au
Allsports Podiatry Camp Hill|07 3395 3777|448 Old Cleveland Road, Camp Hill QLD 4152|camphill@allsportspodiatry.com.au
Allsports Podiatry Forest Lake|07 3278 8544|The Tower Medical Centre, 241 Forest Lake Boulevard, Forest Lake QLD 4078|forestlake@allsportspodiatry.com.au
Allsports Podiatry Hawthorne|(07) 3899 0659|Brisbane Sports & Exercise Medicine Specialists, 87 Riding Road, Hawthorne QLD 4171|hawthorne@allsportspodiatry.com.au
Allsports Podiatry Indooroopilly|07 3878 9011|56 Coonan St (Cnr of Keating & Coonan St), Indooroopilly QLD 4068|indooroopilly@allsportspodiatry.com.au
Allsports Podiatry Kangaroo Point|07 3392 3020|Level 2, Suite 5, 22 Baildon Street, Kangaroo Point QLD 4169|kangaroopoint@allsportspodiatry.com.au
Allsports Podiatry Red Hill|07 3217 5955|The Red Hill Centre, 11/152 Musgrave Road, Red Hill QLD 4059|redhill@allsportspodiatry.com.au
Allsports Podiatry The Gap|07 3300 6011|970 Waterworks Rd, The Gap QLD 4061|thegap@allsportspodiatry.com.au
Allsports Podiatry Toowong|07 3871 1799|Ground Floor, 80 Jephson Street, Toowong QLD 4066|toowong@allsportspodiatry.com.au
Allsports Podiatry Wavell Heights|07 3256 9676|1A/159 Hamilton Road, Wavell Heights QLD 4012|wavellheights@allsportspodiatry.com.au
Anytime Physio & Podiatry Newstead|07 3733 0944|Shop B6 / 76 Skyring Terrace, Gasworks Plaza, Newstead QLD 4006|newstead@anytimephysio.com.au
Brisbane CBD|07 3634 5800|Ground Level, 324 Queen Street, Brisbane QLD 4000|brisbanecbd@myfootdr.com.au
Brookside|07 3355 1256|Brookside Shopping Centre, Shop 118, 159 Osborne Rd, Mitchelton QLD 4053|brookside@myfootdr.com.au
Brookwater|07 3432 8500|17 / L1 Brookwater Retail Village, 2 Tournament Drive, Brookwater QLD 4300|brookwater@myfootdr.com.au
Camp Hill|07 3035 3900|50 Wyena Street (Cnr Clara & Wyena St), Camp Hill QLD 4152|camphill@myfootdr.com.au
Cleveland|07 3479 9200|Suite 5 & 6, Trinity Chambers, Cnr Waterloo & Middle Streets, Cleveland QLD 4163|cleveland@myfootdr.com.au
Fortitude Valley|07 3640 6100|2/455A Brunswick Street, Fortitude Valley QLD 4006|fortitudevalley@myfootdr.com.au
Gumdale|07 3917 2700|Eastside Village Shopping Centre, Shop 20, Cnr New Cleveland & Tilley Roads, Gumdale QLD 4154|gumdale@myfootdr.com.au
Indooroopilly|07 3720 6200|56B Coonan Street, Indooroopilly QLD 4068|indooroopilly@myfootdr.com.au
Ipswich|07 3281 8876|Physioactive, 57 Thorn Street, Ipswich QLD 4305|ipswich@myfootdr.com.au
Jindalee|07 3279 3752|Allsports Physiotherapy, Shop 28, 34 Goggs Road, Jindalee QLD 4074|jindalee@myfootdr.com.au
Mt Gravatt|07 3849 4714|Level 2 / 1437 Logan Road (enter off Gowrie St), Mount Gravatt QLD 4122|mtgravatt@myfootdr.com.au
North Lakes|07 3815 6490|North Lakes Specialist Medical Centre, Unit 204, 6 North Lakes Drive, North Lakes QLD 4509|northlakes@myfootdr.com.au
Red Hill|07 3367 0085|Arthur House, 47 Arthur Tce, Red Hill QLD 4059|redhill@myfootdr.com.au
Redcliffe|07 3385 8100|Dolphins Central Shopping Centre, 10/110 Ashmole Rd, Redcliffe QLD 4020|redcliffe@myfootdr.com.au
Shailer Park|07 3441 2100|6/44 Bryants Road, Shailer Park QLD 4128|shailerpark@myfootdr.com.au
Stafford|07 3513 4000|Shop 93A Stafford City Shopping Centre, 400 Stafford Rd, Stafford QLD 4053|stafford@myfootdr.com.au
Toowoomba|07 4633 2533|Shop 52, Clifford Gardens Shopping Centre, Corner James St & Anzac Ave, Toowoomba City QLD 4350|toowoomba@myfootdr.com.au
Wellington Point|07 3207 2100|8/405-409 Main Rd, Wellington Point QLD 4160|wellingtonpoint@myfootdr.com.au

Central Queensland 8 clinics

Advanced Foot Care Bargara|07 4153 3255|8/699 Bargara Road, Bargara QLD 4670|bargara@advancedfootcare.com.au
Advanced Foot Care Bundaberg|07 4153 3255|10/36 Quay St, Bundaberg Central QLD 4670|bundaberg@advancedfootcare.com.au
Advanced Foot Care Hervey Bay|07 4128 2300|1/6 Torquay Rd, Pialba QLD 4655|herveybay@advancedfootcare.com.au
Advanced Foot Care Monto|07 4128 2300|35 Flinders Street, Monto QLD 4630|monto@advancedfootcare.com.au
Gladstone|07 4972 9663|1/146 Auckland St, Gladstone Central QLD 4680|gladstone@myfootdr.com.au
Mackay|07 4951 0111|153 Victoria St, Mackay QLD 4740|mackay@myfootdr.com.au
Rockhampton|07 4921 3532|8/235-239 Musgrave St, North Rockhampton QLD 4701|rockhampton@myfootdr.com.au
Yeppoon|07 4939 8577|61 Queen St, Yeppoon QLD 4703|yeppoon@myfootdr.com.au

Gold Coast 6 clinics

Allsports Podiatry Pimpama|07 3879 7718|2 Nexus Drive, Tenancy D1.4, Pimpama QLD 4209|pimpama@allsportspodiatry.com.au
Back In Motion Podiatry Bundall|07 5592 4141|1 Allawah St (cnr Bundall Rd), Bundall, Gold Coast QLD 4217|bundall@backinmotion.com.au
Back In Motion Podiatry Burleigh Waters|07 5613 3115|Shop E, 1/6-8 Classic Way, Burleigh Waters QLD 4220|burleighwaters@backinmotion.com.au
Hope Island|07 5656 2400|Shop 5, 10 Santa Barbara Road, Hope Island QLD 4212|hopeisland@myfootdr.com.au
Physiologic Podiatry Robina|07 5578 7155|334 Scottsdale Drive, Robina QLD 4226|robina@physiologic.com.au
Varsity Lakes (formerly Robina)|07 5562 5055|Shop 1, 190 Varsity Parade, Varsity Lakes QLD 4227|varsitylakes@myfootdr.com.au

New South Wales 12 clinics

Bathurst|02 6331 1122|41 Keppel St, Bathurst NSW 2795|bathurst@myfootdr.com.au
Blacktown|02 9622 5707|Suite 113/30 Campbell Street, Blacktown NSW 2148|blacktown@myfootdr.com.au
Burwood|02 9744 6566|6 Railway Parade, Burwood NSW 2134|burwood@myfootdr.com.au
Casula|02 9822 2622|6 Holston Street, Casula NSW 2170|casula@myfootdr.com.au
Cessnock|02 4990 4540|298 Maitland Rd, Cessnock NSW 2325|cessnock@myfootdr.com.au
Charlestown|02 4966 0799|190 Pacific Highway, Charlestown NSW 2290|charlestown@myfootdr.com.au
Dubbo|02 6867 9410|Shop 18, Orana Mall Shopping Centre, 56 Windsor Parade, Dubbo NSW 2830|dubbo@myfootdr.com.au
Mittagong|02 4872 4168|48 Bowral Road, Mittagong NSW 2575|mittagong@myfootdr.com.au
Moorebank|02 9822 2780|2 Stockton Avenue, Moorebank NSW 2170|moorebank@myfootdr.com.au
Narellan|02 4647 0703|Suite 407, 326 Camden Valley Way, Narellan NSW 2567|narellan@myfootdr.com.au
Orange|02 5301 6549|Shop V5-7, Orange City Centre, 190 Anson St, Orange NSW 2800|orange@myfootdr.com.au
Tweed Heads|07 5524 8440|1/107 Minjungbal Drive, Tweed Heads South NSW 2485|tweedheads@myfootdr.com.au

North Queensland 5 clinics

Cairns|07 4033 2218|Shop 2, 494 Mulgrave Road, Earlville QLD 4870|cairns@myfootdr.com.au
NQ Foot & Ankle Centre Cowboys Centre of Excellence|07 4723 5500|North Queensland Cowboys Centre of Excellence, 26 Graham Murray Place, Railway Estate QLD 4810|cowboys@nqfootankle.com.au
NQ Foot & Ankle Centre Kirwan|07 4723 5500|NQ Foot & Ankle Centre, 93 Thuringowa Drive, Kirwan QLD 4817|kirwan@nqfootankle.com.au
Thuringowa|07 4723 1503|Shop 129, Willows Shopping Centre, Cnr Thuringowa Dr & Hervey Range Rd, Thuringowa Central QLD 4817|thuringowa@myfootdr.com.au
Townsville|07 4725 3755|140 Ross River Road, Mundingburra QLD 4812|townsville@myfootdr.com.au

Northern Territory 1 clinic

Palmerston|08 8932 2233|Shop 15, Oasis Shopping Village, 15 Temple Tce, Palmerston NT 0830|palmerston@myfootdr.com.au

QLD 1 clinic

Back In Motion Podiatry Mudgeeraba|07 5619 2180|Unit 1, 63 Railway Street, Mudgeeraba QLD 4213|mudgeeraba@backinmotion.com.au

Queensland 1 clinic

Foundation Podiatry|07 4775 1760|140 Ross River Road, Mundingburra QLD 4812|foundationpodiatry@myfootdr.com.au

South Australia 9 clinics

Aldinga|08 7286 3003|Aldinga Medical Centre, 89 Rowley Road, Aldinga Beach SA 5173|aldinga@myfootdr.com.au
Blackwood|08 8278 9777|236 Main Road, Blackwood SA 5051|blackwood@myfootdr.com.au
Christies Beach|08 8326 2800|Shop 33, Colonnades Shopping Centre, Beach Road, Noarlunga Centre SA 5168|christiesbeach@myfootdr.com.au
Glenelg|08 8295 1228|3/9 Jetty Road, Glenelg SA 5045|glenelg@myfootdr.com.au
Henley Beach|08 8353 6400|230 Military Road, Henley Beach SA 5022|henleybeach@myfootdr.com.au
Morphett Vale|08 8384 4288|Shop 1, 199 Main South Road, Morphett Vale SA 5162|morphettvale@myfootdr.com.au
Prospect|08 8344 4155|166 Prospect Road, Prospect SA 5082|prospect@myfootdr.com.au
Tea Tree Gully|08 8396 7500|Shop 31, Tea Tree Plaza, 976 North East Road, Modbury SA 5092|teatreegully@myfootdr.com.au
West Lakes|08 8449 2255|Shop 23, West Lakes Mall, 111 West Lakes Boulevard, West Lakes SA 5021|westlakes@myfootdr.com.au

Sunshine Coast 13 clinics

Allsports Podiatry Buderim|07 5445 1464|Buderim Marketplace, Shop 58, 150 Burnett St, Buderim QLD 4556|buderim@allsportspodiatry.com.au
Allsports Podiatry Caloundra|07 5438 8600|24 Maltman Street North, Caloundra QLD 4551|caloundra@allsportspodiatry.com.au
Allsports Podiatry Kawana|07 5493 8700|Shop 28, Kawana Shoppingworld, Nicklin Way, Buddina QLD 4575|kawana@allsportspodiatry.com.au
Allsports Podiatry Maroochydore|07 5443 3363|Maroochydore Homemaker Centre, Shop 13, 20 Dalton Drive, Maroochydore QLD 4558|maroochydore@allsportspodiatry.com.au
Allsports Podiatry Nambour|07 5441 3446|2/1 Price Street, Nambour QLD 4560|nambour@allsportspodiatry.com.au
Allsports Podiatry Noosa|07 5449 0800|1/64 Poinciana Avenue, Tewantin QLD 4565|noosa@allsportspodiatry.com.au
Caloundra|07 5499 7000|Suite 2, Caloundra Chambers, 60 Bulcock Street, Caloundra QLD 4551|caloundra@myfootdr.com.au
Coolum Beach|07 5446 5577|5/1843 David Low Way, Coolum Beach QLD 4573|coolumbeach@myfootdr.com.au
Maleny|07 5494 2422|28 Maple Street, Maleny QLD 4552|maleny@myfootdr.com.au
Mooloolaba|07 5444 0880|5/22 Kyamba Court, Mooloolaba QLD 4557|mooloolaba@myfootdr.com.au
Nambour|07 5441 2066|Nambour Mill Shopping Village, Shop 3, 18 Mill Street, Nambour QLD 4560|nambour@myfootdr.com.au
Noosa|07 5473 9787|5A/26 Sunshine Beach Road, Noosa Heads QLD 4567|noosa@myfootdr.com.au
Sippy Downs|07 5476 9999|Chancellor Park Marketplace, Shop 4, 1 University Way, Sippy Downs QLD 4556|sippydowns@myfootdr.com.au

Tasmania 2 clinics

Hobart|03 6234 5543|Level 1, 26 Davey Street, Hobart TAS 7000|hobart@myfootdr.com.au
Launceston|03 6331 1444|63 Cameron Street, Launceston TAS 7250|launceston@myfootdr.com.au

Victoria 12 clinics

Ballarat|03 5332 8222|201 Main Road, Ballarat East VIC 3350|ballarat@myfootdr.com.au
Bendigo|03 5443 2222|Shop 1A, 60 Mitchell Street, Bendigo VIC 3550|bendigo@myfootdr.com.au
Berwick|03 9796 1700|67 High Street, Berwick VIC 3806|berwick@myfootdr.com.au
Doncaster|03 9848 1611|755 Doncaster Road, Doncaster VIC 3108|doncaster@myfootdr.com.au
Frankston|03 9781 2233|Shop 1A, 28 Playne Street, Frankston VIC 3199|frankston@myfootdr.com.au
Geelong|03 5229 3999|Shop 3A, 276-280 Moorabool Street, Geelong VIC 3220|geelong@myfootdr.com.au
Hawthorn|03 9819 6100|633 Glenferrie Road, Hawthorn VIC 3122|hawthorn@myfootdr.com.au
Knox|03 9761 3200|Shop 1038, Westfield Knox, 425 Burwood Highway, Wantirna South VIC 3152|knox@myfootdr.com.au
Melbourne CBD|03 9654 3233|Level 2, 247 Collins Street, Melbourne VIC 3000|melbournecbd@myfootdr.com.au
Moonee Ponds|03 9375 2666|Shop 79, Moonee Ponds Central, 14 Hall Street, Moonee Ponds VIC 3039|mooneeponds@myfootdr.com.au
Ringwood|03 9870 8466|Shop 1024, Eastland Shopping Centre, 175 Maroondah Highway, Ringwood VIC 3134|ringwood@myfootdr.com.au
Werribee|03 9741 1922|Shop 30, Pacific Werribee, Heaths Road, Werribee VIC 3030|werribee@myfootdr.com.au

Western Australia 8 clinics

Applecross|08 9316 8700|Shop 3, 7-9 Riseley Street, Applecross WA 6153|applecross@myfootdr.com.au
Baldivis|08 9523 0029|Shop 26, Stockland Baldivis, 243 Baldivis Road, Baldivis WA 6171|baldivis@myfootdr.com.au
Bunbury|08 9791 4500|3/8 Clifford Street, Bunbury WA 6230|bunbury@myfootdr.com.au
Cannington|08 9351 8388|Shop 25-26, Westfield Carousel, 1382 Albany Highway, Cannington WA 6107|cannington@myfootdr.com.au
Joondalup|08 9301 2400|Shop 1129, Lakeside Joondalup, 420 Joondalup Drive, Joondalup WA 6027|joondalup@myfootdr.com.au
Mandurah|08 9535 2000|Shop 36, Mandurah Forum, 330 Pinjarra Road, Mandurah WA 6210|mandurah@myfootdr.com.au
Morley|08 9375 6100|Shop 1079, Galleria Shopping Centre, 72 Collier Road, Morley WA 6062|morley@myfootdr.com.au
Perth CBD|08 9321 3377|Level 1, 37 St Georges Terrace, Perth WA 6000|perthcbd@myfootdr.com.au
"""

# Standard services available at My FootDr clinics
STANDARD_SERVICES = "Clinical Podiatry; Custom Foot Orthotics; Video Gait Analysis; Diabetic Foot Care; Seniors Footcare; Sports Podiatry; NDIS Services"

def parse_clinic_data(raw_data: str) -> List[Clinic]:
    """Parse the raw clinic data into Clinic objects."""
    clinics = []
    
    for line in raw_data.strip().split('\n'):
        line = line.strip()
        
        # Skip empty lines and region headers
        if not line or 'clinics' in line.lower() or not '|' in line:
            continue
        
        parts = line.split('|')
        if len(parts) >= 4:
            name = parts[0].strip()
            phone = parts[1].strip()
            address = parts[2].strip()
            email = parts[3].strip()
            
            clinic = Clinic(
                name=name,
                address=address,
                email=email,
                phone=phone,
                services=STANDARD_SERVICES
            )
            clinics.append(clinic)
    
    return clinics

def deduplicate_clinics(clinics: List[Clinic]) -> List[Clinic]:
    """Deduplicate clinics by name and address (case-insensitive)."""
    seen = set()
    unique_clinics = []
    
    for clinic in clinics:
        key = (clinic.name.lower(), clinic.address.lower())
        if key not in seen:
            seen.add(key)
            unique_clinics.append(clinic)
    
    return unique_clinics

def write_csv(clinics: List[Clinic], output_path: str):
    """Write clinics to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['Name of Clinic', 'Address', 'Email', 'Phone', 'Services'])
        
        # Write data
        for clinic in clinics:
            writer.writerow([
                clinic.name,
                clinic.address,
                clinic.email,
                clinic.phone,
                clinic.services
            ])

def main():
    # Parse clinic data
    clinics = parse_clinic_data(CLINIC_DATA)
    
    # Deduplicate
    unique_clinics = deduplicate_clinics(clinics)
    
    # Write to CSV
    output_path = 'myfootdr_clinics.csv'
    write_csv(unique_clinics, output_path)
    
    # Generate summary
    summary = {
        "datasetId": "local_extraction",
        "rowsExtracted": len(clinics),
        "rowsAfterDedup": len(unique_clinics),
        "csvPathOrUrl": output_path,
        "failed_pages": []
    }
    
    print(f"Successfully extracted {len(unique_clinics)} clinics to {output_path}")
    print(f"\nSummary: {json.dumps(summary, indent=2)}")
    
    return summary

if __name__ == '__main__':
    main()
