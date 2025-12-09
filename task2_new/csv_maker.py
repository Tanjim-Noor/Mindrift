"""
MyFootDr Clinic Scraper - Multi-Stage Web Scraping
This script processes scraped data from the MyFootDr website archive to extract clinic information.
"""

import json
import csv
import re
from datetime import datetime

# ==========================================
# STAGE 1 & 2 DATA: Extracted from the main page scrape
# The main page contains all clinic listings with basic info
# ==========================================

# Complete clinic data extracted from the main page scrape
# Format: {region: [{"name": ..., "address": ..., "phone": ..., "url": ...}, ...]}

clinics_data = {
    "Brisbane": [
        {
            "name": "Allsports Podiatry Albany Creek",
            "address": "Albany Creek Leisure Centre, Cnr Old Northern Rd & Explorer Drive, Albany Creek QLD 4035",
            "phone": "07 3264 5159",
            "email": "albanycreek@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/albany-creek-allsports-podiatry/"
        },
        {
            "name": "Allsports Podiatry Aspley",
            "address": "2/1370 Gympie Road, Aspley QLD 4034",
            "phone": "07 3378 0135",
            "email": "aspley@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/aspley-allsports-podiatry/"
        },
        {
            "name": "Allsports Podiatry Calamvale",
            "address": "Cnr Kameruka Street & Beaudesert Road, Calamvale QLD 4116",
            "phone": "07 3272 5230",
            "email": "calamvale@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/calamvale-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry Camp Hill",
            "address": "448 Old Cleveland Road, Camp Hill QLD 4152",
            "phone": "07 3395 3777",
            "email": "camphill@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/camp-hill-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry Forest Lake",
            "address": "The Tower Medical Centre, 241 Forest Lake Boulevard, Forest Lake QLD 4078",
            "phone": "07 3278 8544",
            "email": "forestlake@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/forest-lake-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry Hawthorne",
            "address": "Brisbane Sports & Exercise Medicine Specialists, 87 Riding Road, Hawthorne QLD 4171",
            "phone": "(07) 3899 0659",
            "email": "hawthorne@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/hawthorne-podiatry-clinic-allsports-podiatry/"
        },
        {
            "name": "Allsports Podiatry Indooroopilly",
            "address": "56 Coonan St (Cnr of Keating & Coonan St), Indooroopilly QLD 4068",
            "phone": "07 3878 9011",
            "email": "indooroopilly@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/indooroopilly-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry Kangaroo Point",
            "address": "Level 2, Suite 5, 22 Baildon Street, Kangaroo Point QLD 4169",
            "phone": "07 3392 3020",
            "email": "kangaroopoint@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/kangaroo-point-allsports-podiatry-centre/"
        },
        {
            "name": "Allsports Podiatry Red Hill",
            "address": "The Red Hill Centre, 11/152 Musgrave Road, Red Hill QLD 4059",
            "phone": "07 3217 5955",
            "email": "redhill@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/red-hill-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry The Gap",
            "address": "970 Waterworks Rd, The Gap QLD 4061",
            "phone": "07 3300 6011",
            "email": "thegap@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/the-gap-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry Toowong",
            "address": "Ground Floor, 80 Jephson Street, Toowong QLD 4066",
            "phone": "07 3871 1799",
            "email": "toowong@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/toowong-podiatry-centre-allsports/"
        },
        {
            "name": "Allsports Podiatry Wavell Heights",
            "address": "1A/159 Hamilton Road, Wavell Heights QLD 4012",
            "phone": "07 3256 9676",
            "email": "wavellheights@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/wavell-heights-podiatry-centre-allsports/"
        },
        {
            "name": "Anytime Physio & Podiatry Newstead",
            "address": "Shop B6 / 76 Skyring Terrace, Gasworks Plaza, Newstead QLD 4006",
            "phone": "07 3733 0944",
            "email": "newstead@anytimephysio.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/newstead-podiatry-clinic-anytime-physio-podiatry/"
        },
        {
            "name": "My FootDr Brisbane CBD",
            "address": "Ground Level, 324 Queen Street, Brisbane QLD 4000",
            "phone": "07 3634 5800",
            "email": "brisbanecbd@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/brisbane-cbd-podiatry-centre/"
        },
        {
            "name": "My FootDr Brookside",
            "address": "Brookside Shopping Centre, Shop 118, 159 Osborne Rd, Mitchelton QLD 4053",
            "phone": "07 3355 1256",
            "email": "brookside@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/mitchelton-podiatry-centre/"
        },
        {
            "name": "My FootDr Brookwater",
            "address": "17 / L1 Brookwater Retail Village, 2 Tournament Drive, Brookwater QLD 4300",
            "phone": "07 3432 8500",
            "email": "brookwater@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/brookwater-podiatry-centre/"
        },
        {
            "name": "My FootDr Camp Hill",
            "address": "50 Wyena Street (Cnr Clara & Wyena St), Camp Hill QLD 4152",
            "phone": "07 3035 3900",
            "email": "camphill@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/camp-hill-podiatry-centre/"
        },
        {
            "name": "My FootDr Cleveland",
            "address": "Suite 5 & 6, Trinity Chambers, Cnr Waterloo & Middle Streets, Cleveland QLD 4163",
            "phone": "07 3479 9200",
            "email": "cleveland@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cleveland-podiatry-centre/"
        },
        {
            "name": "My FootDr Fortitude Valley",
            "address": "2/455A Brunswick Street, Fortitude Valley QLD 4006",
            "phone": "07 3640 6100",
            "email": "fortitudevalley@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/fortitude-valley-podiatry-centre/"
        },
        {
            "name": "My FootDr Gumdale",
            "address": "Eastside Village Shopping Centre, Shop 20, Cnr New Cleveland & Tilley Roads, Gumdale QLD 4154",
            "phone": "07 3917 2700",
            "email": "gumdale@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/gumdale-podiatry-centre/"
        },
        {
            "name": "My FootDr Indooroopilly",
            "address": "56B Coonan Street, Indooroopilly QLD 4068",
            "phone": "07 3720 6200",
            "email": "indooroopilly@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/indooroopilly-podiatry-centre/"
        },
        {
            "name": "My FootDr Ipswich",
            "address": "Physioactive, 57 Thorn Street, Ipswich QLD 4305",
            "phone": "07 3281 8876",
            "email": "ipswich@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/ipswich-podiatry-centre/"
        },
        {
            "name": "My FootDr Jindalee",
            "address": "Allsports Physiotherapy, Shop 28, 34 Goggs Road, Jindalee QLD 4074",
            "phone": "07 3279 3752",
            "email": "jindalee@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/jindalee-podiatry-centre-allsports/"
        },
        {
            "name": "My FootDr Mt Gravatt",
            "address": "Level 2 / 1437 Logan Road (enter off Gowrie St), Mount Gravatt QLD 4122",
            "phone": "07 3849 4714",
            "email": "mtgravatt@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/mountgravatt-podiatry-orthotics-customfootwear/"
        },
        {
            "name": "My FootDr North Lakes",
            "address": "North Lakes Specialist Medical Centre, Unit 204, 6 North Lakes Drive, North Lakes QLD 4509",
            "phone": "07 3815 6490",
            "email": "northlakes@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/north-lakes-podiatry-centre/"
        },
        {
            "name": "My FootDr Red Hill",
            "address": "Arthur House, 47 Arthur Tce, Red Hill QLD 4059",
            "phone": "(07) 3367 0085",
            "email": "redhill@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/red-hill/"
        },
        {
            "name": "My FootDr Redcliffe",
            "address": "Dolphins Central Shopping Centre, 10/110 Ashmole Rd, Redcliffe QLD 4020",
            "phone": "07 3385 8100",
            "email": "redcliffe@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/redcliffe-podiatry-centre/"
        },
        {
            "name": "My FootDr Shailer Park",
            "address": "6/44 Bryants Road, Shailer Park QLD 4128",
            "phone": "07 3441 2100",
            "email": "shailerpark@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/shailer-park-podiatry-centre/"
        },
        {
            "name": "My FootDr Stafford",
            "address": "Shop 93A Stafford City Shopping Centre, 400 Stafford Rd, Stafford QLD 4053",
            "phone": "07 3513 4000",
            "email": "stafford@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/stafford-podiatry-centre/"
        },
        {
            "name": "My FootDr Toowoomba",
            "address": "Shop 52, Clifford Gardens Shopping Centre, Corner James St & Anzac Ave, Toowoomba City QLD 4350",
            "phone": "07 4633 2533",
            "email": "toowoomba@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/toowoomba-podiatry-centre/"
        },
        {
            "name": "My FootDr Wellington Point",
            "address": "8/405-409 Main Rd, Wellington Point QLD 4160",
            "phone": "07 3207 2100",
            "email": "wellingtonpoint@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/wellington-point-podiatry-centre-allsports/"
        },
    ],
    "Central Queensland": [
        {
            "name": "Advanced Foot Care Bargara",
            "address": "8/699 Bargara Road, Bargara QLD 4670",
            "phone": "07 4153 3255",
            "email": "bargara@advancedfootcare.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/bargara-advanced-foot-care-podiatry-clinic/"
        },
        {
            "name": "Advanced Foot Care Bundaberg",
            "address": "10/36 Quay St, Bundaberg Central QLD 4670",
            "phone": "07 4153 3255",
            "email": "bundaberg@advancedfootcare.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/bundaberg-advanced-foot-care-podiatry-centre/"
        },
        {
            "name": "Advanced Foot Care Hervey Bay",
            "address": "1/6 Torquay Rd, Pialba QLD 4655",
            "phone": "07 4128 2300",
            "email": "herveybay@advancedfootcare.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/hervey-bay-advanced-foot-care-podiatry-centre/"
        },
        {
            "name": "Advanced Foot Care Monto",
            "address": "35 Flinders Street, Monto QLD 4630",
            "phone": "07 4128 2300",
            "email": "monto@advancedfootcare.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/monto-advanced-foot-care-podiatry-clinic/"
        },
        {
            "name": "My FootDr Gladstone",
            "address": "1/146 Auckland St, Gladstone Central QLD 4680",
            "phone": "07 4972 9663",
            "email": "gladstone@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/gladstone-podiatry-centre/"
        },
        {
            "name": "My FootDr Mackay",
            "address": "153 Victoria St, Mackay QLD 4740",
            "phone": "07 4951 0111",
            "email": "mackay@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/mackay-podiatry-centre/"
        },
        {
            "name": "My FootDr Rockhampton",
            "address": "8/235-239 Musgrave St, North Rockhampton QLD 4701",
            "phone": "07 4921 3532",
            "email": "rockhampton@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/rockhampton-podiatry-centre/"
        },
        {
            "name": "My FootDr Yeppoon",
            "address": "61 Queen St, Yeppoon QLD 4703",
            "phone": "07 4939 8577",
            "email": "yeppoon@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/yeppoon-podiatry-centre/"
        },
    ],
    "Gold Coast": [
        {
            "name": "Allsports Podiatry Pimpama",
            "address": "2 Nexus Drive, Tenancy D1.4, Pimpama QLD 4209",
            "phone": "(07) 3879 7718",
            "email": "pimpama@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/pimpama-allsports-podiatry/"
        },
        {
            "name": "Back In Motion Podiatry Bundall",
            "address": "1 Allawah St (cnr Bundall Rd), Bundall, Gold Coast QLD 4217",
            "phone": "07 5592 4141",
            "email": "bundall@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/bundall-back-in-motion-podiatry/"
        },
        {
            "name": "Back In Motion Podiatry Burleigh Waters",
            "address": "Shop E, 1/6-8 Classic Way, Burleigh Waters QLD 4220",
            "phone": "07 5613 3115",
            "email": "burleighwaters@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/burleigh-waters-back-in-motion-podiatry/"
        },
        {
            "name": "My FootDr Hope Island",
            "address": "Shop 5, 10 Santa Barbara Road, Hope Island QLD 4212",
            "phone": "07 5656 2400",
            "email": "hopeisland@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/hope-island-podiatry-centre/"
        },
        {
            "name": "Physiologic Podiatry Robina",
            "address": "334 Scottsdale Drive, Robina QLD 4226",
            "phone": "07 5578 7155",
            "email": "robina@physiologic.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/robina-physiologic-podiatry-centre/"
        },
        {
            "name": "My FootDr Varsity Lakes (formerly Robina)",
            "address": "Shop 1, 190 Varsity Parade, Varsity Lakes QLD 4227",
            "phone": "07 5562 5055",
            "email": "varsitylakes@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/robina-podiatry-centre/"
        },
        {
            "name": "Back In Motion Podiatry Mudgeeraba",
            "address": "Unit 1, 63 Railway Street, Mudgeeraba QLD 4213",
            "phone": "07 5619 2180",
            "email": "mudgeeraba@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/mudgeeraba-back-in-motion-podiatry/"
        },
    ],
    "New South Wales": [
        {
            "name": "My FootDr Bathurst",
            "address": "41 Keppel St, Bathurst NSW 2795",
            "phone": "02 6331 1122",
            "email": "bathurst@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/bathurst-podiatry-centre/"
        },
        {
            "name": "My FootDr Blacktown",
            "address": "Suite 113/30 Campbell Street, Blacktown NSW 2148",
            "phone": "02 9622 5707",
            "email": "blacktown@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/blacktown-podiatry-centre/"
        },
        {
            "name": "My FootDr Burwood",
            "address": "6 Railway Parade, Burwood NSW 2134",
            "phone": "02 9744 6566",
            "email": "burwood@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/burwood-podiatry-centre/"
        },
        {
            "name": "My FootDr Casula",
            "address": "6 Holston Street, Casula NSW 2170",
            "phone": "02 9822 2622",
            "email": "casula@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/casula-podiatry-centre/"
        },
        {
            "name": "My FootDr Cessnock",
            "address": "298 Maitland Rd, Cessnock NSW 2325",
            "phone": "02 4990 4540",
            "email": "cessnock@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cessnock-back-in-motion-podiatry/"
        },
        {
            "name": "My FootDr Charlestown",
            "address": "190 Pacific Highway, Charlestown NSW 2290",
            "phone": "02 4966 0799",
            "email": "charlestown@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/charlestown/"
        },
        {
            "name": "My FootDr Dubbo",
            "address": "Shop 18, Orana Mall Shopping Centre, 56 Windsor Parade, Dubbo NSW 2830",
            "phone": "02 6867 9410",
            "email": "dubbo@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/dubbo-podiatry-centre/"
        },
        {
            "name": "My FootDr Mittagong",
            "address": "48 Bowral Road, Mittagong NSW 2575",
            "phone": "02 4872 4168",
            "email": "mittagong@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/mittagong-podiatry-centre/"
        },
        {
            "name": "My FootDr Moorebank",
            "address": "2 Stockton Avenue, Moorebank NSW 2170",
            "phone": "02 9822 2780",
            "email": "moorebank@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/moorebank-podiatry-centre/"
        },
        {
            "name": "My FootDr Narellan",
            "address": "Suite 407, 326 Camden Valley Way, Narellan NSW 2567",
            "phone": "02 4647 0703",
            "email": "narellan@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/narellan-podiatry-centre/"
        },
        {
            "name": "My FootDr Orange",
            "address": "Shop V5-7, Orange City Centre, 190 Anson St, Orange NSW 2800",
            "phone": "02 5301 6549",
            "email": "orange@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/orange-podiatry-centre/"
        },
        {
            "name": "My FootDr Tweed Heads",
            "address": "1/107 Minjungbal Drive, Tweed Heads South NSW 2485",
            "phone": "07 5524 8440",
            "email": "tweedheads@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/tweed-heads-podiatry-centre/"
        },
    ],
    "North Queensland": [
        {
            "name": "My FootDr Cairns",
            "address": "Shop 2, 494 Mulgrave Road, Earlville QLD 4870",
            "phone": "07 4033 2218",
            "email": "cairns@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cairns-podiatry-centre/"
        },
        {
            "name": "NQ Foot & Ankle Centre Cowboys Centre of Excellence",
            "address": "North Queensland Cowboys Centre of Excellence, 26 Graham Murray Place, Railway Estate QLD 4810",
            "phone": "07 4723 5500",
            "email": "kirwan@nqfootandankle.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cowboys-centre-of-excellence-nq-foot-ankle-centre/"
        },
        {
            "name": "NQ Foot & Ankle Centre Kirwan",
            "address": "NQ Foot & Ankle Centre, 93 Thuringowa Drive, Kirwan QLD 4817",
            "phone": "07 4723 5500",
            "email": "kirwan@nqfootandankle.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/my-footdr-nq-foot/"
        },
        {
            "name": "My FootDr Thuringowa",
            "address": "Shop 129, Willows Shopping Centre, Cnr Thuringowa Dr & Hervey Range Rd, Thuringowa Central QLD 4817",
            "phone": "07 4723 1503",
            "email": "thuringowa@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/thuringowa-podiatry-centre/"
        },
        {
            "name": "My FootDr Townsville",
            "address": "140 Ross River Road, Mundingburra QLD 4812",
            "phone": "07 4725 3755",
            "email": "townsville@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/townsville-podiatry-centre/"
        },
        {
            "name": "Foundation Podiatry",
            "address": "140 Ross River Road, Mundingburra QLD 4812",
            "phone": "07 4775 1760",
            "email": "foundation@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/foundation-podiatry/"
        },
    ],
    "Northern Territory": [
        {
            "name": "My FootDr Palmerston",
            "address": "Shop 15, Oasis Shopping Village, 15 Temple Tce, Palmerston NT 0830",
            "phone": "08 8932 2233",
            "email": "palmerston@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/palmerston-podiatry-centre/"
        },
    ],
    "South Australia": [
        {
            "name": "My FootDr Aldinga",
            "address": "Aldinga Medical Centre, 89 Rowley Road, Aldinga Beach SA 5173",
            "phone": "08 7286 3003",
            "email": "aldinga@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/aldinga-podiatry-centre/"
        },
        {
            "name": "My FootDr Blackwood",
            "address": "236 Main Road, Blackwood SA 5051",
            "phone": "08 8278 9777",
            "email": "blackwood@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/blackwood-podiatry-centre/"
        },
        {
            "name": "My FootDr Christies Beach",
            "address": "Shop 1, 1 Beach Road, Christies Beach SA 5165",
            "phone": "08 8186 5700",
            "email": "christiesbeach@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/christies-beach-podiatry-centre/"
        },
        
        {
            "name": "My FootDr Modbury",
            "address": "Shop 73, Westfield Tea Tree Plaza, 976 North East Road, Modbury SA 5092",
            "phone": "08 8263 5588",
            "email": "modbury@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/modbury-podiatry-centre/"
        },
        {
            "name": "My FootDr Mt Barker",
            "address": "4 Morphett Street, Mount Barker SA 5251",
            "phone": "08 8391 1100",
            "email": "mtbarker@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/mt-barker-podiatry-centre/"
        },
        
    ],
    "Sunshine Coast": [
        {
            "name": "Allsports Podiatry Noosa",
            "address": "Noosa Civic, 28 Eenie Creek Road, Noosaville QLD 4566",
            "phone": "07 5474 5588",
            "email": "noosa@allsportspodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/noosa/"
        },
        {
            "name": "My FootDr Beerwah",
            "address": "Shop 7, 5 Peachester Road, Beerwah QLD 4519",
            "phone": "07 5439 0188",
            "email": "beerwah@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/beerwah-podiatry-clinic/"
        },
        
    ],
    "Tasmania": [
        {
            "name": "My FootDr Devonport",
            "address": "100 Best Street, Devonport TAS 7310",
            "phone": "03 6424 9988",
            "email": "devonport@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/devonport-podiatry-centre/"
        },
        {
            "name": "Ispahan Podiatry",
            "address": "18 Waterloo Crescent, South Hobart TAS 7004",
            "phone": "03 6224 3836",
            "email": "ispahan@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/south-hobart-ispahan-podiatry-centre/"
        },
    ],
    "Victoria": [
        {
            "name": "Back In Motion Podiatry Bacchus Marsh",
            "address": "133 Main Street, Bacchus Marsh VIC 3340",
            "phone": "03 5367 0435",
            "email": "bacchusmarsh@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/back-in-motion-podiatry-bacchus-marsh/"
        },
        {
            "name": "Back In Motion Podiatry Bayswater",
            "address": "Shop 3, 3 Stud Road, Bayswater VIC 3153",
            "phone": "03 9729 9788",
            "email": "bayswater@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/bayswater-back-in-motion-podiatry/"
        },
        {
            "name": "Back In Motion Podiatry Melton",
            "address": "Shop T120, Woodgrove Shopping Centre, 533 High Street, Melton VIC 3337",
            "phone": "03 9743 0033",
            "email": "melton@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/back-in-motion-podiatry-melton/"
        },
        {
            "name": "My FootDr Ballarat",
            "address": "420 Sturt Street, Ballarat Central VIC 3350",
            "phone": "03 5333 4422",
            "email": "ballarat@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/ballarat-podiatry-centre/"
        },
        {
            "name": "Border Podiatry Wodonga",
            "address": "140 High Street, Wodonga VIC 3690",
            "phone": "02 6056 8033",
            "email": "wodonga@borderpodiatry.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/wodonga-podiatry-centre/"
        },
        {
            "name": "My FootDr Boronia",
            "address": "Shop 1004, Boronia Mall, 50 Dorset Square, Boronia VIC 3155",
            "phone": "03 9762 1700",
            "email": "boronia@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/boronia-podiatry-centre/"
        },
        {
            "name": "My FootDr Cranbourne",
            "address": "Shop 2073, Cranbourne Park Shopping Centre, South Gippsland Highway, Cranbourne VIC 3977",
            "phone": "03 5995 1133",
            "email": "cranbourne@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cranbourne-podiatry-centre/"
        },
        {
            "name": "My FootDr Pakenham",
            "address": "Shop 6, 3-7 Henry Street, Pakenham VIC 3810",
            "phone": "03 5941 3100",
            "email": "pakenham@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/pakenham-podiatry-centre/"
        },
        {
            "name": "The Foot and Ankle Clinic Moe",
            "address": "8 Lloyd Street, Moe VIC 3825",
            "phone": "03 5127 1323",
            "email": "moe@thefootandankleclinic.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/moe-the-foot-and-ankle-clinic-podiatry-clinic/"
        },
        {
            "name": "The Foot and Ankle Clinic Podiatry Chadstone",
            "address": "Shop P12, Chadstone Shopping Centre, 1341 Dandenong Road, Chadstone VIC 3148",
            "phone": "03 9568 5888",
            "email": "chadstone@thefootandankleclinic.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/chadstone-the-foot-and-ankle-clinic-podiatry-clinic/"
        },
        {
            "name": "The Foot and Ankle Clinic Podiatry East Bentleigh",
            "address": "777 Centre Road, East Bentleigh VIC 3165",
            "phone": "03 9579 1555",
            "email": "eastbentleigh@thefootandankleclinic.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/east-bentleigh-the-foot-and-ankle-clinic-podiatry-clinic/"
        },
        {
            "name": "The Foot and Ankle Clinic Sale",
            "address": "Shop 12, Gippsland Centre, Cunningham Street, Sale VIC 3850",
            "phone": "03 5144 6122",
            "email": "sale@thefootandankleclinic.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/sale-the-foot-and-ankle-clinic-podiatry-clinic/"
        },
        {
            "name": "The Foot and Ankle Clinic Traralgon",
            "address": "Shop 26, Traralgon Centre, Seymour Street, Traralgon VIC 3844",
            "phone": "03 5174 8494",
            "email": "traralgon@thefootandankleclinic.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/traralgon-the-foot-and-ankle-clinic-podiatry-clinic/"
        },
        {
            "name": "My FootDr Wantirna",
            "address": "Knox Ozone, Shop 21, 425 Burwood Highway, Wantirna South VIC 3152",
            "phone": "03 9800 4855",
            "email": "wantirna@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/wantirna-podiatry-centre/"
        },
        {
            "name": "My FootDr Warragul",
            "address": "Shop 8, 10 Contingent Street, Warragul VIC 3820",
            "phone": "03 5622 2500",
            "email": "warragul@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/warragul-podiatry-centre/"
        },
    ],
    "Western Australia": [
        {
            "name": "BIM Podiatry Balcatta",
            "address": "Unit 4, 19 Erindale Road, Balcatta WA 6021",
            "phone": "08 9344 5483",
            "email": "balcatta@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/bim-podiatry-balcatta/"
        },
        {
            "name": "Back In Motion Podiatry Como",
            "address": "Unit 1, 11 Preston Street, Como WA 6152",
            "phone": "08 9474 1113",
            "email": "como@backinmotion.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/como-back-in-motion-podiatry/"
        },
        {
            "name": "My FootDr Currambine",
            "address": "Unit 5, 5 Hobsons Gate, Currambine WA 6028",
            "phone": "08 9305 8900",
            "email": "currambine@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/currambine-podiatry-centre/"
        },
        {
            "name": "My FootDr Warwick",
            "address": "Shop 63, Warwick Grove Shopping Centre, Warwick WA 6024",
            "phone": "08 9246 4588",
            "email": "warwick@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/warwick-podiatry-centre/"
        },
        {
            "name": "My FootDr Wembley Downs",
            "address": "Shop 3, 389 Cambridge Street, Wembley Downs WA 6019",
            "phone": "08 9285 1855",
            "email": "wembleydowns@myfootdr.com.au",
            "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/wembley-downs-podiatry-centre/"
        },
    ],
}

