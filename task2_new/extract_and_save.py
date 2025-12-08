#!/usr/bin/env python3
"""
Extract services from markdown and save to JSON.
Paste the markdown response here, run the script.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

JSON_FILE = Path("data/clinic_service_2.json")

def extract_services_from_markdown(markdown: str) -> List[str]:
    """Extract services from markdown."""
    services = []
    
    services_match = re.search(
        r'##\s+Services?\s+Available\s*\n(.*?)(?=\n##\s|\Z)',
        markdown,
        re.IGNORECASE | re.DOTALL
    )
    
    if not services_match:
        return []
    
    services_section = services_match.group(0)
    service_lines = re.findall(r'^###\s+(.+?)(?:\n|$)', services_section, re.MULTILINE)
    
    for line in service_lines:
        service_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        service_name = service_name.strip()
        
        if service_name and len(service_name) > 3:
            services.append(service_name)
    
    return services

def save_clinic(region: str, clinic_name: str, services: List[str]) -> None:
    """Update JSON with scraped clinic services."""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if region in data and clinic_name in data[region]:
        data[region][clinic_name]['services'] = services
        data[region][clinic_name]['scraped'] = True
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ {clinic_name}: {len(services)} services saved")
        for i, svc in enumerate(services, 1):
            print(f"  {i}. {svc}")
    else:
        print(f"✗ ERROR: Could not find {clinic_name} in {region}")

# PASTE THE MARKDOWN HERE (use raw string to avoid escape sequence issues):
MARKDOWN = r"""Podiatrist Albany Creek, Orthotics, Diabetic Footcare | Allsports Podiatry

