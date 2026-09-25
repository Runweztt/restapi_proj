import xml.etree.ElementTree as ET

tree = ET.parse("modified_sms_v2.xml")
root = tree.getroot()

print("total records:", len(root))

seen_bodies = set()
count = 0
for sms in root:
    body = sms.attrib.get("body", "")
    key = body[:30]
    if key in seen_bodies:
        continue
    seen_bodies.add(key)
    print("---")
    print(body)
    count += 1
    if count >= 8:
        break