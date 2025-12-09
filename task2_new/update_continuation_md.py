from pathlib import Path
import json

f = Path('d:/Work/Mindrift/task2_new/CONTINUATION_PROMPT_FOR_LLM.md')
text = f.read_text(encoding='utf-8')
# compute current counts from main JSON
pj = Path('d:/Work/Mindrift/task2_new/data/clinic_service_2.json')
data = json.loads(pj.read_text(encoding='utf-8'))
regions = data['regions']
total = sum(len(r.get('clinics', {})) for r in regions.values())
scraped = sum(1 for r in regions.values() for c in r.get('clinics', {}).values() if c.get('scraped'))
remaining = total - scraped
percent = int((scraped * 100) // total) if total else 0

# Replace lines (being robust)
import re
text = re.sub(r"\*\*Currently Scraped:\*\* .*", f"**Currently Scraped:** {scraped} clinics ({percent}% complete)", text)
text = re.sub(r"\*\*Remaining:\*\* .*", f"**Remaining:** {remaining} clinics ({100-percent}% )", text)

f.write_text(text, encoding='utf-8')
print('Updated CONTINUATION_PROMPT_FOR_LLM.md')