[![Wayback Machine](https://web-static.archive.org/_static/images/toolbar/wayback-toolbar-logo-200.png)](/web/ "Wayback Machine home page")

[34 captures](/web/20250517064322*/https://www.myfootdr.com.au/our-clinics/albany-creek-allsports-podiatry/ "See a list of every capture for this URL")

22 Jun 2020 - 27 Sep 2025

|     |     |     |
| --- | --- | --- |
| Apr | MAY | Jun |
|     | 17  |     |
| 2024 | 2025 | 2026 |

success

fail

[](# "Share via My Web Archive")[](https://archive.org/account/login.php "Sign In")[](https://help.archive.org/help/category/the-wayback-machine/ "Get some help using the Wayback Machine")[](#close "Close the toolbar")

[](/web/20250517064322/http://web.archive.org/screenshot/https://www.myfootdr.com.au/our-clinics/albany-creek-allsports-podiatry/ "screenshot")[](# "video")[](# "Share on Facebook")[](# "Share on Twitter")

[About this capture](#expand)

COLLECTED BY

Collection: [Common Crawl](https://archive.org/details/commoncrawl)

Web crawl data from Common Crawl.

TIMESTAMPS

![loading](https://web-static.archive.org/_static/images/loading.gif)

The Wayback Machine - https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-clinics/albany-creek-allsports-podiatry/

Welcome to

# [Allsports Podiatry Albany Creek](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-clinics/albany-creek-allsports-podiatry/)

j Closed

[Book online](javascript:HeartExp.Pages.Clinic.bookNow\(8930\))[Call 07 3264 5159](tel:0732645159)

Looking for a Brisbane podiatrist near you? Conveniently located in Albany Creek, the team continues to service its local community as well as the neighbouring suburbs of Eatons Hill, Bridgeman Downs, Brendale & Carseldine.

\* Yellow opening hours indicates special hours for particular dates this week.

**Monday**  
Closed

**Tuesday**  
7:30 am -  
5:30 pm

**Wednesday**  
7:30 am -  
11:30 am

**Thursday**  
7:30 am -  
4:00 pm

**Friday**  
Closed

**Saturday**  
Closed

**Sunday**  
Closed

![Allsports Podiatry Albany Creek](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/Allsports-pod-logo-600x324-1-300x162.png "Allsports Podiatry Albany Creek")[Book online](javascript:HeartExp.Pages.Clinic.bookNow\(8930\))[Call 07 3264 5159](tel:0732645159)

[V Get directions with Google Maps](https://web.archive.org/web/20250517064322/https://www.google.com/maps/dir/?api=1&destination=-27.3522546%2C152.9657954&destination_place_id=ChIJbfiYcZ39k2sR4RUr84hyGaw)

[i Albany Creek Leisure Centre  
Cnr Old Northern Rd & Explorer Drive  
Albany Creek QLD 4035](https://web.archive.org/web/20250517064322/https://maps.google.com/?cid=12401068981462177249 "View address in Google Maps...")

[v albanycreek@allsportspodiatry.com.au](https://web.archive.org/web/20250517064322/mailto:albanycreek@allsportspodiatry.com.au "Send an email to Allsports Podiatry Albany Creek")

U 07 3264 6644

## Services Available

![Clinical Podiatry](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/clinical-podiatry.jpg)

[November 12, 2015](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/clinical-podiatry/)

### [Clinical Podiatry](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/clinical-podiatry/)

Our centres provide the full scope of clinical podiatry including comprehensive foot assessments, various treatments and surgery.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/clinical-podiatry/)

![](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/MFD-health-funds-3-1000x667-1.jpg)

[February 1, 2022](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/health-funds/)

### [Health Funds](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/health-funds/)

At My FootDr we are passionate about providing all our patient's treatment options that lead to better health outcomes for not only themselves, but their families too. Being a preferred provider of a health fund means that our clinics may allow you access to exclusive benefits dependent on your level of cover.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/health-funds/)

![Custom Foot Orthotics](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/custom-foot-orthotics-1.jpg)

[November 12, 2015](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/custom-foot-orthotics/)

### [Custom Foot Orthotics](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/custom-foot-orthotics/)

Our custom foot orthotics are manufactured with precision from digital foot scans and are typically available on the same day.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/custom-foot-orthotics/)

![Video Gait Analysis](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/video-gait-analysis.jpg)

[November 12, 2015](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/video-gait-analysis/)

### [Video Gait Analysis](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/video-gait-analysis/)

We use this advanced form of motion analysis to assists us in diagnosing complex motion related pathology of the foot, ankle, knee hip and lower back.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/video-gait-analysis/)

![Diabetic Foot Care](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/diabetic-footcare.jpg)

[November 12, 2015](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/diabetes-and-footcare/)

### [Diabetes and Footcare](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/diabetes-and-footcare/)

Regular podiatric care plays an integral role in the prevention of diabetic foot complications. Our My FootDr podiatrists are trained in diabetic foot care to make sure our patients have the best outcome.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/diabetes-and-footcare/)

![National Disability Insurance Scheme](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/NDIS.jpg)

[September 28, 2018](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/national-disability-insurance-scheme-ndis/)

### [National Disability Insurance Scheme (NDIS)](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/national-disability-insurance-scheme-ndis/)

My FootDr is a proud supporter of the NDIS and are an innovative, nationally registered provider of podiatry services to NDIS participants across Australia.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/national-disability-insurance-scheme-ndis/)

![Aged Footcare](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/aged-footcare.jpg)

[September 12, 2018](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/seniors-footcare/)

### [Seniors Footcare](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/seniors-footcare/)

With Australia's advancing aged population, it has never been more important to highlight foot care in the elderly. My FootDr podiatrists can prevent many complications with early diagnosis and treatment.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/seniors-footcare/)

![Happy family walking on beach](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/resources.jpg)

[June 21, 2016](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/resources/)

### [Resources](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/resources/)

Useful resources for doctors including our Referral Form.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/resources/)

#### [Home](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/) [Our Clinics](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-clinics/)

# [Allsports Podiatry Albany Creek](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-clinics/albany-creek-allsports-podiatry/)

![Allsports Podiatry Albany Creek](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/Albany-Creek-Allsports-3-copy-scaled.jpg)

Looking for an Albany Creek podiatrist near you? The friendly team at Albany Creek is here to provide the local community with a range of quality foot-care services for all patients, including neighbouring suburbs of Brendale, Eatons Hill, Bunya & Aspley. Call us today!

Welcome to Allsports Podiatry Albany Creek! Located on the Cnr of Old Northern Rd and Explorer Drive, Our Allsports Podiatry Albany Creek clinic is conveniently found inside the [Allsports Physiotherapy & Sports Medicine Albany Creek](https://web.archive.org/web/20250517064322/https://www.allsportsphysio.com.au/our-clinics/albany-creek/) clinic. The Allsports Podiatry group is a passionate and enthusiastic team of professionals, who are committed to providing the highest quality of care for their patients. Our friendly podiatry team can assist with:

*   [Sports podiatry](https://web.archive.org/web/20250517064322/https://www.allsportspodiatry.com.au/our-services/sports-podiatry/)
*   [Digital Gait analysis](https://web.archive.org/web/20250517064322/https://www.allsportspodiatry.com.au/our-services/digital-gait-analysis/)
*   [Custom Orthotics](https://web.archive.org/web/20250517064322/https://www.allsportspodiatry.com.au/our-services/orthotics/)
*   [Paediatric assessments](https://web.archive.org/web/20250517064322/https://www.allsportspodiatry.com.au/our-services/paediatric-assessments/)
*   [Footwear assessments](https://web.archive.org/web/20250517064322/https://www.allsportspodiatry.com.au/our-services/footwear-assessments/)
*   [General podiatry care](https://web.archive.org/web/20250517064322/https://www.allsportspodiatry.com.au/our-services/general-podiatry-care/)

Allsports Podiatry was founded in 2003, and our team have continued to provide excellence in podiatric care for people of all ages and lifestyles. Our Albany Creek staff ensure to utilise the latest assessment techniques to better understand the foot and ankle pain of our patients and then apply this knowledge to achieve the best treatment outcomes. For any questions make sure to contact us today or feel free to book online!

## Local News

[May 22, 2023](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2023/05/what-are-plantar-warts-and-how-are-they-caused/)

### [What are plantar warts and how are they caused?](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2023/05/what-are-plantar-warts-and-how-are-they-caused/)

Having warts on the bottom of the feet that won't go away is a frustrating, ongoing problem that can last months or even years. They can make walking unpleasant but also painful. While many people are told that they should just wait for the wart to go away on its own, or to use padding in the meantime that only ever provides a little temporary relief, the reality is that when left untreated, warts can stick around for a very long time.  
What are plantar warts and how are they caused?  
Plantar warts are small, rough, round growths that are medically known as verrucae and present on the bottom of the foot. They're caused by a virus called the Human Papilloma Virus (HPV) in the outer skin layer and are often contracted in childhood. Once you've contracted the virus, you'll always have it in your system, so plantar warts may pop up spontaneously throughout your lifetime.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2023/05/what-are-plantar-warts-and-how-are-they-caused/)

![](https://web.archive.org/web/20250517064322im_/https://www.myfootdr.com.au/wp-content/uploads/MicrosoftTeams-image-8.jpg)

[May 9, 2023](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2023/05/do-you-have-toenail-pain/)

### [Do You Have Toenail Pain?](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2023/05/do-you-have-toenail-pain/)

Ingrown toenails on a woman's foot, pain in the big toe closeup

Ingrown toenails, also known as onychocryptosis, are a common and painful complaint. A true ingrown toenail is when a spike or edge of nail pierces the skin at the nail edge. This is known as the sulcus and can cause inflammation and even lead to infection.   
There are a variety of factors that can cause ingrown toenails. The most common cause is due to improper cutting of your toenail and leaving a spike of nail in the sulcus. It can also be a result of a curved nail, known as an involuted nail, from external pressure.   
If you are experiencing pain, redness, and swelling around your toenail, it may be time to consider seeing one of our podiatrists. With over 30 years of combined experience in treating foot and ankle conditions, we have successfully treated many clinics of ingrown toenails.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2023/05/do-you-have-toenail-pain/)

[April 28, 2021](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2021/04/preventing-falls-lands-on-foot-health/)

### [Preventing Falls Lands On Foot Health](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2021/04/preventing-falls-lands-on-foot-health/)

Approximately 200,000 Australians are hospitalised every year as a result of having a fall. Bone fractures are the most common type of injury resulting from a fall. While falls are most common in those aged over 65, young males aged 5-24 years are also particularly prone to falls.

[Read more »](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/2021/04/preventing-falls-lands-on-foot-health/)

[Book an appointment online](javascript:onlineBooking\(\)) or call us on [1800 366 837](tel:1800366837)."""

if __name__ == "__main__":
    services = extract_services_from_markdown(MARKDOWN)
    print(f"\nExtracted {len(services)} services:")
    for i, svc in enumerate(services, 1):
        print(f"  {i}. {svc}")
    
    print("\nSaving to JSON...")
    save_clinic("Brisbane", "Allsports Podiatry Albany Creek", services)
