"""UTM link generator — creates tagged URLs for campaign tracking."""

from urllib.parse import urlencode, urlparse, parse_qs, urlunparse, quote


def generate_utm(
    url: str,
    source: str,
    medium: str,
    campaign: str | None = None,
    term: str | None = None,
    content: str | None = None,
) -> str:
    """Generate a UTM-tagged URL.

    Args:
        url: Base URL to tag.
        source: Traffic source (e.g. "telegram", "vk", "yandex").
        medium: Marketing medium (e.g. "social", "cpc", "email").
        campaign: Campaign name (optional).
        term: Paid keyword (optional).
        content: Ad variation identifier (optional).

    Returns:
        Formatted string with UTM link and parameter breakdown.
    """
    parsed = urlparse(url)
    existing_params = parse_qs(parsed.query, keep_blank_values=True)

    utm_params: dict[str, str] = {
        "utm_source": source,
        "utm_medium": medium,
    }
    if campaign:
        utm_params["utm_campaign"] = campaign
    if term:
        utm_params["utm_term"] = term
    if content:
        utm_params["utm_content"] = content

    # Merge existing query params with UTM params
    merged: dict[str, str] = {}
    for k, v_list in existing_params.items():
        merged[k] = v_list[0] if v_list else ""
    merged.update(utm_params)

    new_query = urlencode(merged, quote_via=quote)
    tagged_url = urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment,
    ))

    # Build readable breakdown
    lines = [f"**UTM-ссылка:**\n`{tagged_url}`\n"]
    lines.append("**Параметры:**")
    for key, val in utm_params.items():
        lines.append(f"- {key} = {val}")

    return "\n".join(lines)
