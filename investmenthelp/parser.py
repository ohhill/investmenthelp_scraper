"""Parse a browser-rendered /advisor/detail/<id> page with selectolax."""

from selectolax.parser import HTMLParser

from investmenthelp.api import VALID_MARKER, clean


def parse_detail_html(html):
    """Return a record with FIELDS keys, or None if the page has no Contact Details."""
    tree = HTMLParser(html)
    contact = next(
        (n for n in tree.css("div.contact-advisor") if clean(n.css_first("h5").text()) == VALID_MARKER),
        None,
    )
    name_link = tree.css_first("h3.advisor-name a")
    if contact is None or name_link is None:
        return None

    url = name_link.attributes.get("href", "")
    full_name = clean(name_link.text(deep=False))
    first_name, _, last_name = full_name.partition(" ")

    firm = tree.css_first("p.advisor-firm-location")
    org_node = firm.css_first("span:not(.big-screen)") if firm else None
    loc_node = firm.css_first("span.big-screen") if firm else None
    organization = clean(org_node.text()) if org_node else ""
    location = clean(loc_node.text()) if loc_node else ""
    city, _, state = location.rpartition(", ")

    email = phone = website = ""
    lines, current = [], []
    p = contact.css_first("p")
    for node in p.iter(include_text=True):
        if node.tag == "br":
            lines.append(clean(" ".join(current)))
            current = []
        elif node.tag == "-text":
            current.append(node.text())
        elif node.tag == "a":
            href = node.attributes.get("href") or ""
            if href.startswith("mailto:"):
                email = clean(node.text())
            elif href.startswith("tel:"):
                phone = clean(node.text())
            elif not node.attributes.get("target"):
                website = clean(node.text())
    lines = [line for line in lines if line]

    # Text lines are: [org_name], address_1..3, "City, ST ZIP"
    if organization and lines and lines[0] == organization:
        lines = lines[1:]
    city_line = lines.pop() if lines else ""
    postal_code = city_line.removeprefix(location).strip(", ")

    cst_no = url.rstrip("/").rpartition("/")[2]
    return {
        "cst_no": int(cst_no) if cst_no.isdigit() else None,
        "first_name": first_name,
        "last_name": last_name,
        "prefix": "",
        "title": "",
        "organization": organization,
        "email": email.lower(),
        "phone": phone,
        "website": website,
        "address": ", ".join(lines),
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": "",
        "location": location,
        "url": url,
    }
