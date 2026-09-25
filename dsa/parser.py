import xml.etree.ElementTree as ET
import re
import json

def clean_amount(s):
    return float(s.replace(",", ""))

def parse_record(sms_id, attrib):
    body = attrib.get("body", "")
    timestamp = attrib.get("readable_date", "")

    record = {
        "id": sms_id,
        "type": "other",
        "amount": None,
        "sender": None,
        "receiver": None,
        "transaction_id": None,
        "fee": None,
        "balance": None,
        "timestamp": timestamp,
        "raw_body": body
    }

    m = re.search(
        r"You have received ([\d,]+) RWF from (.+?) \([\*\d]+\).*?Financial Transaction Id: (\d+)",
        body
    )
    if m:
        record["type"] = "received"
        record["amount"] = clean_amount(m.group(1))
        record["sender"] = m.group(2).strip()
        record["transaction_id"] = m.group(3)
        return record

    m = re.search(
        r"(?:TxId:?\s?(\d+)\.?\*?S?\*?\s?)?Your payment of ([\d,]+) RWF to (Airtime|.+?) (?:\d+ )?has been completed at ([\d\- :]+)\. .*?Fee was:? ?([\d,]+) RWF",
        body
    )
    if m:
        record["type"] = "airtime" if "Airtime" in m.group(3) else "payment"
        record["transaction_id"] = m.group(1)
        record["amount"] = clean_amount(m.group(2))
        record["receiver"] = m.group(3).strip()
        record["fee"] = clean_amount(m.group(5))
        return record

    m = re.search(
        r"A bank deposit of ([\d,]+) RWF has been added to your mobile money account.*?NEW BALANCE :([\d,]+) RWF",
        body
    )
    if m:
        record["type"] = "bank_deposit"
        record["amount"] = clean_amount(m.group(1))
        record["balance"] = clean_amount(m.group(2))
        return record

    m = re.search(
        r"DEPOSIT RWF ([\d,]+) Receiver: (\d+)",
        body
    )
    if m:
        record["type"] = "bank_deposit"
        record["amount"] = clean_amount(m.group(1))
        record["receiver"] = m.group(2).strip()
        return record

    m = re.search(
        r"([\d,]+) RWF transferred to (.+?) \((\d+)\) from (\d+) at ([\d\- :]+) \. Fee was:? ([\d,]+) RWF\. New balance: ([\d,]+) RWF",
        body
    )
    if m:
        record["type"] = "transfer"
        record["amount"] = clean_amount(m.group(1))
        record["receiver"] = m.group(2).strip()
        record["fee"] = clean_amount(m.group(6))
        record["balance"] = clean_amount(m.group(7))
        return record

    m = re.search(
        r"You have transferred ([\d,]+) RWF to (.+?) \((\d+)\) from your mobile money account.*?Financial Transaction Id: (\d+)",
        body
    )
    if m:
        record["type"] = "transfer"
        record["amount"] = clean_amount(m.group(1))
        record["receiver"] = m.group(2).strip()
        record["transaction_id"] = m.group(4)
        return record

    m = re.search(
        r"A transaction of ([\d,]+) RWF by (.+?)\s+on your MOMO account was successfully completed.*?"
        r"new balance:([\d,]+) RWF\. Fee was ([\d,]+) RWF\. Financial Transaction Id: (\d+)",
        body
    )
    if m:
        record["type"] = "merchant_payment"
        record["amount"] = clean_amount(m.group(1))
        record["receiver"] = m.group(2).strip()
        record["balance"] = clean_amount(m.group(3))
        record["fee"] = clean_amount(m.group(4))
        record["transaction_id"] = m.group(5)
        return record

    m = re.search(
        r"You (.+?) \([\*\d]+\) have via agent: (.+?) \((\d+)\), withdrawn ([\d,]+) RWF.*?"
        r"new balance: ([\d,]+) RWF\. Fee paid: ([\d,]+) RWF.*?Financial Transaction Id: (\d+)",
        body
    )
    if m:
        record["type"] = "withdrawal"
        record["sender"] = m.group(1).strip()
        record["receiver"] = m.group(2).strip()
        record["amount"] = clean_amount(m.group(4))
        record["balance"] = clean_amount(m.group(5))
        record["fee"] = clean_amount(m.group(6))
        record["transaction_id"] = m.group(7)
        return record

    m = re.search(r"Umaze kugura ([\d,]+)\s*(?:Rwf|FRW)", body, re.IGNORECASE)
    if m:
        record["type"] = "bundle_purchase"
        record["amount"] = clean_amount(m.group(1))
        return record

    m = re.search(
        r"A reversal has been initiated for your transaction to (.+?) \((\d+)\) with ([\d,]+) RWF",
        body
    )
    if m:
        record["type"] = "reversal"
        record["receiver"] = m.group(1).strip()
        record["amount"] = clean_amount(m.group(3))
        return record

    m = re.search(
        r"Your transaction to (.+?) \((\d+)\) with ([\d,]+) RWF has been reversed at ([\d\- :]+)\. Your new balance is ([\d,]+) RWF",
        body
    )
    if m:
        record["type"] = "reversal"
        record["receiver"] = m.group(1).strip()
        record["amount"] = clean_amount(m.group(3))
        record["balance"] = clean_amount(m.group(5))
        return record

    m = re.search(
        r"the transaction with amount ([\d,]+) RWF for (.+?) with message:.*?failed at ([\d\- :]+)",
        body
    )
    if m:
        record["type"] = "failed"
        record["amount"] = clean_amount(m.group(1))
        record["receiver"] = m.group(2).strip()
        return record

    m = re.search(
        r"Your payment of ([\d,]+) RWF to (.+?) with token\s*has failed at ([\d\- :]+)",
        body
    )
    if m:
        record["type"] = "failed"
        record["amount"] = clean_amount(m.group(1))
        record["receiver"] = m.group(2).strip()
        return record

    if "one-time password" in body:
        record["type"] = "non_transaction"
        return record

    return record

def parse_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    transactions = []
    for i, sms in enumerate(root, start=1):
        transactions.append(parse_record(i, sms.attrib))
    return transactions

if __name__ == "__main__":
    transactions = parse_xml("modified_sms_v2.xml")

    counts = {}
    for t in transactions:
        counts[t["type"]] = counts.get(t["type"], 0) + 1
    print("Type breakdown:", counts)

    print("\nSample 'other' bodies:")
    shown = 0
    for t in transactions:
        if t["type"] == "other":
            print("---")
            print(t["raw_body"])
            shown += 1
        if shown >= 10:
            break

    with open("dsa/parsed_transactions.json", "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)

    print("\nSaved", len(transactions), "records to dsa/parsed_transactions.json")