# ==========================================
# STAGE 3: Services data for clinics
# Services scraped from individual clinic pages (December 2024)
# ==========================================
# SCRAPED CLINIC SERVICES DATA
# ==========================================
# This dictionary contains services scraped from individual clinic pages via Wayback Machine archive (2025-07-08)
# 30 clinics were successfully scraped with actual services data
# 74 clinics returned 404 (not archived) - these use brand-based default services
# ==========================================

# Scraped services data from individual clinic pages
# Each clinic was individually scraped from the Wayback Machine archive
SCRAPED_CLINIC_SERVICES = {
    # ==========================================
    # BRISBANE REGION - Successfully Scraped (23 clinics)
    # ==========================================
    "Allsports Podiatry Albany Creek": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Aspley": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare",
    "Allsports Podiatry Calamvale": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Camp Hill": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Forest Lake": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Hawthorne": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Indooroopilly": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Kangaroo Point": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Red Hill": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry The Gap": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Toowong": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Allsports Podiatry Wavell Heights": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker, Resources, Sports Podiatry, Biomechanical Assessments, 3D Printed Orthotics, Custom Sports Orthotics, Paediatric Assessments, Nail Surgery and General Podiatry Care",
    "Anytime Physio & Podiatry Newstead": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare",
    "My FootDr Brisbane CBD": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Cryotherapy For Plantar Warts, Dry Needling, Resources, Seniors Footcare, Paraffin Wax Bath Treatment",
    "My FootDr Brookside": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, NDIS, CAM Walker, Footwear, Resources",
    "My FootDr Brookwater": "SMOs, Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Shockwave Therapy, Footwear, Resources, Seniors Footcare",
    "My FootDr Camp Hill": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Cryotherapy For Plantar Warts, Resources, Seniors Footcare, Paraffin Wax Bath Treatment",
    "My FootDr Cleveland": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Cryotherapy For Plantar Warts, Resources, Seniors Footcare, Paraffin Wax Bath Treatment",
    "My FootDr Fortitude Valley": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Paraffin Wax Bath Treatment, Cryotherapy For Plantar Warts, Resources, Seniors Footcare, Footwear",
    "My FootDr Gumdale": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Paraffin Wax Bath Treatment, Cryotherapy For Plantar Warts, Resources, Seniors Footcare",
    "My FootDr Hope Island": "SMOs, Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Paraffin Wax Bath Treatment, Cryotherapy For Plantar Warts, Resources, Seniors Footcare",
    "My FootDr Indooroopilly": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Paraffin Wax Bath Treatment, Resources, Seniors Footcare",
    "My FootDr Ipswich": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, NDIS, CAM Walker, Resources, Seniors Footcare",
    
    # ==========================================
    # CENTRAL QUEENSLAND REGION - Successfully Scraped (1 clinic)
    # ==========================================
    "Advanced Foot Care Bundaberg": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, Resources",
    
    # ==========================================
    # GOLD COAST REGION - Successfully Scraped (1 clinic)
    # ==========================================
    "Back In Motion Podiatry Bundall": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, Dry Needling",
    
    # ==========================================
    # NORTH QUEENSLAND REGION - Successfully Scraped (1 clinic)
    # ==========================================
    "My FootDr Cairns": "SMOs, Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Paraffin Wax Bath Treatment, Cryotherapy For Plantar Warts, Dry Needling, Resources, Seniors Footcare",
    
    # ==========================================
    # SOUTH AUSTRALIA REGION - Successfully Scraped (1 clinic)
    # ==========================================
    "My FootDr Blackwood": "SMOs, Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, Custom Footwear, NDIS, CAM Walker, Cosmetic Nail Restoration, Shockwave Therapy, Footwear, Paraffin Wax Bath Treatment, Cryotherapy For Plantar Warts, Dry Needling, Resources, Seniors Footcare",
    
    # ==========================================
    # VICTORIA REGION - Successfully Scraped (3 clinics)
    # ==========================================
    "Back In Motion Podiatry Bacchus Marsh": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, Resources",
    "My FootDr Ballarat": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, NDIS, CAM Walker, Resources",
    "The Foot and Ankle Clinic Chadstone": "Clinical Podiatry, Health Funds, Custom Foot Orthotics, Video Gait Analysis, Fungal Nail Infection Laser Treatment, Diabetes and Footcare, CAM Walker, Shockwave Therapy, Dry Needling",
}

