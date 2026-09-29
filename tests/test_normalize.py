from investmenthelp.api import FIELDS, normalize

RAW = {
    "cst_no": 12345,
    "first_name": " John ",
    "last_name": "Sample",
    "prefix": "Mr.",
    "title": "Senior  Vice President",
    "org_name": "",
    "email": "John.Sample@Example.com",
    "phone": "555-010-0000",
    "website": None,
    "address_1": "Acme Wealth",
    "address_2": "100 Main Street",
    "address_3": "",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "UNITED STATES",
}


def test_normalize():
    record = normalize(RAW)
    assert list(record) == FIELDS
    assert record["first_name"] == "John"
    assert record["title"] == "Senior Vice President"
    assert record["email"] == "john.sample@example.com"
    assert record["website"] == ""
    assert record["address"] == "Acme Wealth, 100 Main Street"
    assert record["location"] == "Springfield, IL"
    assert record["url"] == "https://investmenthelp.org/advisor/detail/12345"


def test_location_without_state():
    record = normalize({**RAW, "state": ""})
    assert record["location"] == "Springfield"
