from pathlib import Path

from investmenthelp.parser import parse_detail_html

FIXTURE = (Path(__file__).parent / "fixtures" / "advisor_detail.html").read_text(encoding="utf-8")

ORG_FIRM_LOCATION = '<p class="advisor-firm-location"><span>Acme Wealth</span> , <span class="big-screen">'


def test_parses_basic_fields():
    assert parse_detail_html(FIXTURE) == {
        "cst_no": 12345,
        "first_name": "John",
        "last_name": "Sample",
        "prefix": "",
        "title": "",
        "organization": "",
        "email": "john.sample@example.com",
        "phone": "555-010-0000",
        "website": "",
        "address": "100 Main Street, Suite 200",
        "city": "Springfield",
        "state": "IL",
        "postal_code": "62701",
        "country": "",
        "location": "Springfield, IL",
        "url": "https://investmenthelp.org/advisor/detail/12345",
    }


def test_organization_is_not_part_of_address():
    # The page renders org_name in the title bar and as the first line of Contact Details
    html = FIXTURE.replace('<p class="advisor-firm-location"><!----><span class="big-screen">', ORG_FIRM_LOCATION)
    html = html.replace("<p>  <!---->", "<p> Acme Wealth <br>  <!---->")
    record = parse_detail_html(html)
    assert record["organization"] == "Acme Wealth"
    assert record["address"] == "100 Main Street, Suite 200"


def test_page_without_contact_details():
    shell = '<!doctype html><html><body><noscript>InvestmentHelp.org</noscript><div id="app"></div></body></html>'
    assert parse_detail_html(shell) is None