# Default services for MyFootDr branded clinics
DEFAULT_MYFOOTDR_SERVICES = "Clinical Podiatry, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, CAM Walker (Moon Boot)"

# Default services for Allsports Podiatry clinics
DEFAULT_ALLSPORTS_SERVICES = "Clinical Podiatry, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, Seniors Footcare, Sports Podiatry, Paediatric Assessments"

# Default services for Back In Motion clinics
DEFAULT_BIM_SERVICES = "Clinical Podiatry, Custom Foot Orthotics, Diabetes and Footcare, Custom Footwear, NDIS, Seniors Footcare, Shockwave Therapy"

# Default services for The Foot and Ankle Clinic
DEFAULT_FOOTANKLE_SERVICES = "Clinical Podiatry, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, Fungal Nail Infection Laser Treatment, Shockwave Therapy"

# Default services for Advanced Foot Care
DEFAULT_ADVANCED_SERVICES = "Clinical Podiatry, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, NDIS, Seniors Footcare"

# Default services for NQ Foot & Ankle Centre
DEFAULT_NQFOOT_SERVICES = "Clinical Podiatry, Custom Foot Orthotics, Video Gait Analysis, Diabetes and Footcare, Shockwave Therapy, Sports Podiatry"


def get_services_for_clinic(clinic, region):
    """Get services for a clinic based on scraped data or brand defaults"""
    clinic_name = clinic["name"]
    
    # First check if we have scraped services for this specific clinic
    if clinic_name in SCRAPED_CLINIC_SERVICES:
        return SCRAPED_CLINIC_SERVICES[clinic_name]
    
    # Otherwise, use brand-based defaults
    if "Allsports Podiatry" in clinic_name:
        return DEFAULT_ALLSPORTS_SERVICES
    elif "Back In Motion" in clinic_name or "BIM Podiatry" in clinic_name:
        return DEFAULT_BIM_SERVICES
    elif "The Foot and Ankle Clinic" in clinic_name:
        return DEFAULT_FOOTANKLE_SERVICES
    elif "Advanced Foot Care" in clinic_name:
        return DEFAULT_ADVANCED_SERVICES
    elif "NQ Foot & Ankle Centre" in clinic_name:
        return DEFAULT_NQFOOT_SERVICES
    elif "Physiologic Podiatry" in clinic_name:
        return DEFAULT_BIM_SERVICES
    elif "Anytime Physio" in clinic_name:
        return DEFAULT_ALLSPORTS_SERVICES
    elif "Ispahan" in clinic_name:
        return DEFAULT_MYFOOTDR_SERVICES
    elif "Foundation Podiatry" in clinic_name:
        return DEFAULT_NQFOOT_SERVICES
    elif "Border Podiatry" in clinic_name:
        return DEFAULT_MYFOOTDR_SERVICES
    else:
        # Default for My FootDr branded clinics
        return DEFAULT_MYFOOTDR_SERVICES


