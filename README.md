\# MoMo SMS REST API



Team assignment: parse mobile money SMS records, serve them through a REST API secured with

Basic Auth, and compare linear search against dictionary lookup.



\## Data source



The raw file is `modified\_sms\_v2.xml`, an SMS backup export. It is \*\*not\*\* a clean transactions

table. Each record is one `<sms>` tag with attributes (`body`, `date`, `readable\_date`, etc),

and the actual transaction details (amount, sender, fee, transaction ID) are written as a

sentence inside `body`, in one of several different wordings depending on the transaction type.



Example raw record:



```

address: M-Money

body: You have received 2000 RWF from Jane Smith (\*\*\*\*\*\*\*\*\*013) on your mobile money

&#x20;     account at 2024-05-10 16:30:51. ... Financial Transaction Id: 76662021700.

readable\_date: 10 May 2024 4:30:58 PM

```



There is no `amount` field, no `sender` field, no `id` field. Everything has to be pulled out

of `body` and `readable\_date`.



\## What's been built



\### `dsa/inspect.py`

First step: printed a sample of raw records to see the actual attribute names and a spread of

different `body` message wordings. Used to figure out how many distinct SMS formats exist

before writing any parsing logic.



\### `dsa/parser.py`

Parses `modified\_sms\_v2.xml` into a flat list of transaction dictionaries. Because the data

has 1691 records across many wording variants, this went through several rounds: run the

parser, check how many records fell into an `"other"` bucket (unrecognized format), read a

sample of those, add a regex pattern for that wording, repeat.



Ended with 13 recognized patterns covering all 1691 records (0 left unclassified):



| Type | Count | What it is |

|---|---|---|

| payment | 698 | Payment to a person or merchant |

| transfer | 591 | Money sent to another account |

| bank\_deposit | 249 | Deposit into the mobile money account |

| received | 63 | Money received from someone |

| merchant\_payment | 36 | Payment to a registered business |

| bundle\_purchase | 21 | Airtime/data bundle purchase |

| airtime | 15 | Airtime top-up |

| non\_transaction | 8 | One-time password messages, not a transaction |

| failed | 5 | Failed transaction attempt |

| withdrawal | 3 | Cash withdrawal via agent |

| reversal | 2 | Reversed transaction |



Each output record has a consistent shape regardless of which pattern matched it:



```json

{

&#x20; "id": 1,

&#x20; "type": "received",

&#x20; "amount": 2000.0,

&#x20; "sender": "Jane Smith",

&#x20; "receiver": null,

&#x20; "transaction\_id": "76662021700",

&#x20; "fee": null,

&#x20; "balance": null,

&#x20; "timestamp": "10 May 2024 4:30:58 PM",

&#x20; "raw\_body": "You have received 2000 RWF from Jane Smith ..."

}

```



Fields that don't apply to a given transaction type are `null` rather than missing, so every

record has the same keys.



Run it:

```

py dsa\\parser.py

```

Output: `dsa/parsed\_transactions.json` (1691 records) plus a type breakdown printed to the

terminal.



\### `dsa/search\_compare.py`

Compares linear search against dictionary lookup for finding a record by `id`, timed across

6 positions in the list (id 1 through id 1690) with 2000 repeats each.



Result: dictionary lookup stayed flat at roughly 0.3 ms regardless of position. Linear search

grew from 0.4 ms (id near the start) to 161 ms (id near the end) — about 500x slower at the

far end of the list. This is the expected O(1) vs O(n) behavior and is what goes in the DSA

reflection section of the report.



Run it:

```

py dsa\\search\_compare.py

```



\## Where things stand



Parsing and the DSA comparison are complete and pushed. The output file that the API needs is:



```

dsa/parsed\_transactions.json

```



\## Handoff to Person 2 (API implementation)



Start here. The transaction list is ready — load `dsa/parsed\_transactions.json` directly, no

sample data needed anymore. Build `api/server.py` on top of it:



\- `GET /transactions` — return the full list

\- `GET /transactions/{id}` — look up by `id` (use a dict built from the list, like

&#x20; `search\_compare.py` does, not a loop)

\- `POST /transactions` — accept a new record in the same shape as above, assign the next

&#x20; available `id`

\- `PUT /transactions/{id}` — update an existing record

\- `DELETE /transactions/{id}` — remove a record



`type` will be one of the 11 values in the table above — validate against that list if you

want stricter input checking on POST/PUT, though it's not required by the assignment.



Once the endpoints work, `api/auth.py` (Person 3) plugs in as the Basic Auth check called at

the top of each handler.



\## Setup



Requires Python 3. No external packages — everything here uses the standard library

(`xml.etree.ElementTree`, `json`, `time`, `http.server`).



```

git clone https://github.com/Runweztt/restapi\_proj.git

cd restapi\_proj

py dsa\\parser.py

py dsa\\search\_compare.py

```

