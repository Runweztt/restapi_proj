import json
import time

def load_transactions(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def linear_search(transactions, target_id):
    for t in transactions:
        if t["id"] == target_id:
            return t
    return None

def build_lookup(transactions):
    return {t["id"]: t for t in transactions}

def dict_search(lookup, target_id):
    return lookup.get(target_id)

if __name__ == "__main__":
    transactions = load_transactions("dsa/parsed_transactions.json")
    print("Total records:", len(transactions))

    lookup = build_lookup(transactions)

    test_ids = [1, 100, 400, 800, 1200, 1690]
    repeats = 2000

    for tid in test_ids:
        start = time.perf_counter()
        for _ in range(repeats):
            linear_search(transactions, tid)
        linear_time = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(repeats):
            dict_search(lookup, tid)
        dict_time = time.perf_counter() - start

        print(f"id={tid:5d}  linear={linear_time*1000:8.3f} ms  dict={dict_time*1000:8.3f} ms  "
              f"dict is {linear_time / dict_time:8.1f}x faster")