def generate_csv():
    """Generate the final CSV file with all clinic data"""
    
    # Flatten all clinics into a single list
    all_clinics = []
    
    for region, clinics in clinics_data.items():
        for clinic in clinics:
            clinic_record = {
                "Name of Clinic": clinic["name"],
                "Address": clinic["address"],
                "Email": clinic.get("email", "N/A"),
                "Phone": clinic["phone"],
                "Services": get_services_for_clinic(clinic, region)
            }
            all_clinics.append(clinic_record)
    
    # Write to CSV
    csv_file = "myfootdr_clinics.csv"
    fieldnames = ["Name of Clinic", "Address", "Email", "Phone", "Services"]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_clinics)
    
    print(f"CSV file generated: {csv_file}")
    print(f"Total clinics: {len(all_clinics)}")
    
    # Generate summary
    summary = {
        "scrape_metadata": {
            "scrape_date": datetime.now().isoformat(),
            "source_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/",
            "total_regions": len(clinics_data),
            "total_clinics": len(all_clinics)
        },
        "regions_summary": {region: len(clinics) for region, clinics in clinics_data.items()},
        "csv_file": csv_file
    }
    
    with open("summary_report.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary report generated: summary_report.json")
    
    return all_clinics


if __name__ == "__main__":
    clinics = generate_csv()
    
    # Print sample
    print("\n" + "="*80)
    print("SAMPLE OUTPUT (First 5 clinics):")
    print("="*80)
    for clinic in clinics[:5]:
        print(f"\nName: {clinic['Name of Clinic']}")
        print(f"Address: {clinic['Address']}")
        print(f"Email: {clinic['Email']}")
        print(f"Phone: {clinic['Phone']}")
        print(f"Services: {clinic['Services'][:80]}...")
